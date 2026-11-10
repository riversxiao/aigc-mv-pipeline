"""Director contracts must constrain compiled prompts, references and acceptance."""
import copy
import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from typer.testing import CliRunner

from test_shared_assets import series, write_json  # Reuse actual images, stems and timing fixtures.
from aigc_mv import h3
from aigc_mv.cli import app
from aigc_mv.directing import (REFERENCE_ROLES, REVIEW_CRITERIA, direction_readiness,
                               scaffold_direction)
from aigc_mv.motion_assets import MotionLibrary, prepare_motion
from aigc_mv.shared_assets import approve_voices, file_hash, production_readiness
from aigc_mv.shot_review import record_review, retake_plan


def ready_plan(series, motion=False):
    path=series.ep/'direction.json'
    cfg=json.loads(series.assets.read_text())
    cfg.update(schema_version=4,directing_plan=path.name)
    write_json(series.assets,cfg)
    plan=scaffold_direction(series.ep,series.assets,path)
    plan['floor_plan']='Two rivals face across the jade stage; camera remains south of the axis.'
    for row in plan['shots'].values():
        row.update(status='ready',camera_side='south of the stage axis',light='soft neutral face key and cool hair rim',
                   emotion='quietly amused',primary_action='One small downward free-hand accent.',
                   ending='free hand returns to waist; shoulders settle')
        for block in row['blocking'].values():
            block.update(position='beside the jade rail',facing='toward the rival',eyeline='past the lens toward the rival')
        row['beats']={'prepare':'Breathe and hold the opening pose','accent':'One downward beat gesture','settle':'Lower the hand and listen'}
        row['microphone']={'hand':'right','position':'at lower sternum, lips fully visible'}
        row['motion']['required']=motion
    write_json(path,plan)
    approve_voices(series.ep,series.assets,'Actual mix and separate character samples heard')
    return path,plan,json.loads(series.assets.read_text())


def template(series):
    ids=['1','2','3','4','5','6','7','8','20','21','22','23','24','25','26','27','30','31','32','34','35']
    data={k:{'class_type':'TestNode','inputs':{}} for k in ids}
    data['20']['class_type']='MiniMaxH3ReferenceToVideo'
    path=series.root/'template.json';write_json(path,data)
    # Schema-4 production pins the validated workflow, as a real model_profile does.
    cfg=json.loads(series.assets.read_text())
    cfg.setdefault('model_profile',{})['template_sha256']=file_hash(path)
    write_json(series.assets,cfg)
    return path


def clip(path, fps=30, count=30, audio=False):
    av=pytest.importorskip('av')
    with av.open(str(path),'w') as container:
        stream=container.add_stream('libx264',rate=fps)
        stream.width=stream.height=64;stream.pix_fmt='yuv420p'
        if audio:
            sound=container.add_stream('aac',rate=8000)
            frame=av.AudioFrame.from_ndarray(np.zeros((1,1024),dtype=np.int16),format='s16',layout='mono');frame.sample_rate=8000
            for packet in sound.encode(frame):container.mux(packet)
            for packet in sound.encode():container.mux(packet)
        for i in range(count):
            frame=av.VideoFrame.from_ndarray(np.full((64,64,3),i*3,dtype=np.uint8),format='rgb24')
            for packet in stream.encode(frame):container.mux(packet)
        for packet in stream.encode():container.mux(packet)


def motion_index(series):
    root=series.root/'motions';root.mkdir();video=root/'pose.mp4';clip(video)
    index=root/'catalog.json'
    write_json(index,{'schema_version':1,'motions':{'gesture.v1':{'kind':'pose_video','status':'ready','people':1,
        'path':video.name,'sha256':file_hash(video),'microphone_hand':'right','framings':['MCU'],'views':['front']}}})
    return index,video


