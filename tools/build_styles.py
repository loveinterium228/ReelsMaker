'Generate the dark and light QSS styles from shared design tokens. Run python tools/build_styles.py.'
import os

DARK = {
    'bg': '#141519',
    'surface': '#1b1d21',
    'surface_alt': '#1c1e23',
    'raised': '#24272e',
    'raised_alt': '#2b2f37',
    'hover': '#2d313a',
    'border': '#3a3f49',
    'border_strong': '#4c525d',
    'text': '#e9ebee',
    'text_secondary': '#aab0ba',
    'text_muted': '#868c96',
    'accent': '#4ecdc4',
    'accent_deep': '#0d7c72',
    'accent_mid': '#0f8378',
    'accent_bg': '#12302c',
    'danger': '#ff6b6b',
    'disabled_text': '#565b63',
}

LIGHT = {
    'bg': '#f4f5f7',
    'surface': '#ffffff',
    'surface_alt': '#fafbfc',
    'raised': '#ffffff',
    'raised_alt': '#eef0f3',
    'hover': '#e6e9ed',
    'border': '#d5d9e0',
    'border_strong': '#b6bcc6',
    'text': '#1b1d21',
    'text_secondary': '#4c525d',
    'text_muted': '#7c828b',
    'accent': '#0f8378',
    'accent_deep': '#0d7c72',
    'accent_mid': '#4ecdc4',
    'accent_bg': '#e2f5f2',
    'danger': '#d64545',
    'disabled_text': '#aab0ba',
}

