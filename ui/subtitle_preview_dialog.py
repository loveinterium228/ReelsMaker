import os
import tempfile
import uuid
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QSpinBox, QGroupBox, QColorDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QColor
from utils.constants import SUBTITLE_PRESETS
from utils.ffmpeg_utils import run_ffmpeg, get_video_duration, subtitle_filter
from utils.process_utils import ProcessController

class SubtitlePreviewGenerator(QThread):
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, video_path, srt_path, style_params, temp_output):
        super().__init__()
        self.video_path = video_path
        self.srt_path = srt_path
        self.style_params = dict(style_params)
        self.temp_output = temp_output
        self.controller = ProcessController()

    def stop(self):
        self.controller.cancel()

    def run(self):
        try:
            duration = get_video_duration(self.video_path)
            mid_point = duration / 2 if duration > 0 else 0

            cmd = [
                "-y",
                "-i", self.video_path,
                "-vf", subtitle_filter(self.srt_path, self.style_params),
                "-ss", str(mid_point),
                "-vframes", "1",
                self.temp_output
            ]

            run_ffmpeg(cmd, self.video_path, controller=self.controller)
            self.finished_signal.emit(self.temp_output)

        except Exception as e:
            self.error_signal.emit(str(e))

class SubtitlePreviewDialog(QDialog):
    def __init__(self, video_path, srt_path, parent=None, style=None):
        super().__init__(parent)
        self.video_path = video_path
        self.srt_path = srt_path
        self.temp_files = []
        self.preview_thread = None
        self.current_style = dict(SUBTITLE_PRESETS['Classic'], **(style or {}))

        self.setWindowTitle('Subtitle preview')
        self.setMinimumSize(900, 700)
        self.init_ui()
        self.update_preview()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(400)
        self.preview_label.setStyleSheet("border: 2px solid #7b2cbf; border-radius: 8px;")
        layout.addWidget(self.preview_label)

        controls_group = QGroupBox('Style settings')
        controls_layout = QVBoxLayout(controls_group)

        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel('Preset:'))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(SUBTITLE_PRESETS.keys())
        self.preset_combo.currentTextChanged.connect(self.on_preset_changed)
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        controls_layout.addLayout(preset_layout)

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel('Font:'))
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Arial", "Arial Black", "Impact", "Calibri", "Roboto", "Times New Roman", "Verdana"])
        self.font_combo.setCurrentText(self.current_style['font'])
        self.font_combo.currentTextChanged.connect(self.on_style_changed)
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()
        controls_layout.addLayout(font_layout)

        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel('Size:'))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(20, 80)
        self.size_spin.setValue(self.current_style['size'])
        self.size_spin.valueChanged.connect(self.on_style_changed)
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()
        controls_layout.addLayout(size_layout)

        color_layout = QHBoxLayout()
        self.color_btn = QPushButton('Text color')
        self.color_btn.clicked.connect(lambda: self.pick_color('color'))
        self.outline_color_btn = QPushButton('Outline color')
        self.outline_color_btn.clicked.connect(lambda: self.pick_color('outline_color'))
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.outline_color_btn)
        color_layout.addStretch()
        controls_layout.addLayout(color_layout)

        outline_layout = QHBoxLayout()
        outline_layout.addWidget(QLabel('Outline width:'))
        self.outline_spin = QSpinBox()
        self.outline_spin.setRange(0, 5)
        self.outline_spin.setValue(self.current_style['outline_width'])
        self.outline_spin.valueChanged.connect(self.on_style_changed)
        outline_layout.addWidget(self.outline_spin)
        outline_layout.addStretch()
        controls_layout.addLayout(outline_layout)

        position_layout = QHBoxLayout()
        position_layout.addWidget(QLabel('Position:'))
        self.position_combo = QComboBox()
        self.position_combo.addItems([
            "Bottom left (1)", "Bottom center (2)", "Bottom right (3)",
            'Middle left (4)', 'Middle center (5)', 'Middle right (6)',
            "Top left (7)", "Top center (8)", "Top right (9)"
        ])
        self.position_combo.setCurrentIndex(self.current_style['position'] - 1)
        self.position_combo.currentIndexChanged.connect(self.on_style_changed)
        position_layout.addWidget(self.position_combo)
        position_layout.addStretch()
        controls_layout.addLayout(position_layout)

        layout.addWidget(controls_group)

        buttons_layout = QHBoxLayout()
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self.update_preview)
        apply_btn = QPushButton('Apply')
        apply_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def on_preset_changed(self, preset_name):
        if preset_name in SUBTITLE_PRESETS:
            self.current_style = SUBTITLE_PRESETS[preset_name].copy()
            controls = (self.font_combo, self.size_spin, self.outline_spin, self.position_combo)
            for control in controls:
                control.blockSignals(True)
            self.font_combo.setCurrentText(self.current_style['font'])
            self.size_spin.setValue(self.current_style['size'])
            self.outline_spin.setValue(self.current_style['outline_width'])
            self.position_combo.setCurrentIndex(self.current_style['position'] - 1)
            for control in controls:
                control.blockSignals(False)
            self.update_preview()

    def on_style_changed(self):
        self.current_style['font'] = self.font_combo.currentText()
        self.current_style['size'] = self.size_spin.value()
        self.current_style['outline_width'] = self.outline_spin.value()
        self.current_style['position'] = self.position_combo.currentIndex() + 1

    def pick_color(self, color_type):
        current_color = QColor(self.current_style.get(color_type, '#FFFFFF'))
        color = QColorDialog.getColor(current_color, self, "Choose a color")
        if color.isValid():
            self.current_style[color_type] = color.name()
            self.update_preview()

    def update_preview(self):
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
            if not self.preview_thread.wait(4000):
                return
        temp_output = os.path.join(tempfile.gettempdir(), f"sub_preview_{uuid.uuid4()}.png")
        self.temp_files.append(temp_output)

        self.preview_label.setText('Generating preview...')
        self.preview_thread = SubtitlePreviewGenerator(
            self.video_path, self.srt_path, self.current_style, temp_output
        )
        self.preview_thread.finished_signal.connect(self.on_preview_ready)
        self.preview_thread.error_signal.connect(self.on_preview_error)
        self.preview_thread.start()

    def on_preview_ready(self, image_path):
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.preview_label.setPixmap(
                pixmap.scaled(self.preview_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.preview_label.setText('Could not load preview')

    def on_preview_error(self, error_msg):
        self.preview_label.setText(f"Error: {error_msg}")

    def get_style(self):
        return self.current_style

    def done(self, result):
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
            if not self.preview_thread.wait(4000):
                return
        for path in self.temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        self.temp_files.clear()
        super().done(result)

    def closeEvent(self, event):
        self.done(QDialog.Rejected)
        if self.preview_thread and self.preview_thread.isRunning():
            event.ignore()
        else:
            event.accept()