def test_schema4_requires_director_plan_and_fails_before_bundle_creation(series):
    cfg=json.loads(series.assets.read_text());cfg['schema_version']=4;write_json(series.assets,cfg)
    approve_voices(series.ep,series.assets,'Actual audio reviewed')
    report=production_readiness(series.ep,series.assets)
    assert not report['ready_for_h3_production'] and 'directing_plan' in report['direction']['errors'][0]
    target=series.root/'blocked'
    with pytest.raises(ValueError,match='preflight'):
        h3.export_bundle(series.ep,series.assets,series.root/'absent.json',target,['s001'])
    assert not target.exists()


def test_draft_and_incomplete_spatial_fields_are_not_ready(series):
    path,plan,cfg=ready_plan(series)
    plan['shots']['s001']['blocking']['wang_ye']['eyeline']=''
    plan['shots']['s001']['status']='draft';write_json(path,plan)
    errors=direction_readiness(series.ep,series.assets,cfg)['errors']
    assert any('eyeline' in s for s in errors) and any('draft' in s for s in errors)


def test_other_visible_people_need_idle_business_and_stable_ids(series):
    board=json.loads((series.ep/'board/board.json').read_text());board['shots'][0]['background']=['b']
    write_json(series.ep/'board/board.json',board)
    path,plan,cfg=ready_plan(series)
    assert any('idle action' in e for e in direction_readiness(series.ep,series.assets,cfg)['errors'])
    plan['shots']['s001']['others']={'zhuge_qing':'A small attentive breath, eyes on the performer'}
    write_json(path,plan)
    assert direction_readiness(series.ep,series.assets,cfg)['ready']


def test_reference_roles_and_stale_script_are_rejected(series):
    path,plan,cfg=ready_plan(series)
    changed=copy.deepcopy(plan);changed['reference_roles']['motion']='identity'
    write_json(path,changed)
    assert not direction_readiness(series.ep,series.assets,cfg)['ready']
    write_json(path,plan)
    episode=json.loads((series.ep/'episode.yaml').read_text());episode['verses'][0]['lines'][0]['text']='changed'
    write_json(series.ep/'episode.yaml',episode)
    assert any('stale' in e for e in direction_readiness(series.ep,series.assets,cfg)['errors'])


def test_pending_motion_library_is_explicit_and_never_submits(series):
    path,plan,cfg=ready_plan(series,motion=True)
    report=direction_readiness(series.ep,series.assets,cfg)
    assert not report['ready'] and report['gpu_started'] is False
    assert any('pending' in e for e in report['errors'])


def test_plan_reaches_h3_prompt_and_changes_task_identity(series):
    path,plan,cfg=ready_plan(series)
    first=h3.export_bundle(series.ep,series.assets,template(series),series.root/'one',['s001'])
    job=first['jobs'][0]
    assert 'Primary action: One small downward' in job['prompt']
    assert 'south of the stage axis' in job['prompt'] and 'looks past the lens' in job['prompt']
    assert 'Natural small nods' not in job['prompt']
    assert job['review_contract']['criteria']==REVIEW_CRITERIA
    plan['shots']['s001']['ending']='left hand settles against the waist';write_json(path,plan)
    second=h3.export_bundle(series.ep,series.assets,template(series),series.root/'two',['s001'])
    assert second['jobs'][0]['job_id']!=job['job_id']


@pytest.mark.parametrize('mode', ['lavalier', 'headset'])
def test_wearable_mic_frees_hands_without_handheld_prompt(series, mode):
    path, plan, cfg = ready_plan(series)
    for row in plan['shots'].values():
        row['microphone'] = {'mode': mode, 'hand': 'none', 'position': 'at the collar, lips unobstructed'}
    write_json(path, plan)
    assert direction_readiness(series.ep, series.assets, cfg)['ready']
    job = h3.export_bundle(series.ep, series.assets, template(series), series.root/'wearable', ['s001'])['jobs'][0]
    assert f'discreet {mode} microphone' in job['prompt']
    assert 'both hands remain free' in job['prompt']
    assert 'Keep the microphone at lower sternum' not in job['prompt']


