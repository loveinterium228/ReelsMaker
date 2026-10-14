APP_NAME = "ReelsMaker Pro"
APP_VERSION = "1.1.0"
LOG_FILE = "app.log"
import os

FFMPEG_EXE_PATH = 'ffmpeg/bin/ffmpeg.exe' if os.name == 'nt' else 'ffmpeg/bin/ffmpeg'

VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv']
GIF_EXTENSIONS = ['.gif']
VALID_INPUT_EXTENSIONS = VIDEO_EXTENSIONS + GIF_EXTENSIONS

FILTERS = {
    'No filter': "",
    'Random color': "eq=brightness={br}:contrast={ct}:saturation={sat},hue=h={hue}",
    'Black and white': "hue=s=0",
    'Sepia': "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131:0",
    'Invert colors': "negate",
    'Light blur': "gblur=sigma=2",
    'Strong blur': "gblur=sigma=10",
    'Flip horizontally': "hflip",
    'Flip vertically': "vflip",
    'Pixelate': "scale=iw/10:ih/10,scale=iw*10:ih*10:flags=neighbor",
    'VHS noise and shift': "chromashift=1:1,noise=alls=20:allf=t+u",
    'Increase contrast': "eq=contrast=1.5",
    'Decrease contrast': "eq=contrast=0.7",
    'Increase saturation': "eq=saturation=1.5",
    'Decrease saturation': "eq=saturation=0.5",
    'Increase brightness': "eq=brightness=0.15",
    'Decrease brightness': "eq=brightness=-0.15",
    'Cool tones': "curves=b='0/0 0.4/0.5 1/1':g='0/0 0.4/0.4 1/1'",
    'Warm tones': "curves=r='0/0 0.4/0.5 1/1':g='0/0 0.6/0.6 1/1'",
    'Vignette': "vignette=PI/4",
    'Strong vignette': "vignette=PI/3",
    'Lens distortion': "lenscorrection=k1=-0.227:k2=-0.022",
    'RGB shift': "chromashift=cbh=-2:crh=2",
    'Film grain': "noise=alls=12:allf=t",
    'Heavy noise': "noise=alls=25:allf=t+u",
    'Sharpen': "unsharp=5:5:1.0:5:5:0.0",
    'Soft focus': "smartblur=1.5:-0.35",
    "Cyan-Magenta": "colorbalance=rs=.3:gs=-.1:bs=-.2",
    "Orange-Teal": "colorbalance=rs=.15:bs=-.15",
    'Random filter': "RANDOM_PLACEHOLDER"
}

FILTER_GROUPS = (
    ('Color', [
        'Random color',
        'Black and white',
        'Sepia',
        'Invert colors',
        'Cool tones',
        'Warm tones',
        "Cyan-Magenta",
        "Orange-Teal",
    ]),
    ('Brightness and contrast', [
        'Increase contrast',
        'Decrease contrast',
        'Increase saturation',
        'Decrease saturation',
        'Increase brightness',
        'Decrease brightness',
    ]),
    ('Sharpness and blur', [
        'Sharpen',
        'Soft focus',
        'Light blur',
        'Strong blur',
    ]),
    ('Film and noise', [
        'VHS noise and shift',
        'Film grain',
        'Heavy noise',
        'RGB shift',
        'Vignette',
        'Strong vignette',
    ]),
    ('Geometry', [
        'Flip horizontally',
        'Flip vertically',
        'Lens distortion',
        'Pixelate',
    ]),
    ('Special', [
        'Random filter',
    ]),
)

