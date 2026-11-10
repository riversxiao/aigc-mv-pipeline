"""Series reuse must preserve character identity, stage sides and reviewed voices."""
import json
import shutil
import zipfile
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np
import pytest
import soundfile as sf
from PIL import Image
from typer.testing import CliRunner

from aigc_mv import h3
from aigc_mv.cli import app
from aigc_mv.shared_assets import (AssetLibrary, approve_voices, file_hash,
    pack_library, production_readiness, register_asset, scaffold_shared_assets,
    unpack_library, voice_readiness)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


@pytest.fixture
def series(tmp_path):
    library=tmp_path/'library/catalog.json'
    write_json(library,{'schema_version':1,'series_id':'test','version':'v1','assets':{},'characters':{},
        'defaults':{'scene_reference':'asset:scene.stage.v1','look_description':'Refined cinematic CG in indigo light.'}})
    ep=tmp_path/'episode';(ep/'audio').mkdir(parents=True)
    episode={'title':'test','venue':{'cn':'stage'},'cast':{
        'a':{'character':'wang_ye','name_cn':'王也','name_en':'Wang Ye','side':'left'},
        'b':{'character':'zhuge_qing','name_cn':'诸葛青','name_en':'Zhuge Qing','side':'right'}},
        'verses':[{'who':'a','lines':[{'text':'甲测试'}]},{'who':'b','lines':[{'text':'乙测试'}]}]}
    # JSON is also valid YAML; no test-specific YAML serializer is needed.
    write_json(ep/'episode.yaml',episode)
    sr=8000;t=np.arange(2*sr)/sr;tracks=[]
    for i,character in enumerate(['wang_ye','zhuge_qing']):
        image=tmp_path/f'{character}.png';Image.new('RGB',(24,16),(70+i*30,80,90)).save(image)
        register_asset(library,f'character.{character}.front.v1',image,'portrait',[character],
                       view='front',description=f'{character} front portrait')
        voice=tmp_path/f'{character}.wav';sf.write(voice,.2*np.sin(2*np.pi*(220+i*110)*t),sr)
        register_asset(library,f'voice.{character}.v1',voice,'voice',[character])
        track=.12*np.sin(2*np.pi*(330+i*110)*t);track[(t<1) if i else (t>=1)]=0
        sf.write(ep/f'audio/{character}_vocals.wav',track,sr);tracks.append(track)
    sf.write(ep/'audio/song.wav',sum(tracks),sr);sf.write(ep/'audio/vocals.wav',sum(tracks)*.3,sr)
    sf.write(ep/'audio/instrumental.wav',np.zeros(len(t)),sr)
    stage=tmp_path/'stage.png';Image.new('RGB',(24,16),(0,0,10)).save(stage)
    register_asset(library,'scene.stage.v1',stage,'scene',[])
    pair=tmp_path/'pair.png';Image.new('RGB',(24,16),(10,10,0)).save(pair)
    register_asset(library,'frame.pair.v1',pair,'composition',['wang_ye','zhuge_qing'],
                   positions={'wang_ye':'left','zhuge_qing':'right'})
    write_json(ep/'board/board.json',{'title':'test','grammar':'show','look':'test','duration':2,'units':[],
        'shots':[{'id':'s001','t0':0,'t1':.8,'section':'verse','kind':'perform','who':['a'],
                  'singer':'a','sung':True,'lines':[0],'unit':'u01','framing':'MCU','lens':'85'},
                 {'id':'s002','t0':1,'t1':1.8,'section':'verse','kind':'perform','who':['b'],
                  'singer':'b','sung':True,'lines':[1],'unit':'u02','framing':'MCU','lens':'85'}]})
    write_json(ep/'analysis/timing.json',{'duration':2,'grid':{'bpm':120,'beats':[0,.5,1,1.5],
        'downbeats':[0],'duration':2},'sections':[],
        'lines':[{'idx':i,'verse':i,'line':0,'who':key,'text':text,'t0':i,'t1':i+.8,'bar':0,'phrases':[]}
                 for i,(key,text) in enumerate([('a','甲测试'),('b','乙测试')])]})
    assets=ep/'h3_assets.json';cfg=scaffold_shared_assets(ep,library,assets)
    # These regression fixtures intentionally exercise the existing schema-3 path.
    cfg['schema_version']=3;cfg.pop('directing_plan');cfg.pop('motion_library')
    cfg['keyframes']={'s001':'asset:character.wang_ye.front.v1','s002':'asset:character.zhuge_qing.front.v1'}
    for character,v in cfg['audio_cast']['voices'].items():
        v.update(voice_id=character+'_v1',reference=f'asset:voice.{character}.v1')
    write_json(assets,cfg)
    return NS(ep=ep,library=library,assets=assets,cfg=cfg,root=tmp_path)


