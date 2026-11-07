"""A song ending between frame boundaries must not remove the final picture."""
import json
import shutil
import subprocess
from types import SimpleNamespace as NS

import numpy as np
import pytest
import soundfile as sf

from aigc_mv.edit import package
from aigc_mv.tools import ffmpeg_exe


def test_package_retains_rounded_last_frame_and_original_song_duration(tmp_path):
    probe = shutil.which('ffprobe')
    if probe is None:
        pytest.skip('ffprobe required for the media regression')
    (tmp_path/'audio').mkdir();(tmp_path/'edit').mkdir()
    seconds=.62;frames=round(seconds*24)
    sf.write(tmp_path/'audio/song.wav',np.zeros((round(seconds*48000),2)),48000)
    picture=tmp_path/'edit/picture.mp4'
    subprocess.run([ffmpeg_exe(),'-v','error','-y','-f','lavfi','-i',
                    'color=c=navy:s=192x108:r=24','-frames:v',str(frames),
                    '-c:v','libx264','-pix_fmt','yuv420p',str(picture)],check=True)
    episode=NS(fps=24,format='battle',title='frame_boundary',song='audio/song.wav',subtitle_style='broadcast')
    result=package(tmp_path,episode,NS(duration=seconds),NS(lines=[]),picture,(192,108),0,seconds,
                   look=False,overlays=False,beat=False)
    streams=json.loads(subprocess.check_output([probe,'-v','error','-show_streams','-of','json',str(result)]))['streams']
    video=next(s for s in streams if s['codec_type']=='video');audio=next(s for s in streams if s['codec_type']=='audio')
    assert int(video['nb_frames'])==frames
    assert video['avg_frame_rate']=='24/1'
    assert abs(float(audio['duration'])-seconds)<1/48000