SUBTITLE_PRESETS = {
    'Classic': {
        "font": "Arial",
        "size": 36,
        "color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 2,
        "shadow": 1,
        "bold": False,
        "position": 2
    },
    'Bold TikTok': {
        "font": "Arial Black",
        "size": 42,
        "color": "#FFFFFF",
        "outline_color": "#000000",
        "outline_width": 3,
        "shadow": 2,
        "bold": True,
        "position": 5
    },
    'Neon': {
        "font": "Impact",
        "size": 40,
        "color": "#00FF00",
        "outline_color": "#0000FF",
        "outline_width": 3,
        "shadow": 3,
        "bold": False,
        "position": 2
    },
    'Minimal': {
        "font": "Calibri",
        "size": 32,
        "color": "#F0F0F0",
        "outline_color": "#1A1A1A",
        "outline_width": 1,
        "shadow": 0,
        "bold": False,
        "position": 2
    },
    'YouTube style': {
        "font": "Roboto",
        "size": 38,
        "color": "#FFFFFF",
        "outline_color": "#CC0000",
        "outline_width": 2,
        "shadow": 2,
        "bold": True,
        "position": 8
    }
}

ROTATION_RANGE = (-3, 3)
AUDIO_PITCH_RANGE = (0.95, 1.05)
CROP_RANDOM_OFFSET = 20

OVERLAY_POSITIONS = {
    'Top left': "x=20:y=70",
    'Top center': "x=(W-w)/2:y=10",
    'Top right': "x=W-w-10:y=10",
    'Middle left': "x=10:y=(H-h)/2",
    'Middle center': "x=(W-w)/2:y=(H-h)/2",
    'Middle right': "x=W-w-10:y=(H-h)/2",
    'Bottom left': "x=10:y=H-h-10",
    'Bottom center': "x=(W-w)/2:y=H-h-10",
    'Bottom right': "x=W-w-10:y=H-h-10"
}

REELS_WIDTH = 1080
REELS_HEIGHT = 1920
REELS_FORMAT_NAME = f"Reels/TikTok ({REELS_WIDTH}x{REELS_HEIGHT})"
OUTPUT_FORMATS = ['Original', REELS_FORMAT_NAME]

SPLIT_LAYOUTS = {
    'Square content - 1080 / 840 px': 1080,
    'Equal panels - 960 / 960 px': 960,
    'Larger content - 1280 / 640 px': 1280,
    'Larger background - 840 / 1080 px': 840,
}
SPLIT_CONTENT_TOP = 'Content above background'
SPLIT_CONTENT_BOTTOM = 'Background above content'
SPLIT_POSITIONS = [SPLIT_CONTENT_TOP, SPLIT_CONTENT_BOTTOM]

PRESETS_DIR = "resources/presets"

RANDOM_FILLER = "__random__"

SCENARIOS = {
    'Vertical video 9:16': {
        "output_format": REELS_FORMAT_NAME,
        "blur_background": True,
        "auto_crop": True,
        "split": False,
        "subtitles": False,
    },
    'Vertical video with captions': {
        "output_format": REELS_FORMAT_NAME,
        "blur_background": True,
        "auto_crop": True,
        "split": False,
        "subtitles": True,
    },
    'Split-screen video': {
        "output_format": REELS_FORMAT_NAME,
        "blur_background": False,
        "auto_crop": False,
        "split": True,
        "subtitles": False,
    },
    'Transcode only': {
        "output_format": 'Original',
        "blur_background": False,
        "auto_crop": False,
        "split": False,
        "subtitles": False,
    },
    'Custom settings': {},
}

CODECS = {
    "CPU (H.264 | libx264)": "libx264",
    "NVIDIA (H.264 | h264_nvenc)": "h264_nvenc",
    "NVIDIA (H.265 | hevc_nvenc)": "hevc_nvenc",
    "Intel (H.264 | h264_qsv)": "h264_qsv",
    "Intel (H.265 | hevc_qsv)": "hevc_qsv",
    "AMD (H.264 | h264_amf)": "h264_amf",
    "AMD (H.265 | hevc_amf)": "hevc_amf",
}

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
WHISPER_LANGUAGES = ["Auto-detect", "Russian", "English", "Ukrainian", "German", "French", "Spanish", "Italian"]
