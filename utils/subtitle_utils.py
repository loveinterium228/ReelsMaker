"""Audio extraction and isolated, cancellable speech transcription."""
import logging
import os
import subprocess
import sys

from .ffmpeg_utils import run_ffmpeg
from .transcribe_cli import WORKER_FLAG
from .process_utils import finish_process, hidden_process_options

logger = logging.getLogger(__name__)

def extract_audio(video_path, audio_path, controller=None):
    run_ffmpeg(['-y', '-i', video_path, '-vn', '-ar', '16000', '-ac', '1',
                '-c:a', 'pcm_s16le', audio_path], video_path, controller=controller)

def _worker_command(audio_path, srt_path, model_name, language, words_per_line):
    arguments = [WORKER_FLAG, '--audio', audio_path, '--srt', srt_path,
                 '--model', model_name or 'base', '--language', language or '',
                 '--words-per-line', str(words_per_line or 5)]
    if getattr(sys, 'frozen', False):
        worker = os.path.join(os.path.dirname(os.path.abspath(sys.executable)),
                              'transcriber', 'rm-transcribe.exe')
        return [worker] + arguments
    return [sys.executable, os.path.join(os.path.dirname(__file__), 'transcribe_cli.py')] + arguments

def generate_srt_from_whisper(audio_path, srt_path, model_name='base', language=None,
                              words_per_line=5, progress_callback=None, controller=None):
    if controller:
        controller.check()
    command = _worker_command(audio_path, srt_path, model_name, language, words_per_line)
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, text=True, encoding='utf-8',
                               errors='replace', bufsize=1, **hidden_process_options())
    if controller:
        controller.attach(process)
    failure = None
    try:
        for line in process.stderr:
            if controller:
                controller.check()
            line = line.strip()
            if line.startswith('PROGRESS ') and progress_callback:
                try:
                    progress_callback(int(line.split(' ', 1)[1]))
                except ValueError:
                    pass
            elif line.startswith('ERROR '):
                failure = line.split(' ', 1)[1]
            elif line:
                logger.info('transcriber: %s', line)
        code = process.wait()
        if controller:
            controller.check()
        if code or failure or not os.path.isfile(srt_path):
            raise RuntimeError('Speech transcription failed. The first run requires internet '
                               'access to download the model. Details: ' +
                               (failure or f'exit code {code}'))
        return srt_path
    finally:
        finish_process(process)
        process.stderr.close()
        if controller:
            controller.detach(process)