def test_short_shot_uses_only_its_script_excerpt_and_preserves_background_occupancy(series):
    path, plan, cfg = ready_plan(series)
    board = json.loads((series.ep/'board/board.json').read_text())
    timing = json.loads((series.ep/'analysis/timing.json').read_text())
    text = timing['lines'][board['shots'][0]['lines'][0]]['text']
    excerpt = text[:max(1, len(text)//2)]
    cfg['shot_overrides'] = {'s001': {'lyric_excerpt': excerpt}}
    write_json(series.assets, cfg)
    job = h3.export_bundle(series.ep, series.assets, template(series), series.root/'excerpt', ['s001'])['jobs'][0]
    assert f'<d>[Mandarin]{excerpt}</d>' in job['prompt']
    assert 'Preserve the exact background population' in job['prompt']
    assert 'The distant gallery contains seated sect disciples' not in job['prompt']
    cfg['shot_overrides']['s001']['lyric_excerpt'] = '完全不在歌词中的新句子'
    write_json(series.assets, cfg)
    with pytest.raises(ValueError, match='contiguous part'):
        h3.export_bundle(series.ep, series.assets, template(series), series.root/'invented', ['s001'])


def test_sung_shot_still_requires_explicit_microphone_assignment(series):
    path, plan, cfg = ready_plan(series)
    plan['shots']['s001']['microphone'] = {'hand': 'none', 'position': 'at collar'}
    write_json(path, plan)
    assert any('microphone hand' in e for e in direction_readiness(series.ep, series.assets, cfg)['errors'])
    plan['shots']['s001']['microphone'].update(mode='lavalier', hand='right')
    write_json(path, plan)
    assert any('both hands free' in e for e in direction_readiness(series.ep, series.assets, cfg)['errors'])


def test_pilot_honors_authored_medium_shot_for_body_reference(series):
    path, plan, cfg = ready_plan(series)
    cfg.update(mode='pilot', shot_overrides={'s001': {'framing': 'MS'}})
    write_json(series.assets, cfg)
    for row in plan['shots'].values():
        row.update(framing='MCU', camera='locked')
    plan['shots']['s001']['framing'] = 'MS'
    write_json(path, plan)
    assert direction_readiness(series.ep, series.assets, cfg, ['s001'])['ready']
    job = h3.export_bundle(series.ep, series.assets, template(series), series.root/'medium', ['s001'])['jobs'][0]
    assert job['framing'] == 'MS'


def test_external_motion_is_checked_for_hand_view_bytes_and_portable_identity(series):
    path,plan,cfg=ready_plan(series,motion=True);index,video=motion_index(series)
    cfg['motion_library']=str(index);write_json(series.assets,cfg)
    for row in plan['shots'].values():row['motion']['asset_id']='gesture.v1'
    write_json(path,plan)
    first=direction_readiness(series.ep,series.assets,cfg);assert first['ready']
    moved=series.root/'moved';shutil.copytree(index.parent,moved)
    cfg['motion_library']=str(moved/'catalog.json')
    assert direction_readiness(series.ep,series.assets,cfg)['shots']['s001']['fingerprint']==first['shots']['s001']['fingerprint']
    plan['shots']['s001']['microphone']['hand']='left';write_json(path,plan)
    assert any('microphone hand' in e for e in direction_readiness(series.ep,series.assets,cfg)['errors'])
    with pytest.raises(ValueError,match='framing or view'):
        MotionLibrary(index).resolve('gesture.v1',hand='right',framing='MCU',view='back')
    video.write_bytes(b'changed')
    with pytest.raises(ValueError,match='bytes changed'):
        MotionLibrary(index).resolve('gesture.v1',hand='right',framing='MCU',view='front')


def test_native_fps_motion_is_fitted_and_audio_is_never_retimed(series):
    av=pytest.importorskip('av');index,video=motion_index(series)
    output=series.root/'prepared.mp4'
    report=prepare_motion(video,output,expected_sha256=file_hash(video),frames=90,lead_frames=8,active_frames=24)
    assert report['target_audio_retimed'] is False and report['source_audio_used'] is False
    assert report['tail_hold_frames']==58
    with av.open(str(output)) as container:
        stream=container.streams.video[0]
        assert stream.average_rate==24 and not container.streams.audio
        frames=[f.to_ndarray(format='rgb24') for f in container.decode(stream)]
    assert len(frames)==90 and np.array_equal(frames[0],frames[7])
    assert float(frames[8].mean()) < float(frames[31].mean())
    source_audio=series.root/'audio_ref.mp4';clip(source_audio,audio=True)
    with pytest.raises(ValueError,match='no audio'):
        prepare_motion(source_audio,series.root/'bad.mp4',expected_sha256=file_hash(source_audio),frames=90,lead_frames=8,active_frames=24)


def test_production_graph_routes_skeleton_images_without_source_audio(series):
    path,plan,cfg=ready_plan(series,motion=True);index,video=motion_index(series)
    cfg['motion_library']=str(index);write_json(series.assets,cfg)
    for row in plan['shots'].values():row['motion']['asset_id']='gesture.v1'
    write_json(path,plan)
    result=h3.export_bundle(series.ep,series.assets,template(series),series.root/'bundle',['s001'])
    job=result['jobs'][0];graph=json.loads((series.root/'bundle'/job['workflow']).read_text())
    assert graph['20']['inputs']['ref_videos.ref_video_0']==['301',0]
    assert not any(k.startswith('ref_video_audios.') for k in graph['20']['inputs'])
    assert job['motion_metadata']['asset_id']=='gesture.v1'
    assert '<Video 1>' in job['prompt'] and '<Subject 1> only' in job['prompt']


def test_cli_attaches_a_draft_and_reports_pending_without_gpu(series):
    path=series.ep/'new_direction.json'
    result=CliRunner().invoke(app,['ep','direct-plan',str(series.ep),'--assets',str(series.assets),'--out',str(path)])
    assert result.exit_code==0 and path.exists()
    assert json.loads(series.assets.read_text())['directing_plan']==path.name
    checked=CliRunner().invoke(app,['ep','direction-check',str(series.ep),'--assets',str(series.assets)])
    assert checked.exit_code==1 and '"gpu_started": false' in checked.output


def test_ingest_keeps_checks_pending_and_locks_the_actual_input_hashes(series):
    ready_plan(series)
    bundle=series.root/'ingest_bundle'
    manifest=h3.export_bundle(series.ep,series.assets,template(series),bundle,['s001'])
    job=manifest['jobs'][0];results=series.root/'results';results.mkdir()
    video=results/(job['job_id']+'_raw.mp4');video.write_bytes(b'unit-test render result')
    write_json(results/'state.json',{'jobs':{job['job_id']:{'status':'complete','files':[
        {'file':video.name,'sha256':file_hash(video)}]}}})
    take=h3.ingest_shot_results(series.ep,bundle,results)['s001'][0]
    assert set(take['criteria_status'].values())=={'unreviewed'}
    assert take['generation_contract']['input_sha256'][job['audio']]==manifest['files']['input/'+job['audio']]
    assert take['generation_contract']['workflow_sha256']==manifest['files'][job['workflow']]
    assert h3.approved_shot_takes(series.ep)=={}


def test_library_preflight_rejects_a_source_audio_track_and_excessive_speed(series):
    index,video=motion_index(series)
    source=series.root/'audio_pose.mp4';clip(source,audio=True)
    data=json.loads(index.read_text());data['motions']['gesture.v1'].update(path='../audio_pose.mp4',sha256=file_hash(source))
    write_json(index,data)
    with pytest.raises(ValueError,match='escapes'):
        MotionLibrary(index).resolve('gesture.v1',hand='right',framing='MCU',view='front')
    shutil.copy2(source,index.parent/'audio_pose.mp4');data['motions']['gesture.v1']['path']='audio_pose.mp4';write_json(index,data)
    with pytest.raises(ValueError,match='no audio'):
        MotionLibrary(index).resolve('gesture.v1',hand='right',framing='MCU',view='front')
    with pytest.raises(ValueError,match='2x speed'):
        prepare_motion(video,series.root/'too_slow.mp4',expected_sha256=file_hash(video),frames=90,lead_frames=8,active_frames=80)
    assert not (series.root/'too_slow.mp4').exists()


def take_fixture(series):
    video=series.ep/'h3/take.mp4';video.parent.mkdir();video.write_bytes(b'reviewed immutable video')
    take={'job_id':'job1','file':'h3/take.mp4','sha256':file_hash(video),'mode':'production',
        'pilot_override':{},'visual_status':'pass','identity_status':'pass',
        'review_contract':{'version':1,'criteria':REVIEW_CRITERIA},
        'generation_contract':{'seed':40,'steps':12,'audio':'unchanged.wav','camera':'locked'}}
    write_json(series.ep/'h3/shot_takes.json',{'s001':[take]})
    return take


def test_new_take_needs_all_evidence_and_cannot_use_only_legacy_pass_flags(series):
    take=take_fixture(series)
    assert h3.approved_shot_takes(series.ep)=={}
    review={'job_id':take['job_id'],'video_sha256':take['sha256'],'verdict':'keep',
        'checks':{k:{'status':'pass','evidence':'Inspected the actual clip at 0.5s and 2.0s'} for k in REVIEW_CRITERIA}}
    path=series.root/'review.json';write_json(path,review)
    record_review(series.ep,'s001','job1',path)
    assert h3.approved_shot_takes(series.ep)['s001']['job_id']=='job1'
    review['checks']['hands_props']['status']='fail';write_json(path,review)
    with pytest.raises(ValueError,match='every required'):
        record_review(series.ep,'s001','job1',path)
    review['video_sha256']='stale';write_json(path,review)
    with pytest.raises(ValueError,match='exact job'):
        record_review(series.ep,'s001','job1',path)


def test_retake_is_one_change_and_preserves_original_generation_contract(series):
    take=take_fixture(series)
    review={'job_id':'job1','video_sha256':take['sha256'],'verdict':'retake',
        'checks':{k:{'status':'fail' if k=='hands_props' else 'pass','evidence':'At 1.2s microphone covers lips' if k=='hands_props' else 'Actual footage checked'} for k in REVIEW_CRITERIA}}
    path=series.root/'review.json';write_json(path,review);record_review(series.ep,'s001','job1',path)
    proposal=series.root/'proposal.json'
    change={'field':'direction.shots.s001.microphone.position','value':'lower sternum'}
    write_json(proposal,{'hypothesis':'A lower microphone may preserve the visible lips','changes':[change]})
    report=retake_plan(series.ep,'s001','job1',proposal,series.root/'retake.json')
    assert report['submitted'] is False and report['gpu_started'] is False
    assert report['preserve']==take['generation_contract']
    write_json(proposal,{'hypothesis':'too many changes','changes':[change,change]})
    with pytest.raises(ValueError,match='exactly one'):
        retake_plan(series.ep,'s001','job1',proposal,series.root/'bad_retake.json')


@pytest.mark.parametrize('evidence',[None, '', ['unstructured']])
def test_empty_or_unstructured_evidence_cannot_approve_a_take(series, evidence):
    take=take_fixture(series)
    review={'job_id':'job1','video_sha256':take['sha256'],'verdict':'keep',
        'checks':{k:{'status':'pass','evidence':evidence} for k in REVIEW_CRITERIA}}
    path=series.root/'invalid_review.json';write_json(path,review)
    with pytest.raises(ValueError,match='observed evidence'):
        record_review(series.ep,'s001','job1',path)
    assert h3.approved_shot_takes(series.ep)=={}


def test_federated_motion_categories_duel_whitemodels_and_free_hand_instruments(series):
    motions_root = series.root / 'federated_motions'
    for cat in ('battle_rap', 'instruments', 'kpop_dance', 'luotian_combat'):
        (motions_root / cat).mkdir(parents=True)

    rap_vid = motions_root / 'battle_rap/rap.mp4'
    inst_vid = motions_root / 'instruments/piano.mp4'
    dance_vid = motions_root / 'kpop_dance/choreo.mp4'
    duel_vid = motions_root / 'luotian_combat/duel.mp4'
    for v in (rap_vid, inst_vid, dance_vid, duel_vid):
        clip(v, fps=24, count=48)

    write_json(motions_root / 'battle_rap/catalog.json', {
        'schema_version': 1,
        'category': 'battle_rap',
        'motions': {
            'battle_rap.accent.v1': {
                'kind': 'pose_video', 'status': 'ready', 'people': 1,
                'path': rap_vid.name, 'sha256': file_hash(rap_vid),
                'microphone_hand': 'right', 'framings': ['MCU', 'MS'], 'views': ['front'],
                'pose_format': '2d_wholebody_skeleton_rtmw', 'tags': ['rap'],
            }
        }
    })
    write_json(motions_root / 'instruments/catalog.json', {
        'schema_version': 1,
        'category': 'instruments',
        'motions': {
            'instruments.piano.v1': {
                'kind': 'pose_video', 'status': 'ready', 'people': 1,
                'path': inst_vid.name, 'sha256': file_hash(inst_vid),
                'microphone_hand': 'none', 'framings': ['MCU', 'MS'], 'views': ['front'],
                'pose_format': 'rigged_3d_white_mannequin', 'tags': ['piano'],
            }
        }
    })
    write_json(motions_root / 'kpop_dance/catalog.json', {
        'schema_version': 1,
        'category': 'kpop_dance',
        'motions': {
            'kpop_dance.solo.v1': {
                'kind': 'pose_video', 'status': 'ready', 'people': 1,
                'path': dance_vid.name, 'sha256': file_hash(dance_vid),
                'microphone_hand': 'either', 'framings': ['FS', 'MS', 'MCU'], 'views': ['front'],
                'pose_format': 'rigged_3d_white_mannequin', 'tags': ['kpop'],
            }
        }
    })
    write_json(motions_root / 'luotian_combat/catalog.json', {
        'schema_version': 1,
        'category': 'luotian_combat',
        'motions': {
            'luotian_combat.thunder.duel_white.v1': {
                'kind': 'pose_video', 'status': 'ready', 'people': 2,
                'path': duel_vid.name, 'sha256': file_hash(duel_vid),
                'microphone_hand': 'none', 'framings': ['2S', 'MS', 'MCU'], 'views': ['front'],
                'pose_format': '3d_whitemodel_duel_mannequin', 'tags': ['martial_arts', 'duel_2p'],
                'characters': ['张楚岚', '张灵玉'],
            }
        }
    })

    # Loading either the root directory or one sibling catalog discovers all categories
    fed = MotionLibrary(motions_root / 'battle_rap/catalog.json')
    assert set(fed.categories()) == {'battle_rap', 'instruments', 'kpop_dance', 'luotian_combat'}
    assert fed.summary()['ready_motions'] == 4
    assert len(fed.search(category='kpop_dance', tag='kpop')) == 1
    assert len(fed.search(people=2, character='张灵玉')) == 1

    # Resolve 2-person duel white model with people=2 and allow_free_hands=True
    duel_res = fed.resolve('luotian_combat.thunder.duel_white.v1', hand='right', framing='MCU', view='front', people=2, allow_free_hands=True)
    assert Path(duel_res['source']) == duel_vid.resolve()

    # Verify direction_readiness supports cross-category instrument & 2p duel motions
    path, plan, cfg = ready_plan(series, motion=True)
    cfg['motion_library'] = str(motions_root / 'battle_rap/catalog.json')
    write_json(series.assets, cfg)
    plan['shots']['s001']['motion'].update(asset_id='instruments.piano.v1', allow_free_hands=True)
    plan['shots']['s002']['motion'].update(asset_id='luotian_combat.thunder.duel_white.v1', people=2, allow_free_hands=True)
    write_json(path, plan)
    rep = direction_readiness(series.ep, series.assets, cfg)
    assert rep['ready'], rep['errors']

    res_cli = CliRunner().invoke(app, ['ep', 'motion-search', '--library', str(motions_root), '--people', '2'])
    assert res_cli.exit_code == 0 and 'luotian_combat.thunder.duel_white.v1' in res_cli.output
