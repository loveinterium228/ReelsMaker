"""FFmpeg discovery, probing and shared preview/export filter graphs."""
import json
import logging
import math
import os
import random
import re
import shutil
import subprocess
from collections import deque

from .constants import (FFMPEG_EXE_PATH, FILTERS, OVERLAY_POSITIONS, REELS_WIDTH,
                        REELS_HEIGHT, REELS_FORMAT_NAME, PRESETS_DIR,
                        VIDEO_EXTENSIONS, RANDOM_FILLER)
from .path_utils import resource_path, user_data_dir
from .process_utils import (finish_process,
                            hidden_process_options, run_capture)

logger = logging.getLogger(__name__)

def find_executable(base_path, exe_name):
    if os.path.isfile(base_path):
        return os.path.abspath(base_path)
    return shutil.which(exe_name)

FFMPEG_PATH_BASE = resource_path(FFMPEG_EXE_PATH)
FFPROBE_PATH_BASE = os.path.join(os.path.dirname(FFMPEG_PATH_BASE),
                               'ffprobe.exe' if os.name == 'nt' else 'ffprobe')
FFMPEG_PATH_EFFECTIVE = find_executable(FFMPEG_PATH_BASE, 'ffmpeg')
FFPROBE_PATH_EFFECTIVE = find_executable(FFPROBE_PATH_BASE, 'ffprobe')

def configure_ffmpeg(path=''):
    """Apply a custom executable and its sibling FFprobe, or restore discovery."""
    global FFMPEG_PATH_EFFECTIVE, FFPROBE_PATH_EFFECTIVE
    if path:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(path):
            raise FileNotFoundError('FFmpeg executable does not exist: ' + path)
        probe = os.path.join(os.path.dirname(path), 'ffprobe.exe' if os.name == 'nt' else 'ffprobe')
        if not os.path.isfile(probe):
            raise FileNotFoundError('Place FFprobe alongside FFmpeg: ' + probe)
        result = run_capture([path, '-version'], timeout=10)
        if result.returncode or 'ffmpeg version' not in result.stdout.lower():
            raise ValueError('The selected executable is not a working FFmpeg build.')
        result = run_capture([probe, '-version'], timeout=10)
        if result.returncode or 'ffprobe version' not in result.stdout.lower():
            raise ValueError('The sibling executable is not a working FFprobe build.')
        FFMPEG_PATH_EFFECTIVE, FFPROBE_PATH_EFFECTIVE = path, probe
    else:
        FFMPEG_PATH_EFFECTIVE = find_executable(FFMPEG_PATH_BASE, 'ffmpeg')
        FFPROBE_PATH_EFFECTIVE = find_executable(FFPROBE_PATH_BASE, 'ffprobe')

def run_ffmpeg(cmd, input_file_for_log='input', duration=0, progress_callback=None,
               controller=None):
    if not FFMPEG_PATH_EFFECTIVE:
        raise FileNotFoundError('FFmpeg was not found. Install it or choose its path in Settings.')
    if controller:
        controller.check()
    command = [FFMPEG_PATH_EFFECTIVE, '-nostdin', '-hide_banner']
    if '-loglevel' not in cmd:
        command.extend(['-loglevel', 'info'])
    if progress_callback:
        command.extend(['-progress', 'pipe:1', '-nostats'])
    command.extend(cmd)
    logger.info('Running FFmpeg: %s', subprocess.list2cmdline(command))
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               stdin=subprocess.DEVNULL, text=True, encoding='utf-8',
                               errors='replace', bufsize=1, **hidden_process_options())
    if controller:
        controller.attach(process)
    tail = deque(maxlen=120)
    try:
        for line in process.stdout:
            if controller:
                controller.check()
            line = line.strip()
            tail.append(line)
            logger.debug('FFmpeg: %s', line)
            if progress_callback and duration > 0 and line.startswith('out_time_us='):
                try:
                    progress_callback(min(99, max(0, int(int(line.split('=', 1)[1]) / duration / 10000))))
                except ValueError:
                    pass
        code = process.wait()
        if controller:
            controller.check()
        if code:
            output = '\n'.join(tail)
            raise subprocess.CalledProcessError(code, command, output=output, stderr=output)
        if progress_callback:
            progress_callback(100)
    finally:
        finish_process(process)
        process.stdout.close()
        if controller:
            controller.detach(process)