def test_library_versions_are_immutable_and_move_with_the_folder(series):
    moved=series.root/'moved';shutil.copytree(series.library.parent,moved)
    library=AssetLibrary(moved/'catalog.json');ref='asset:character.wang_ye.front.v1'
    assert library.resolve(ref).read_bytes()==(series.root/'wang_ye.png').read_bytes()
    replacement=series.root/'replacement.png';Image.new('RGB',(24,16),(200,0,0)).save(replacement)
    with pytest.raises(ValueError,match='new version'):
        register_asset(series.library,'character.wang_ye.front.v1',replacement,'portrait',['wang_ye'],view='front')
    asset=library.resolve(ref);asset.chmod(0o644);asset.write_bytes(b'changed')
    with pytest.raises(ValueError,match='Shared asset changed'):
        library.resolve(ref)


def test_scaffold_uses_character_ids_even_when_stage_aliases_change(series):
    episode=json.loads((series.ep/'episode.yaml').read_text())
    episode['cast']['a']['character']='zhuge_qing';episode['cast']['b']['character']='wang_ye'
    write_json(series.ep/'episode.yaml',episode)
    draft=scaffold_shared_assets(series.ep,series.library,series.ep/'next_assets.json')
    assert draft['cast']['a']['portrait']=='asset:character.zhuge_qing.front.v1'
    assert draft['cast']['b']['portrait']=='asset:character.wang_ye.front.v1'
    assert draft['keyframes']=={} and draft['audio_cast']['review']['status']=='pending'
    assert draft['schema_version']==4 and draft['directing_plan']=='direction.json' and draft['motion_library'] is None
    with pytest.raises(FileExistsError):
        scaffold_shared_assets(series.ep,series.library,series.ep/'next_assets.json')


def test_asset_archive_restores_verified_objects_without_overwriting(series):
    archive=series.root/'assets.zip';report=pack_library(series.library,archive)
    target=series.root/'restored';catalog=unpack_library(archive,target)
    assert len(AssetLibrary(catalog).data['assets'])==report['assets']
    assert AssetLibrary(catalog).resolve('asset:character.wang_ye.front.v1').read_bytes()==(series.root/'wang_ye.png').read_bytes()
    with pytest.raises(FileExistsError):unpack_library(archive,target)


def test_asset_archive_rejects_object_corruption_without_publishing_folder(series):
    good=series.root/'good.zip';pack_library(series.library,good)
    bad=series.root/'bad.zip'
    with zipfile.ZipFile(good) as source,zipfile.ZipFile(bad,'w') as dest:
        for name in source.namelist():dest.writestr(name,source.read(name) if name=='catalog.json' else b'corrupt')
    target=series.root/'should_not_restore'
    with pytest.raises(ValueError,match='changed'):unpack_library(bad,target)
    assert not target.exists()


def test_unreviewed_voices_block_new_production_before_bundle_creation(series):
    report=production_readiness(series.ep,series.assets)
    assert not report['ready_for_h3_production'] and report['gpu_started'] is False
    assert any('listening review is pending' in e for e in report['errors'])
    target=series.root/'should_not_exist'
    with pytest.raises(ValueError,match='preflight failed'):
        h3.export_bundle(series.ep,series.assets,series.root/'missing_template.json',target,['s001'])
    assert not target.exists()


