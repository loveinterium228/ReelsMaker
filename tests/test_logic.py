"""Deterministic decisions at the encoder boundary; no media rendering required."""
from copy import deepcopy

import pytest

from utils import ffmpeg_utils as ff
from utils.constants import REELS_FORMAT_NAME, RANDOM_FILLER
from utils.process_utils import ProcessController, ProcessingCancelled


@pytest.mark.parametrize('info,expected', [
    ({'streams': [{'codec_type': 'video', 'duration': '2.5'},
                  {'codec_type': 'audio', 'duration': '10'}], 'format': {'duration': '10'}}, 2.5),
    ({'streams': [{'codec_type': 'video', 'duration': 'N/A'}], 'format': {'duration': '4'}}, 4),
    ({'streams': [{'codec_type': 'audio', 'duration': '10'},
                  {'codec_type': 'video', 'duration': '3'}], 'format': {'duration': '10'}}, 3),
    ({'streams': [{'codec_type': 'video', 'duration': 'nan'}], 'format': {'duration': '7'}}, 7),
    ({'streams': [{'codec_type': 'video', 'duration': '-1'}], 'format': {'duration': '6'}}, 6),
    ({'streams': [{'codec_type': 'video', 'duration': 'inf'}], 'format': {'duration': '0'}}, 0),
    ({}, 0),
])
def test_duration_uses_valid_picture_length_before_container_length(info, expected):
    assert ff._media_duration(info) == expected


@pytest.fixture
def encoder_boundary(monkeypatch):
    metadata = {'streams': [{'codec_type': 'video', 'duration': '10'},
                            {'codec_type': 'audio', 'duration': '10'}],
                'format': {'duration': '10'}}
    commands = []
    monkeypatch.setattr(ff, 'probe_media', lambda *args: deepcopy(metadata))
    monkeypatch.setattr(ff, 'run_ffmpeg', lambda cmd, **kwargs: commands.append((cmd, kwargs)))
    return metadata, commands


def export_options(tmp_path, **overrides):
    args = dict(in_path=str(tmp_path / 'input.mp4'), out_path=str(tmp_path / 'output.mp4'),
                filters=[], zoom_p=100, speed_p=100, overlay_file=None,
                overlay_pos='Middle center', output_format='Original', blur_background=False)
    args.update(overrides)
    return args


@pytest.mark.parametrize('zoom,speed', [(0, 100), (-10, 100), (100, 0), (100, -10)])
def test_nonpositive_transform_rejected_before_starting_encoder(tmp_path, encoder_boundary, zoom, speed):
    with pytest.raises(ValueError):
        ff.process_single(**export_options(tmp_path, zoom_p=zoom, speed_p=speed))
    assert encoder_boundary[1] == []


def test_export_cannot_replace_its_source(tmp_path, encoder_boundary):
    source = tmp_path / 'input.mp4'
    source.write_bytes(b'keep the original')
    with pytest.raises(ValueError):
        ff.process_single(**export_options(tmp_path, out_path=str(source)))
    assert source.read_bytes() == b'keep the original'
    assert encoder_boundary[1] == []


@pytest.mark.parametrize('asset', ['overlay_file', 'overlay_audio_path', 'srt_path'])
def test_missing_requested_asset_does_not_silently_disappear(tmp_path, encoder_boundary, asset):
    with pytest.raises(FileNotFoundError):
        ff.process_single(**export_options(tmp_path, **{asset: str(tmp_path / 'missing')}))
    assert encoder_boundary[1] == []


@pytest.mark.parametrize('format_name', ['Original', REELS_FORMAT_NAME])
def test_unused_background_is_not_resolved(tmp_path, encoder_boundary, monkeypatch, format_name):
    def empty_library():
        raise FileNotFoundError('Empty library')
    monkeypatch.setattr(ff, 'pick_random_filler', empty_library)
    args = export_options(tmp_path, output_format=format_name, filler_path=RANDOM_FILLER)
    if format_name == 'Original':
        ff.process_single(**args)
        assert len(encoder_boundary[1]) == 1
    else:
        with pytest.raises(FileNotFoundError):
            ff.process_single(**args)
        assert encoder_boundary[1] == []