def probe_media(path, controller=None):
    if not FFPROBE_PATH_EFFECTIVE:
        raise FileNotFoundError('FFprobe was not found. Install it alongside FFmpeg.')
    command = [FFPROBE_PATH_EFFECTIVE, '-v', 'error', '-show_streams',
               '-show_format', '-of', 'json', os.path.abspath(path)]
    result = run_capture(command, controller=controller)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command,
                                            output=result.stdout, stderr=result.stderr)
    return json.loads(result.stdout)

def get_video_dimensions(path):
    try:
        stream = next(s for s in probe_media(path)['streams'] if s['codec_type'] == 'video')
        return int(stream['width']), int(stream['height'])
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as error:
        logger.warning('Cannot probe dimensions for %s: %s', path, error)
        return 0, 0

def _media_duration(info):
    video = next((stream for stream in info.get('streams', [])
                  if stream.get('codec_type') == 'video'), {})
    for value in (video.get('duration'), info.get('format', {}).get('duration')):
        try:
            duration = float(value)
            if math.isfinite(duration) and duration > 0:
                return duration
        except (TypeError, ValueError):
            pass
    return 0.0


def get_video_duration(path):
    try:
        return _media_duration(probe_media(path))
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        logger.warning('Cannot probe duration for %s: %s', path, error)
        return 0.0

def detect_crop_dimensions(path, controller=None):
    duration = get_video_duration(path)
    start = min(5, duration * 0.25) if duration > 0 else 0
    if not FFMPEG_PATH_EFFECTIVE:
        raise FileNotFoundError('FFmpeg was not found.')
    result = run_capture([FFMPEG_PATH_EFFECTIVE, '-nostdin', '-hide_banner', '-ss', str(start),
                          '-i', path, '-t', '10', '-vf', 'cropdetect=limit=24:round=2',
                          '-an', '-f', 'null', '-'], timeout=60, controller=controller)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, result.args, stderr=result.stderr)
    matches = re.findall(r'crop=(\d+):(\d+):(\d+):(\d+)', result.stderr)
    # Completely black frames can produce invalid negative/zero crop boxes.
    valid = [m for m in matches if int(m[0]) > 0 and int(m[1]) > 0]
    return 'crop=' + ':'.join(valid[-1]) if valid else None

def probe_encoder(codec, timeout=20, controller=None):
    if not FFMPEG_PATH_EFFECTIVE:
        return False
    try:
        result = run_capture([FFMPEG_PATH_EFFECTIVE, '-nostdin', '-hide_banner', '-loglevel', 'error',
                              '-f', 'lavfi', '-i', 'color=black:s=256x256:d=0.1',
                              '-frames:v', '1', '-c:v', codec, '-f', 'null', '-'], timeout=timeout,
                             controller=controller)
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False

def detect_available_codecs(codecs):
    return {label: probe_encoder(codec) for label, codec in codecs.items()}

def build_split_screen_filter(content_node, filler_node, content_height, content_on_top):
    height = max(2, min(REELS_HEIGHT - 2, int(content_height)))
    height -= height % 2
    other_height = REELS_HEIGHT - height
    panels = (
        f'{content_node}setpts=PTS-STARTPTS,scale={REELS_WIDTH}:{height}:force_original_aspect_ratio=increase,'
        f'crop={REELS_WIDTH}:{height},setsar=1[sp_content];'
        f'{filler_node}setpts=PTS-STARTPTS,scale={REELS_WIDTH}:{other_height}:force_original_aspect_ratio=increase,'
        f'crop={REELS_WIDTH}:{other_height},setsar=1[sp_filler];')
    order = '[sp_content][sp_filler]' if content_on_top else '[sp_filler][sp_content]'
    return panels + order + 'vstack=inputs=2:shortest=1[formatted]'

def user_presets_dir():
    return os.path.join(user_data_dir(), 'presets')

def list_filler_presets():
    found = []
    for folder in (resource_path(PRESETS_DIR), user_presets_dir()):
        if os.path.isdir(folder):
            found.extend(os.path.join(folder, name) for name in os.listdir(folder)
                         if os.path.splitext(name)[1].lower() in VIDEO_EXTENSIONS
                         and os.path.isfile(os.path.join(folder, name)))
    return sorted(found, key=lambda path: os.path.basename(path).lower())

