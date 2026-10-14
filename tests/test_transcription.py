import sys
import subprocess
from types import SimpleNamespace

import pytest
from utils import transcribe_cli as cli


@pytest.mark.parametrize('language,expected', [('German', 'de'), ('French', 'fr'),
                                             ('Spanish', 'es'), ('Italian', 'it')])
def test_ui_languages_use_iso_codes(tmp_path, monkeypatch, language, expected):
    class Model:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, path, **kwargs):
            assert kwargs['language'] == expected
            words = [SimpleNamespace(word=' Hello', start=0., end=0.4),
                     SimpleNamespace(word=' world', start=0.4, end=0.8)]
            return iter([SimpleNamespace(words=words, end=0.8)]), SimpleNamespace(duration=1.)
    monkeypatch.setitem(sys.modules, 'faster_whisper', SimpleNamespace(WhisperModel=Model))
    output = tmp_path / 'captions.srt'
    args = SimpleNamespace(model='tiny', audio='audio.wav', srt=str(output),
                           language=language, words_per_line=4)
    cli.run(args)
    assert 'Hello world' in output.read_text(encoding='utf-8')


def test_srt_timestamps_round_to_nearest_millisecond():
    assert cli._format_time(1.001) == '00:00:01,001'
    assert cli._format_time(59.9999) == '00:01:00,000'


def test_whisper_can_decode_audio_with_installed_dependencies(media):
    # Run outside Qt, matching the production native-library isolation boundary.
    code = ('from faster_whisper.audio import decode_audio; import sys; '
            'audio=decode_audio(sys.argv[1]); assert len(audio)>1000')
    result = subprocess.run([sys.executable, '-c', code, str(media[1])],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
