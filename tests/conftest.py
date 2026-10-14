import os
import shutil
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import pytest
from PyQt5.QtWidgets import QApplication
from utils import ffmpeg_utils as ff


@pytest.fixture(scope='session', autouse=True)
def tools():
    ffmpeg = os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
    ffprobe = os.environ.get('FFPROBE_BINARY') or shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        pytest.fail('Install FFmpeg and FFprobe or set FFMPEG_BINARY and FFPROBE_BINARY.')
    ff.FFMPEG_PATH_EFFECTIVE = str(Path(ffmpeg).resolve())
    ff.FFPROBE_PATH_EFFECTIVE = str(Path(ffprobe).resolve())


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    # Keep QtAwesome's font installation inside the test workspace.
    os.environ['LOCALAPPDATA'] = str(tmp_path_factory.mktemp('qt-localdata'))
    os.environ['APPDATA'] = str(tmp_path_factory.mktemp('appdata'))
    return QApplication.instance() or QApplication([])


@pytest.fixture
def media(tmp_path):
    video = tmp_path / 'silent.mp4'
    ff.run_ffmpeg(['-y', '-f', 'lavfi', '-i', 'testsrc2=s=160x90:r=10:d=1.2',
                  '-an', '-c:v', 'libx264', str(video)])
    audio = tmp_path / 'music.wav'
    ff.run_ffmpeg(['-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.4', str(audio)])
    gif = tmp_path / 'animation.gif'
    ff.run_ffmpeg(['-y', '-i', str(video), str(gif)])
    return video, audio, gif