def test_copying_a_legacy_config_cannot_silently_skip_the_voice_review(series):
    cfg=json.loads(series.assets.read_text());cfg.pop('schema_version')
    write_json(series.assets,cfg);target=series.root/'legacy_should_not_export'
    with pytest.raises(ValueError,match='Legacy production audio'):
        h3.export_bundle(series.ep,series.assets,series.root/'missing_template.json',target,['s001'])
    assert not target.exists()


@pytest.mark.parametrize('change,expected',[
    ('voice_id','voice_id is also assigned'),('reference','voice reference is also assigned'),
    ('vocals','character vocal track is also assigned')])
def test_distinct_names_cannot_hide_duplicate_voice_assets(series,change,expected):
    a=series.cfg['audio_cast']['voices']['wang_ye'];b=series.cfg['audio_cast']['voices']['zhuge_qing']
    if change=='reference':
        copied=series.ep/'copied_reference.wav'
        shutil.copy2(AssetLibrary(series.library).resolve(a['reference']),copied)
        b['reference']=copied.name
    else:b[change]=a[change]
    write_json(series.assets,series.cfg)
    report=voice_readiness(series.ep,series.assets,require_review=False)
    assert any(expected in e for e in report['errors'])


@pytest.mark.parametrize('change',['song','vocals','voice_id','script'])
def test_audio_review_expires_when_the_actual_audio_or_casting_changes(series,change):
    assert approve_voices(series.ep,series.assets,'Listened to both character voices and the final mix')['ready']
    if change in ('song','vocals'):
        path=series.ep/('audio/song.wav' if change=='song' else 'audio/wang_ye_vocals.wav')
        data,sr=sf.read(path);sf.write(path,data*.7,sr)
    elif change=='voice_id':
        cfg=json.loads(series.assets.read_text());cfg['audio_cast']['voices']['wang_ye']['voice_id']='new_voice'
        write_json(series.assets,cfg)
    else:
        episode=json.loads((series.ep/'episode.yaml').read_text());episode['verses'][0]['lines'][0]['text']='换了歌词'
        write_json(series.ep/'episode.yaml',episode)
    assert any('stale' in e for e in voice_readiness(series.ep,series.assets)['errors'])


def test_composed_first_frames_cannot_be_reused_after_sides_change(series):
    board=json.loads((series.ep/'board/board.json').read_text());board['shots'][0]['who']=['a','b']
    write_json(series.ep/'board/board.json',board)
    series.cfg['keyframes']['s001']='asset:frame.pair.v1'
    write_json(series.assets,series.cfg);approve_voices(series.ep,series.assets,'Heard distinct voices')
    assert production_readiness(series.ep,series.assets)['ready_for_h3_production']
    episode=json.loads((series.ep/'episode.yaml').read_text())
    episode['cast']['a']['side']='right';episode['cast']['b']['side']='left';write_json(series.ep/'episode.yaml',episode)
    assert any('stage side changed' in e for e in production_readiness(series.ep,series.assets)['errors'])


def test_back_reference_is_selected_per_shot_and_checked(series):
    back=series.root/'back.png';Image.new('RGB',(24,16),(3,4,5)).save(back)
    register_asset(series.library,'character.wang_ye.back.v1',back,'portrait',['wang_ye'],view='back',description='Rear view only; face unseen.')
    frame=series.root/'rear_frame.png';Image.new('RGB',(24,16),(6,7,8)).save(frame)
    register_asset(series.library,'frame.rear.v1',frame,'composition',['wang_ye'],positions={'wang_ye':'left'},view='back')
    series.cfg['keyframes']['s001']='asset:frame.rear.v1';write_json(series.assets,series.cfg)
    approve_voices(series.ep,series.assets,'Heard distinct voices')
    assert any('back reference' in e for e in production_readiness(series.ep,series.assets)['errors'])
    cfg=json.loads(series.assets.read_text());cfg['shot_overrides']['s001']={'portraits':{'a':'asset:character.wang_ye.back.v1'}}
    write_json(series.assets,cfg)
    assert production_readiness(series.ep,series.assets)['ready_for_h3_production']
    assert cfg['cast']['a']['portrait']=='asset:character.wang_ye.front.v1'


