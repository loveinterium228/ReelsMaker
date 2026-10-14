"""Report usable FFmpeg encoders without requiring PyTorch or CUDA."""
from utils.constants import CODECS
from utils.ffmpeg_utils import detect_available_codecs


def main():
    for label, available in detect_available_codecs(CODECS).items():
        print(f"{'OK' if available else 'Unavailable':12} {label}")


if __name__ == '__main__':
    main()
