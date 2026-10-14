import json
import subprocess
import sys

import pytest
from utils import ffmpeg_utils as ff
from utils.constants import REELS_FORMAT_NAME
from utils.constants import FILTERS


def render(source, output, **options):
    # A separate process imposes a hard limit on regressions that loop forever.
    params = dict(in_path=str(source), out_path=str(output), filters=[], zoom_p=100,
                  speed_p=100, overlay_file=None, overlay_pos='Middle center',
                  output_format='Original', blur_background=False)
    params.update(options)
    code = ('import json,sys; from utils import ffmpeg_utils as f; '
            'f.FFMPEG_PATH_EFFECTIVE=sys.argv[1]; f.FFPROBE_PATH_EFFECTIVE=sys.argv[2]; '
            'f.process_single(**json.loads(sys.argv[3]))')
    result = subprocess.run([sys.executable, '-c', code, ff.FFMPEG_PATH_EFFECTIVE,
                             ff.FFPROBE_PATH_EFFECTIVE, json.dumps(params)],
                            capture_output=True, text=True, encoding='utf-8', timeout=20)
    assert result.returncode == 0, result.stderr[-5000:]
    assert output.stat().st_size > 0
    return float(ff.probe_media(str(output))['format']['duration']), ff.get_video_dimensions(str(output))


def test_silent_video_exports_without_an_audio_stream(media, tmp_path):
    duration, size = render(media[0], tmp_path / 'out.mp4')
    assert duration == pytest.approx(1.2, abs=0.15)
    assert size == (160, 90)


def test_gif_is_finite(media, tmp_path):
    duration, _ = render(media[2], tmp_path / 'gif.mp4')
    assert 0.9 <= duration <= 1.4


def test_silent_split_screen_stops_with_main_video(media, tmp_path):
    duration, size = render(media[0], tmp_path / 'split.mp4',
                            output_format=REELS_FORMAT_NAME, filler_path=str(media[0]))
    assert duration == pytest.approx(1.2, abs=0.15)
    assert size == (1080, 1920)


def test_short_music_does_not_truncate_video(media, tmp_path):
    duration, _ = render(media[0], tmp_path / 'music.mp4', overlay_audio_path=str(media[1]))
    assert duration == pytest.approx(1.2, abs=0.15)


def test_zoom_out_preserves_vertical_canvas(media, tmp_path):
    _, size = render(media[0], tmp_path / 'zoom.mp4', zoom_p=51,
                     output_format=REELS_FORMAT_NAME, mute_audio=True)
    assert size == (1080, 1920)


def test_zoom_out_preserves_original_canvas(media, tmp_path):
    _, size = render(media[0], tmp_path / 'original-zoom.mp4', zoom_p=51, mute_audio=True)
    assert size == (160, 90)


@pytest.mark.parametrize('filter_name', [name for name in FILTERS if name != 'No filter'])
def test_each_filter_can_render(media, tmp_path, filter_name):
    duration, size = render(media[0], tmp_path / 'filter.mp4', filters=[filter_name], mute_audio=True)
    assert duration > 1
    assert size == (160, 90)


@pytest.mark.parametrize('speed,expected', [(50, 2.4), (200, 0.6)])
def test_speed_changes_duration(media, tmp_path, speed, expected):
    duration, _ = render(media[0], tmp_path / 'speed.mp4', speed_p=speed, mute_audio=True)
    assert duration == pytest.approx(expected, abs=0.15)


def test_long_music_does_not_extend_video(media, tmp_path):
    audio = tmp_path / 'long.wav'
    ff.run_ffmpeg(['-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', str(audio)])
    duration, _ = render(media[0], tmp_path / 'music-long.mp4', overlay_audio_path=str(audio))
    assert duration == pytest.approx(1.2, abs=0.15)


def test_original_audio_tail_does_not_extend_the_picture(media, tmp_path):
    source = tmp_path / 'long-audio-tail.mp4'
    ff.run_ffmpeg(['-y', '-i', str(media[0]), '-f', 'lavfi', '-i',
                  'sine=frequency=440:duration=3', '-c:v', 'copy', '-c:a', 'aac', str(source)])
    duration, _ = render(source, tmp_path / 'tail.mp4')
    assert duration == pytest.approx(1.2, abs=0.15)


def test_preview_uses_random_background(media, tmp_path):
    output = tmp_path / 'preview.png'
    ff.generate_preview(str(media[0]), str(output), [], 100, None, 'Middle center',
                         REELS_FORMAT_NAME, False, filler_path='__random__')
    from PyQt5.QtGui import QImage
    image = QImage(str(output))
    assert (image.width(), image.height()) == (1080, 1920)


def test_imported_srt_burns_with_default_style(media, tmp_path):
    srt = tmp_path / 'default.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nDefault caption\n')
    _, size = render(media[0], tmp_path / 'default.mp4', mute_audio=True, srt_path=str(srt))
    assert size == (160, 90)


def test_subtitle_path_with_apostrophe_and_punctuation(media, tmp_path):
    srt = tmp_path / "Editor's [draft], captions.srt"
    srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nHello world\n', encoding='utf-8')
    duration, _ = render(media[0], tmp_path / 'captions.mp4', mute_audio=True,
                         srt_path=str(srt), subtitle_style={'size': 24})
    assert duration > 1


def test_render_errors_preserve_diagnostics(tmp_path):
    with pytest.raises(subprocess.CalledProcessError) as caught:
        ff.run_ffmpeg(['-i', str(tmp_path / 'missing.mp4'), '-f', 'null', '-'])
    assert 'No such file' in caught.value.stderr or 'Error opening input' in caught.value.stderr


def test_relative_paths_are_relative_to_calling_directory(media, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ff.run_ffmpeg(['-y', '-i', media[0].name, '-frames:v', '1', 'frame.png'])
    assert (tmp_path / 'frame.png').is_file()


def test_style_options_reach_export_filter(media, tmp_path, monkeypatch):
    command = []
    monkeypatch.setattr(ff, 'run_ffmpeg', lambda cmd, **kwargs: command.extend(cmd))
    srt = tmp_path / 'test.srt'
    srt.write_text('1\n00:00:00,000 --> 00:00:01,000\nCaption\n')
    ff.process_single(str(media[0]), str(tmp_path / 'out.mp4'), [], 100, 100, None,
                      'Middle center', 'Original', False, mute_audio=True,
                      srt_path=str(srt), subtitle_style={'font': 'Verdana', 'size': 28,
                      'color': '#12AB34', 'position': 8, 'bold': True})
    graph = command[command.index('-filter_complex') + 1]
    assert 'FontName=Verdana' in graph
    assert 'FontSize=28' in graph
    assert 'PrimaryColour=&H0034AB12' in graph
    assert 'Alignment=8' in graph
    assert 'Bold=-1' in graph