def test_missing_timing_cannot_be_reported_as_production_ready(series):
    approve_voices(series.ep,series.assets,'Heard distinct voices')
    (series.ep/'analysis/timing.json').unlink()
    assert any(e.startswith('timing:') for e in production_readiness(series.ep,series.assets)['errors'])


def test_cli_reports_pending_voice_review_without_starting_generation(series):
    result=CliRunner().invoke(app,['ep','production-check',str(series.ep),'--assets',str(series.assets)])
    assert result.exit_code==1 and '"gpu_started": false' in result.output
    assert 'listening review is pending' in result.output


def test_h3_routes_character_audio_and_fingerprints_the_executable_workflow(series,monkeypatch):
    approve_voices(series.ep,series.assets,'Compared same phrase and reviewed actual mix')
    monkeypatch.setattr(h3,'load_timing',lambda _:NS(lines=[NS(t0=0,t1=.8,text='甲测试'),NS(t0=1,t1=1.8,text='乙测试')]))
    ids=['1','2','3','4','5','6','7','8','20','21','22','23','24','25','26','27','30','31','32','34','35']
    template=series.root/'template.json';write_json(template,{k:{'class_type':'TestNode','inputs':{}} for k in ids})
    first=h3.export_bundle(series.ep,series.assets,template,series.root/'bundle1',['s001','s002'])
    assert first['voice_policy']=='reviewed_character_tracks'
    assert 'Wang Ye has half-lidded' in first['jobs'][0]['prompt']
    assert 'Wang Ye has half-lidded' not in first['jobs'][1]['prompt']
    expected=series.ep/'audio/wang_ye_vocals.wav'
    target=series.root/'expected.wav'
    h3.audio_window(expected,target,0,.8,8/24,90,[(0,.82)])
    actual=series.root/'bundle1/input'/first['jobs'][0]['audio']
    assert file_hash(actual)==file_hash(target), 'guide must come from the character track, not mixed vocals.wav'
    original=h3.graph_for
    def changed_graph(template,job):
        graph=original(template,job);graph['21']['inputs']['alpha']=.12;return graph
    monkeypatch.setattr(h3,'graph_for',changed_graph)
    second=h3.export_bundle(series.ep,series.assets,template,series.root/'bundle2',['s001'])
    assert first['jobs'][0]['job_id']!=second['jobs'][0]['job_id']


