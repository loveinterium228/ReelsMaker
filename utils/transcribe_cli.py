'Isolated CPU speech transcription worker. Do not import Qt here. Progress is emitted to stderr and captions are written as SRT.'
import argparse
import sys

WORKER_FLAG = '--transcribe-worker'

LANGUAGE_CODES = {
    'russian': 'ru', 'english': 'en', 'ukrainian': 'uk',
    'german': 'de', 'french': 'fr', 'spanish': 'es', 'italian': 'it',
}

def _emit(kind, value):
    print('%s %s' % (kind, value), file=sys.stderr, flush=True)

def _format_time(seconds):
    milliseconds = max(0, round(seconds * 1000))
    seconds, ms = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return '%02d:%02d:%02d,%03d' % (hours, minutes, seconds, ms)

def run(args):
    if args.words_per_line <= 0:
        raise ValueError('Words per line must be greater than zero.')
    from faster_whisper import WhisperModel

    _emit('STAGE', 'loading')

    model = WhisperModel(args.model, device='cpu', compute_type='int8')

    language = None
    if args.language and args.language != 'Auto-detect':
        language = LANGUAGE_CODES.get(args.language.lower(), args.language.lower())

    _emit('STAGE', 'transcribing')
    segments, info = model.transcribe(args.audio, language=language,
                                      word_timestamps=True)

    total = getattr(info, 'duration', 0) or 0
    lines = []
    index = 1

    for segment in segments:
        words = getattr(segment, 'words', None)
        if not words:
            continue
        for start in range(0, len(words), args.words_per_line):
            chunk = words[start:start + args.words_per_line]
            if not chunk:
                continue
            text = ' '.join(word.word.strip() for word in chunk).strip()
            lines.append('%d\n%s --> %s\n%s\n\n' % (
                index, _format_time(chunk[0].start), _format_time(chunk[-1].end), text))
            index += 1
        if total > 0:
            _emit('PROGRESS', min(99, int(segment.end / total * 100)))

    with open(args.srt, 'w', encoding='utf-8') as handle:
        handle.write(''.join(lines))
    _emit('PROGRESS', 100)
    return 0

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(WORKER_FLAG, action='store_true', dest='worker')
    parser.add_argument('--audio', required=True)
    parser.add_argument('--srt', required=True)
    parser.add_argument('--model', default='base')
    parser.add_argument('--language', default='')
    parser.add_argument('--words-per-line', type=int, default=5, dest='words_per_line')
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as error:
        _emit('ERROR', error)
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