TEMPLATE = '\n\nQMainWindow, QDialog {{\n    background-color: {bg};\n}}\nQWidget {{\n    color: {text};\n    font-family: "Segoe UI", system-ui, sans-serif;\n    font-size: 13px;\n}}\nQLabel {{\n    background: transparent;\n    color: {text};\n}}\nQLabel#app_title {{\n    font-size: 17px;\n    font-weight: 600;\n    color: {text};\n}}\nQLabel#status_label {{\n    color: {text_secondary};\n}}\nQLabel#dnd_label {{\n    color: {text_muted};\n    border: 1px dashed {border_strong};\n    border-radius: 10px;\n    padding: 18px;\n}}\nQLabel#previewLabel {{\n    background-color: {surface_alt};\n    border: 1px solid {border};\n    border-radius: 10px;\n    color: {text_muted};\n}}\nQLabel[text*="<a"] {{\n    color: {accent};\n}}\nQFrame#header_bar {{\n    background-color: {surface};\n    border-bottom: 1px solid {border};\n}}\n\nQTabWidget::pane {{\n    background-color: {surface};\n    border: 1px solid {border};\n    border-radius: 10px;\n    top: -1px;\n}}\nQTabBar {{\n    background: transparent;\n}}\nQTabBar::tab {{\n    background: transparent;\n    color: {text_secondary};\n    padding: 8px 16px;\n    margin-right: 6px;\n    border: 1px solid transparent;\n    border-top-left-radius: 8px;\n    border-top-right-radius: 8px;\n    font-weight: 600;\n}}\nQTabBar::tab:hover {{\n    background-color: {hover};\n    color: {text};\n}}\nQTabBar::tab:selected {{\n    background-color: {surface};\n    color: {accent};\n    border: 1px solid {border};\n    border-bottom-color: {surface};\n}}\n\nQGroupBox {{\n    background-color: {surface};\n    border: 1px solid {border};\n    border-radius: 10px;\n    margin-top: 14px;\n    padding: 16px 12px 12px;\n    font-weight: 600;\n}}\nQGroupBox::title {{\n    subcontrol-origin: margin;\n    left: 12px;\n    padding: 0 6px;\n    color: {accent};\n}}\n\nQPushButton {{\n    background-color: {raised};\n    color: {text};\n    border: 1px solid {border};\n    border-radius: 8px;\n    padding: 7px 16px;\n    min-height: 18px;\n}}\nQPushButton:hover {{\n    background-color: {hover};\n    border-color: {border_strong};\n}}\nQPushButton:pressed {{\n    background-color: {raised_alt};\n}}\nQPushButton:disabled {{\n    background-color: {surface_alt};\n    border-color: {border};\n    color: {disabled_text};\n}}\nQPushButton#process_button, QPushButton#ok_button {{\n    background-color: {accent_deep};\n    border: 1px solid {accent_mid};\n    color: #ffffff;\n    font-weight: 600;\n    padding: 9px 22px;\n}}\nQPushButton#process_button:hover, QPushButton#ok_button:hover {{\n    background-color: {accent_mid};\n}}\nQPushButton#process_button:pressed {{\n    background-color: {accent_deep};\n}}\nQPushButton#process_button:disabled {{\n    background-color: {surface_alt};\n    border-color: {border};\n    color: {disabled_text};\n}}\nQPushButton#settings_btn {{\n    background: transparent;\n    border: none;\n    padding: 6px;\n    border-radius: 8px;\n}}\nQPushButton#settings_btn:hover {{\n    background-color: {hover};\n}}\n\nQLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{\n    background-color: {surface_alt};\n    color: {text};\n    border: 1px solid {border};\n    border-radius: 6px;\n    padding: 6px 10px;\n    \n    min-height: 20px;\n    selection-background-color: {accent_deep};\n    selection-color: #ffffff;\n}}\nQLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{\n    border-color: {border_strong};\n}}\nQLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,\nQComboBox:focus, QPlainTextEdit:focus {{\n    border-color: {accent};\n}}\nQLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{\n    background-color: {surface};\n    color: {disabled_text};\n}}\nQComboBox::drop-down {{\n    border: none;\n    width: 22px;\n}}\nQComboBox QAbstractItemView {{\n    background-color: {raised};\n    color: {text};\n    border: 1px solid {border};\n    border-radius: 8px;\n    selection-background-color: {accent_bg};\n    selection-color: {text};\n    outline: none;\n}}\nQSpinBox::up-button, QSpinBox::down-button,\nQDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{\n    background-color: {raised};\n    border: none;\n    width: 16px;\n}}\n\nQCheckBox, QRadioButton {{\n    background: transparent;\n    color: {text};\n    spacing: 8px;\n}}\nQCheckBox::indicator, QRadioButton::indicator {{\n    width: 16px;\n    height: 16px;\n    border: 1px solid {border_strong};\n    background-color: {surface_alt};\n}}\nQCheckBox::indicator {{\n    border-radius: 4px;\n}}\nQRadioButton::indicator {{\n    border-radius: 8px;\n}}\nQCheckBox::indicator:hover, QRadioButton::indicator:hover {{\n    border-color: {accent};\n}}\nQCheckBox::indicator:checked, QRadioButton::indicator:checked {{\n    background-color: {accent_deep};\n    border-color: {accent};\n}}\nQCheckBox::indicator:disabled {{\n    background-color: {surface};\n    border-color: {border};\n}}\n\nQGroupBox::indicator {{\n    width: 15px;\n    height: 15px;\n    border: 1px solid {border_strong};\n    border-radius: 4px;\n    background-color: {surface_alt};\n}}\nQGroupBox::indicator:hover {{\n    border-color: {accent};\n}}\nQGroupBox::indicator:checked {{\n    background-color: {accent_deep};\n    border-color: {accent};\n}}\n\n\nQListWidget::indicator {{\n    width: 15px;\n    height: 15px;\n    border: 1px solid {border_strong};\n    border-radius: 4px;\n    background-color: {surface_alt};\n}}\nQListWidget::indicator:hover {{\n    border-color: {accent};\n}}\nQListWidget::indicator:checked {{\n    background-color: {accent_deep};\n    border-color: {accent};\n}}\n\nQCheckBox::indicator:checked:disabled,\nQRadioButton::indicator:checked:disabled {{\n    background-color: {accent_bg};\n    border-color: {border_strong};\n}}\n\nQListWidget {{\n    background-color: {surface_alt};\n    color: {text};\n    border: 1px solid {border};\n    border-radius: 8px;\n    padding: 4px;\n    outline: none;\n}}\nQListWidget::item {{\n    padding: 7px 10px;\n    border-radius: 6px;\n}}\nQListWidget::item:hover {{\n    background-color: {hover};\n}}\nQListWidget::item:selected {{\n    background-color: {accent_bg};\n    color: {text};\n}}\n\nQProgressBar {{\n    background-color: {surface};\n    border: 1px solid {border};\n    border-radius: 7px;\n    height: 14px;\n    text-align: center;\n    color: {text_secondary};\n    font-size: 11px;\n}}\nQProgressBar::chunk {{\n    background-color: {accent_deep};\n    border-radius: 6px;\n}}\n\nQSlider::groove:horizontal {{\n    background-color: {surface_alt};\n    border: 1px solid {border};\n    height: 5px;\n    border-radius: 3px;\n}}\nQSlider::handle:horizontal {{\n    background-color: {accent};\n    border: none;\n    width: 15px;\n    height: 15px;\n    margin: -6px 0;\n    border-radius: 7px;\n}}\nQSlider::handle:horizontal:hover {{\n    background-color: {accent_mid};\n}}\nQSlider::handle:horizontal:disabled {{\n    background-color: {border_strong};\n}}\n\nQSplitter::handle {{\n    background-color: {border};\n}}\nQSplitter::handle:hover {{\n    background-color: {accent_deep};\n}}\n\n\nQScrollArea {{\n    background-color: {surface};\n    border: none;\n}}\nQScrollArea > QWidget > QWidget {{\n    background-color: {surface};\n}}\nQScrollBar:vertical {{\n    background: transparent;\n    width: 11px;\n    margin: 0;\n}}\nQScrollBar::handle:vertical {{\n    background-color: {border};\n    border-radius: 5px;\n    min-height: 28px;\n}}\nQScrollBar::handle:vertical:hover {{\n    background-color: {border_strong};\n}}\nQScrollBar:horizontal {{\n    background: transparent;\n    height: 11px;\n    margin: 0;\n}}\nQScrollBar::handle:horizontal {{\n    background-color: {border};\n    border-radius: 5px;\n    min-width: 28px;\n}}\nQScrollBar::handle:horizontal:hover {{\n    background-color: {border_strong};\n}}\nQScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,\nQScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{\n    height: 0;\n    width: 0;\n}}\nQScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,\nQScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{\n    background: transparent;\n}}\n\nQMenu {{\n    background-color: {raised};\n    color: {text};\n    border: 1px solid {border};\n    border-radius: 8px;\n    padding: 4px;\n}}\nQMenu::item {{\n    padding: 7px 18px;\n    border-radius: 6px;\n}}\nQMenu::item:selected {{\n    background-color: {accent_bg};\n}}\nQMessageBox {{\n    background-color: {surface};\n}}\nQMessageBox QLabel {{\n    color: {text};\n    background: transparent;\n}}\nQToolTip {{\n    background-color: {raised};\n    color: {text};\n    border: 1px solid {border_strong};\n    border-radius: 6px;\n    padding: 6px 8px;\n}}\n'

if __name__ == '__main__':
    resources = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
    for name, palette in (('styles_dark.qss', DARK), ('styles_light.qss', LIGHT)):
        path = os.path.join(resources, name)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(TEMPLATE.format(**palette))
        print(f'wrote {name}')