def test_extended_character_sheets_wardrobe_stage_v2_and_meoogo_namespaces(series):
    lib_root = series.library.parent
    cs_dir = lib_root / 'character_sheets'
    cs_dir.mkdir(parents=True)
    quad_img = cs_dir / 'QuadView_WangYe.jpg'
    Image.new('RGB', (64, 36), (40, 50, 60)).save(quad_img)
    young_img = cs_dir / 'QuadView_WangYe_Child.jpg'
    Image.new('RGB', (64, 36), (45, 55, 65)).save(young_img)
    ward_img = cs_dir / 'Wardrobe4x_XiaHe.jpg'
    Image.new('RGB', (64, 36), (70, 40, 60)).save(ward_img)
    write_json(cs_dir / 'character_sheets_catalog.json', {
        'sheets': [
            {
                'file': quad_img.name,
                'character_id': 'wang_ye',
                'sheet_id': 'quadview.wang_ye.v1',
                'character_zh': '王也',
                'faction': '武当',
                'sheet_type': 'quadview_3d_charsheet',
                'sha256': file_hash(quad_img),
            },
            {
                'file': young_img.name,
                'character_id': 'wang_ye_child',
                'sheet_id': 'quadview.wang_ye_child.v1',
                'character_zh': '童年王也',
                'faction': '武当',
                'sheet_type': 'quadview_3d_charsheet',
                'sha256': file_hash(young_img),
            },
            {
                'file': ward_img.name,
                'character_id': 'xia_he',
                'sheet_id': 'wardrobe4x.xia_he.v1',
                'character_zh': '夏禾',
                'faction': '全性',
                'sheet_type': 'female_wardrobe_4x',
                'sha256': file_hash(ward_img),
            },
        ]
    })

    st_dir = lib_root / 'stage_v2'
    st_dir.mkdir(parents=True)
    st_img = st_dir / 'stage_v2_master_panorama.jpg'
    Image.new('RGB', (64, 36), (10, 20, 40)).save(st_img)
    write_json(st_dir / 'catalog.json', {
        'schema_version': 1,
        'assets': {
            'stage_v2.master_panorama.v1': {
                'kind': 'scene',
                'path': st_img.name,
                'sha256': file_hash(st_img),
                'characters': [],
                'description': 'Stage v2 Neo-Taoist arena',
            }
        }
    })

    mg_dir = lib_root / 'meoogo_refs'
    mg_dir.mkdir(parents=True)
    pad_dir = lib_root / 'meoogo_padded_16x9'
    pad_dir.mkdir(parents=True)
    mg_img = mg_dir / 'C001_丁嶋安.png'
    Image.new('RGB', (32, 32), (80, 90, 100)).save(mg_img)
    pad_img = pad_dir / 'C001_丁嶋安_1344x768.jpg'
    Image.new('RGB', (64, 36), (80, 90, 100)).save(pad_img)
    write_json(mg_dir / 'meoogo_characters_catalog.json', {
        'characters': [
            {
                'meoogo_id': 'C001',
                'name_cn': '丁嶋安',
                'faction': '全性',
                'role_tag': '两豪杰',
                'local_2d_ref': f'libraries/luotian/meoogo_refs/{mg_img.name}',
                'padded_16x9_ref': f'libraries/luotian/meoogo_padded_16x9/{pad_img.name}',
            }
        ]
    })
    write_json(lib_root / 'master_asset_library_drive.json', {
        'files': [
            {'name': quad_img.name, 'file_id': 'drive_fid_123', 'file_url': 'https://drive.google.com/file/d/drive_fid_123'}
        ]
    })

    library = AssetLibrary(series.library)
    assert library.resolve('charsheet:wang_ye') == quad_img.resolve()
    assert library.resolve('charsheet:quadview.wang_ye_child.v1') == young_img.resolve()
    assert library.resolve('wardrobe:xia_he') == ward_img.resolve()
    assert library.resolve('stage_v2:master_panorama') == st_img.resolve()
    assert library.resolve('meoogo:丁嶋安') == mg_img.resolve()
    assert library.resolve('meoogo_16x9:丁嶋安') == pad_img.resolve()
    assert library.cloud_info('charsheet:wang_ye')['file_id'] == 'drive_fid_123'

    prof = library.character_profile('wang_ye', age_variant='child')
    assert prof['portrait'] == 'charsheet:quadview.wang_ye_child.v1'

    summary = library.summary()
    assert summary['quadview_3d_sheets'] == 2
    assert summary['female_wardrobe_4x_sheets'] == 1
    assert summary['stage_v2_assets'] == 1
    assert summary['meoogo_2d_characters'] == 1
    assert summary['meoogo_padded_16x9_inputs'] == 1
    assert summary['google_drive_synced_files'] == 1

    # Verify production_readiness accepts age-variant charsheet portrait override
    approve_voices(series.ep, series.assets, 'Reviewed voices')
    cfg = json.loads(series.assets.read_text())
    cfg['shot_overrides'] = {'s001': {'portraits': {'a': 'charsheet:quadview.wang_ye_child.v1'}}}
    write_json(series.assets, cfg)
    rep = production_readiness(series.ep, series.assets)
    assert rep['ready_for_h3_production'], rep['errors']
    assert 'charsheet:quadview.wang_ye_child.v1' in rep['shared_assets_used']