def pick_random_filler():
    presets = list_filler_presets()
    if not presets:
        raise FileNotFoundError('No background clips found. Add a clip to the background library.')
    return random.choice(presets)

def build_uniquify_plan(in_path, methods=None):
    """Choose optional editing variations independently for each input."""
    on = methods or {}
    return {
        'head': round(random.uniform(0.10, 0.40), 3) if on.get('trim', True) else 0.0,
        'tail': round(random.uniform(0.15, 0.60), 3) if on.get('trim', True) else 0.0,
        'pitch': round(random.uniform(0.994, 1.006), 4) if on.get('pitch', True) else 1.0,
        'speed': round(random.uniform(0.97, 1.03), 4) if on.get('speed', False) else 1.0,
        'crf': random.randint(19, 23) if on.get('encode', True) else 24,
        'gop': random.choice([48, 50, 60, 72, 75]) if on.get('encode', True) else 0,
    }

def _escape_filter_value(value):
    # Escape both the filter-option parser and the surrounding graph parser.
    inner = ''.join('\\' + c if c in "\\':" else c for c in str(value))
    return ''.join('\\' + c if c in "\\'[],;" else c for c in inner)

def subtitle_filter(srt_path, style=None):
    style = style or {}

    def ass_color(color):
        color = color.lstrip('#')
        if not re.fullmatch('[0-9a-fA-F]{6}', color):
            raise ValueError('Subtitle colors must use #RRGGBB format.')
        return '&H00' + color[4:6] + color[2:4] + color[0:2]

    font = style.get('font', 'Arial')
    if any(c in font for c in ',\r\n'):
        raise ValueError('Invalid subtitle font name.')
    params = [f"Alignment={int(style.get('position', 2))}", 'MarginL=25', 'MarginR=25',
              'MarginV=70', f'FontName={font}',
              f"FontSize={int(style.get('size', style.get('font_size', 36)))}",
              'PrimaryColour=' + ass_color(style.get('color', '#FFFFFF')),
              'OutlineColour=' + ass_color(style.get('outline_color', '#000000')),
              'BorderStyle=1', f"Outline={int(style.get('outline_width', 2))}",
              f"Shadow={int(style.get('shadow', 1))}", f"Bold={-1 if style.get('bold') else 0}"]
    path = os.path.abspath(srt_path).replace('\\', '/')
    return 'subtitles=filename=' + _escape_filter_value(path) + ':force_style=' + _escape_filter_value(','.join(params))

def _video_graph(filters, zoom_p, overlay_file, overlay_pos, output_format,
                 blur_background, crop_filter, filler_path, split_content_height,
                 content_on_top, preview=False):
    parts = []
    node = '[0:v]'
    index = 0

    def add(expression):
        nonlocal node, index
        new = f'[v{index}]'
        index += 1
        parts.append(node + expression + new)
        node = new

    add('setpts=PTS-STARTPTS')
    if crop_filter:
        add(crop_filter)
    vertical = output_format == REELS_FORMAT_NAME
    if vertical:
        if filler_path:
            parts.append(build_split_screen_filter(node, '[1:v]', split_content_height, content_on_top))
        elif blur_background:
            parts.append(f'{node}split[original][copy];'
                         f'[copy]scale={REELS_WIDTH}:{REELS_HEIGHT}:force_original_aspect_ratio=increase,'
                         f'crop={REELS_WIDTH}:{REELS_HEIGHT},gblur=sigma=25,setsar=1[bg];'
                         f'[original]scale={REELS_WIDTH}:{REELS_HEIGHT}:force_original_aspect_ratio=decrease,'
                         f'setsar=1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2:shortest=1[formatted]')
        else:
            parts.append(f'{node}scale={REELS_WIDTH}:{REELS_HEIGHT}:force_original_aspect_ratio=decrease,'
                         f'pad={REELS_WIDTH}:{REELS_HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1[formatted]')
        node = '[formatted]'
    for name in filters:
        if name == 'Random filter':
            available = [v for k, v in FILTERS.items() if v and k not in ('Random filter', 'Random color')]
            template = FILTERS.get('Sepia') if preview else random.choice(available)
        elif name == 'Random color':
            template = FILTERS[name].format(br=0.1 if preview else random.uniform(-0.15, 0.15),
                                           ct=1.1 if preview else random.uniform(0.8, 1.2),
                                           sat=1.1 if preview else random.uniform(0.8, 1.3),
                                           hue=2 if preview else random.uniform(-5, 5))
        else:
            template = FILTERS.get(name)
        if template:
            add(template)
    zoom = zoom_p / 100.0
    if abs(zoom - 1) > 1e-6:
        parts.append(f'{node}split[zoom_ref][zoom_input];'
                     '[zoom_ref]drawbox=color=black:t=fill[zoom_canvas];'
                     f'[zoom_input]scale=max(2\\,trunc(iw*{zoom}/2)*2):'
                     f'max(2\\,trunc(ih*{zoom}/2)*2)[zoom_scaled];'
                     '[zoom_canvas][zoom_scaled]overlay=(W-w)/2:(H-h)/2:shortest=1[zoomed]')
        node = '[zoomed]'
    if vertical:
        add(f'scale={REELS_WIDTH}:{REELS_HEIGHT},setsar=1')
    if overlay_file:
        overlay_index = 2 if filler_path else 1
        parts.append(f'[{overlay_index}:v]format=rgba[overlay]')
        position = OVERLAY_POSITIONS.get(overlay_pos, 'x=(W-w)/2:y=(H-h)/2')
        new = f'[v{index}]'
        parts.append(f'{node}[overlay]overlay={position}:shortest=0:eof_action=repeat{new}')
        node = new
    return parts, node

