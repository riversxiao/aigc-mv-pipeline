"""Motion pilot isolation, media clocks and cache identities, without models."""
import json
from pathlib import Path

import numpy as np
import pytest

av = pytest.importorskip('av')

from aigc_mv.h3 import graph_for
from aigc_mv.h3_motion import compile_comparison, inspect_reference, reference_graph
from aigc_mv.shared_assets import file_hash


def clip(path, *, fps=24, count=124, color=25, audio=False):
    with av.open(str(path), 'w') as container:
        stream = container.add_stream('libx264', rate=fps)
        stream.width = stream.height = 64
        stream.pix_fmt = 'yuv420p'
        if audio:
            soundtrack = container.add_stream('aac', rate=48000)
            frame = av.AudioFrame.from_ndarray(np.zeros((1, 1024), dtype=np.int16), format='s16', layout='mono')
            frame.sample_rate = 48000
            for packet in soundtrack.encode(frame):
                container.mux(packet)
            for packet in soundtrack.encode():
                container.mux(packet)
        for _ in range(count):
            frame = av.VideoFrame.from_ndarray(np.full((64, 64, 3), color, dtype=np.uint8), format='rgb24')
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


@pytest.fixture
def pilot(tmp_path):
    root = tmp_path / 'baseline'
    (root / 'input').mkdir(parents=True)
    (root / 'workflows').mkdir()
    (root / 'input/guide.wav').write_bytes(b'fixed-guide-test-only')
    keys = ['1','2','3','4','5','6','7','8','20','21','22','23','24','25','26','27','30','31','32','34','35']
    template = {k: {'class_type': 'TestNode', 'inputs': {}} for k in keys}
    template['20']['class_type'] = 'MiniMaxH3ReferenceToVideo'
    job = {'job_id': 's001_base', 'shot': 's001', 'visible_cast': ['b'],
           'pilot_override': {'purpose': 'isolated performer'}, 'portraits': ['portrait.png'],
           'keyframe': 'first.png', 'audio': 'guide.wav', 'frames': 124, 'steps': 12,
           'seed': 20, 'lock_guide_audio': True, 'output_prefix': 'base',
           'checkpoint_name': 'base_av.pt', 'workflow': 'workflows/base.json',
           'prompt': 'subject_definitions:\n<Subject 1> is Wang Ye in <Picture 1>.\n\nsummary:\nTest.\n\noverall_soundscape:\nTarget audio.'}
    graph = graph_for(template, job)
    (root / job['workflow']).write_text(json.dumps(graph))
    manifest = {'mode': 'pilot', 'jobs': [job], 'files': {
        'input/guide.wav': file_hash(root / 'input/guide.wav'),
        job['workflow']: file_hash(root / job['workflow'])}}
    (root / 'manifest.json').write_text(json.dumps(manifest))
    raw, pose = tmp_path / 'raw.mp4', tmp_path / 'pose.mp4'
    clip(raw)
    clip(pose, color=50)
    return root, raw, pose


def test_comparison_preserves_seed_guide_and_baseline_and_excludes_source_audio(pilot, tmp_path):
    baseline, raw, pose = pilot
    original = file_hash(baseline / 'manifest.json')
    out = tmp_path / 'comparison'
    report = compile_comparison(baseline, raw, pose, out, 'One deliberate hand accent followed by a hold.')
    assert len({v['job_id'] for v in report['variants'].values()}) == 3
    assert len({v['seed'] for v in report['variants'].values()}) == 1
    assert len({v['guide_sha256'] for v in report['variants'].values()}) == 1
    assert file_hash(baseline / 'manifest.json') == original
    for variant in report['variants']:
        data = json.loads((out / variant / 'manifest.json').read_text())
        job = data['jobs'][0]
        assert data['mode'] == 'pilot' and job['pilot_override']['motion_experiment'] == variant
        graph = json.loads((out / variant / job['workflow']).read_text())
        inputs = graph['20']['inputs']
        assert not any(k.startswith('ref_video_audios.') for k in inputs)
        assert ('ref_videos.ref_video_0' in inputs) == (variant != 'text_only')
    with pytest.raises(FileExistsError):
        compile_comparison(baseline, raw, pose, out, 'hold')


@pytest.mark.parametrize('options,match', [({'fps': 30}, '24 fps'),
                                         ({'count': 90}, 'expected 124'),
                                         ({'audio': True}, 'no source audio')])
def test_bad_reference_fails_before_output_creation(tmp_path, options, match):
    path = tmp_path / 'bad.mp4'
    clip(path, **options)
    with pytest.raises(ValueError, match=match):
        inspect_reference(path, 124)


def test_changed_reference_bytes_invalidate_the_pilot_job(pilot, tmp_path):
    baseline, raw, pose = pilot
    first = compile_comparison(baseline, raw, pose, tmp_path / 'one', 'hold')
    clip(pose, color=100)
    second = compile_comparison(baseline, raw, pose, tmp_path / 'two', 'hold')
    assert first['variants']['pose_reference']['job_id'] != second['variants']['pose_reference']['job_id']
    assert first['variants']['text_only']['job_id'] == second['variants']['text_only']['job_id']


def test_production_bundle_cannot_be_silently_rewritten_as_a_motion_pilot(pilot, tmp_path):
    baseline, raw, pose = pilot
    path = baseline / 'manifest.json'
    data = json.loads(path.read_text())
    data['mode'] = 'production'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='pilot shot'):
        compile_comparison(baseline, raw, pose, tmp_path / 'out', 'hold')
    assert not (tmp_path / 'out').exists()