@pytest.mark.parametrize('explicit_speed,expected_duration', [(100, 5.0), (200, 4.5)])
def test_explicit_speed_takes_priority_over_per_file_variation(
        tmp_path, encoder_boundary, monkeypatch, explicit_speed, expected_duration):
    monkeypatch.setattr(ff, 'build_uniquify_plan', lambda *args: {
        'head': .4, 'tail': .6, 'speed': 1.8, 'pitch': 1., 'crf': 20, 'gop': 60})
    ff.process_single(**export_options(tmp_path, speed_p=explicit_speed, uniquify=True))
    command, callbacks = encoder_boundary[1][0]
    assert float(command[command.index('-t') + 1]) == expected_duration
    assert callbacks['duration'] == expected_duration
    graph = command[command.index('-filter_complex') + 1]
    assert 'atrim=start=0.4:end=9.4' in graph


def test_tiny_clip_is_not_destroyed_by_random_trimming(tmp_path, encoder_boundary, monkeypatch):
    encoder_boundary[0]['streams'][0]['duration'] = '.3'
    monkeypatch.setattr(ff, 'build_uniquify_plan', lambda *args: {
        'head': .4, 'tail': .6, 'speed': 1., 'pitch': 1., 'crf': 20, 'gop': 60})
    ff.process_single(**export_options(tmp_path, uniquify=True))
    command, _ = encoder_boundary[1][0]
    assert float(command[command.index('-t') + 1]) == .3


def test_muting_source_keeps_requested_overlay_audio(tmp_path, encoder_boundary):
    audio = tmp_path / 'music.wav'
    audio.touch()
    ff.process_single(**export_options(tmp_path, mute_audio=True, overlay_audio_path=str(audio)))
    command, _ = encoder_boundary[1][0]
    graph = command[command.index('-filter_complex') + 1]
    assert '[0:a]' not in graph
    assert '[1:a]' in graph
    assert '-an' not in command
    assert '[aout]' in command


@pytest.mark.parametrize('streams', [[], [{'codec_type': 'audio'}]])
def test_nonvideo_inputs_are_rejected_before_encoding(tmp_path, encoder_boundary, streams):
    encoder_boundary[0]['streams'] = streams
    with pytest.raises(ValueError):
        ff.process_single(**export_options(tmp_path))
    assert encoder_boundary[1] == []


def test_cancelled_controller_rejects_future_work_without_spawning(monkeypatch):
    controller = ProcessController()
    controller.cancel()
    controller.cancel()
    def unexpected_spawn(*args, **kwargs):
        pytest.fail('No child process should start after cancellation.')
    monkeypatch.setattr(ff.subprocess, 'Popen', unexpected_spawn)
    with pytest.raises(ProcessingCancelled):
        ff.run_ffmpeg(['-version'], controller=controller)


def test_original_preview_ignores_the_disabled_split_background(tmp_path, encoder_boundary, monkeypatch):
    monkeypatch.setattr(ff, 'get_video_duration', lambda path: 10)
    def empty_library():
        raise FileNotFoundError('Empty library')
    monkeypatch.setattr(ff, 'pick_random_filler', empty_library)
    args = export_options(tmp_path, filler_path=RANDOM_FILLER)
    args.pop('speed_p')
    ff.generate_preview(**args)
    assert len(encoder_boundary[1]) == 1


@pytest.mark.parametrize('value,expected', [(0, '00:00:00,000'),
                                          (-1, '00:00:00,000'),
                                          (3599.9999, '01:00:00,000'),
                                          (3661.25, '01:01:01,250')])
def test_srt_time_carries_across_boundaries(value, expected):
    from utils.transcribe_cli import _format_time
    assert _format_time(value) == expected
