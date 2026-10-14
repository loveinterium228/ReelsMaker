from PyQt5.QtGui import QImage
from utils import ffmpeg_utils as ff
from ui.subtitle_preview_dialog import SubtitlePreviewGenerator


def test_subtitle_preview_uses_the_selected_frame_timestamp(tmp_path):
    source = tmp_path / 'black.mp4'
    ff.run_ffmpeg(['-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x180:r=10:d=3',
                  '-c:v', 'libx264', str(source)])
    srt = tmp_path / 'middle.srt'
    srt.write_text('1\n00:00:01,200 --> 00:00:01,800\nVISIBLE CAPTION\n')
    output = tmp_path / 'preview.png'
    generator = SubtitlePreviewGenerator(str(source), str(srt), {'size': 24}, str(output))
    errors = []
    generator.error_signal.connect(errors.append)
    generator.run()
    assert not errors
    image = QImage(str(output))
    whites = sum(image.pixelColor(x, y).red() > 220 for y in range(image.height())
                 for x in range(image.width()))
    assert whites > 20, 'The preview should show the caption active at the video midpoint.'