def _validate_assets(overlay_file, filler_path, overlay_audio_path=None, srt_path=None):
    for name, path in [('Image overlay', overlay_file), ('Background clip', filler_path),
                       ('Audio overlay', overlay_audio_path), ('Subtitle file', srt_path)]:
        if path and not os.path.isfile(path):
            raise FileNotFoundError(f'{name} was not found: {path}')

def process_single(in_path, out_path, filters, zoom_p, speed_p, overlay_file,
                   overlay_pos, output_format, blur_background, mute_audio=False,
                   strip_metadata=False, codec='libx264', srt_path=None, subtitle_style=None,
                   crop_filter=None, overlay_audio_path=None, original_volume=1.0,
                   overlay_volume=1.0, filler_path=None, split_content_height=1080,
                   content_on_top=True, uniquify=False, uniquify_methods=None,
                   progress_callback=None, controller=None):
    if zoom_p <= 0 or speed_p <= 0:
        raise ValueError('Zoom and speed must be greater than zero.')
    if os.path.normcase(os.path.abspath(in_path)) == os.path.normcase(os.path.abspath(out_path)):
        raise ValueError('The output must not overwrite the input file.')
    if output_format != REELS_FORMAT_NAME:
        filler_path = None
    elif filler_path == RANDOM_FILLER:
        filler_path = pick_random_filler()
    _validate_assets(overlay_file, filler_path, overlay_audio_path, srt_path)
    info = probe_media(in_path, controller)
    if not any(s.get('codec_type') == 'video' for s in info.get('streams', [])):
        raise ValueError('The input does not contain a video stream.')
    duration = _media_duration(info)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError('Cannot determine a finite input duration.')
    has_audio = any(s.get('codec_type') == 'audio' for s in info['streams'])
    unique = build_uniquify_plan(in_path, uniquify_methods) if uniquify else None
    head, tail = (unique['head'], unique['tail']) if unique else (0, 0)
    if duration - head - tail < min(1.0, duration):
        head = tail = 0
    speed = speed_p / 100.0
    if unique and abs(speed - 1) < 1e-6:
        speed = unique['speed']
    output_duration = (duration - head - tail) / speed
    command = ['-y', '-i', in_path]
    for asset in (filler_path, overlay_file):
        if asset:
            if asset == filler_path or asset.lower().endswith('.gif'):
                command.extend(['-stream_loop', '-1'])
            command.extend(['-i', asset])
    audio_index = 1 + bool(filler_path) + bool(overlay_file)
    if overlay_audio_path:
        command.extend(['-i', overlay_audio_path])
    parts, node = _video_graph(filters, zoom_p, overlay_file, overlay_pos, output_format,
                               blur_background, crop_filter, filler_path,
                               split_content_height, content_on_top)
    # Burn captions on the source timeline, then apply identical trim/speed to A/V.
    if srt_path:
        parts.append(node + subtitle_filter(srt_path, subtitle_style) + '[captioned]')
        node = '[captioned]'
    parts.append(f'{node}trim=start={head}:end={duration-tail},'
                 f'setpts=(PTS-STARTPTS)/{speed},scale=trunc(iw/2)*2:trunc(ih/2)*2,'
                 'format=yuv420p[vout]')
    audio_nodes = []
    if has_audio and not mute_audio:
        parts.append(f'[0:a]atrim=start={head}:end={duration-tail},asetpts=PTS-STARTPTS,'
                     f'volume={original_volume}[a_original]')
        audio_nodes.append('[a_original]')
    if overlay_audio_path:
        parts.append(f'[{audio_index}:a]asetpts=PTS-STARTPTS,volume={overlay_volume}[a_music]')
        audio_nodes.append('[a_music]')
    if audio_nodes:
        if len(audio_nodes) > 1:
            parts.append(''.join(audio_nodes) + 'amix=inputs=2:duration=longest:normalize=0[a_mix]')
            audio_node = '[a_mix]'
        else:
            audio_node = audio_nodes[0]
        tempos = []
        tempo = speed
        while tempo > 2:
            tempos.append('atempo=2')
            tempo /= 2
        while tempo < 0.5:
            tempos.append('atempo=0.5')
            tempo /= 0.5
        tempos.append(f'atempo={tempo}')
        if unique and abs(unique['pitch'] - 1) > 1e-6:
            tempos.extend(['aresample=48000', f"asetrate={48000 * unique['pitch']}",
                           'aresample=48000', f"atempo={1 / unique['pitch']}"])
        parts.append(audio_node + ','.join(tempos) + ',apad[aout]')
    command.extend(['-filter_complex', ';'.join(parts), '-map', '[vout]'])
    if audio_nodes:
        command.extend(['-map', '[aout]', '-c:a', 'aac', '-b:a', '128k'])
    else:
        command.append('-an')
    quality = unique['crf'] if unique else 24
    command.extend(['-c:v', codec])
    if 'nvenc' in codec:
        command.extend(['-rc', 'vbr', '-cq', str(quality), '-b:v', '0'])
    elif 'amf' in codec:
        command.extend(['-rc', 'cqp', '-qp_i', str(quality), '-qp_p', str(quality)])
    elif 'qsv' in codec:
        command.extend(['-global_quality', str(quality)])
    else:
        command.extend(['-preset', 'veryfast', '-crf', str(quality)])
    if unique and unique['gop']:
        command.extend(['-g', str(unique['gop'])])
    if strip_metadata:
        command.extend(['-map_metadata', '-1', '-map_chapters', '-1'])
    command.extend(['-t', str(output_duration), '-movflags', '+faststart', out_path])
    run_ffmpeg(command, input_file_for_log=in_path, duration=output_duration,
               progress_callback=progress_callback, controller=controller)

def generate_preview(in_path, out_path, filters, zoom_p, overlay_file, overlay_pos,
                     output_format, blur_background, crop_filter=None, filler_path=None,
                     split_content_height=1080, content_on_top=True, controller=None,
                     auto_crop=False):
    if output_format != REELS_FORMAT_NAME:
        filler_path = None
    elif filler_path == RANDOM_FILLER:
        filler_path = pick_random_filler()
    _validate_assets(overlay_file, filler_path)
    if auto_crop:
        crop_filter = detect_crop_dimensions(in_path, controller)
    duration = get_video_duration(in_path)
    command = ['-y', '-ss', str(duration / 2), '-i', in_path]
    for asset in (filler_path, overlay_file):
        if asset:
            command.extend(['-i', asset])
    parts, node = _video_graph(filters, zoom_p, overlay_file, overlay_pos, output_format,
                               blur_background, crop_filter, filler_path,
                               split_content_height, content_on_top, preview=True)
    parts.append(node + 'format=rgba[vout]')
    command.extend(['-filter_complex', ';'.join(parts), '-map', '[vout]', '-frames:v', '1', out_path])
    run_ffmpeg(command, input_file_for_log=in_path, controller=controller)
