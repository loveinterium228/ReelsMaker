from pathlib import Path

from workers.worker import Worker
from utils.constants import RANDOM_FILLER, REELS_FORMAT_NAME


def make_worker(files, out_dir, **extra):
    params = dict(files=[str(p) for p in files], filters=[], zoom_mode='static',
                  zoom_static=100, zoom_min=100, zoom_max=100, speed_mode='static',
                  speed_static=100, speed_min=100, speed_max=100, overlay_file=None,
                  overlay_pos='Middle center', out_dir=str(out_dir), mute_audio=True,
                  output_format='Original', blur_background=False, strip_metadata=True,
                  codec='libx264', subtitle_settings={'mode': 'none'}, auto_crop=False,
                  overlay_audio=None, original_volume=100, overlay_volume=100)
    params.update(extra)
    return Worker(**params)


def test_batch_exports_and_preserves_existing_output(media, tmp_path):
    output_dir = tmp_path / 'exports'
    output_dir.mkdir()
    existing = output_dir / 'silent_processed.mp4'
    existing.write_bytes(b'keep this existing file')
    worker = make_worker([media[0]], output_dir)
    errors = []
    worker.error.connect(errors.append)
    worker.run()
    assert not errors, errors
    assert len(worker.output_paths) == 1
    assert existing.read_bytes() == b'keep this existing file'
    assert Path(worker.output_paths[0]).is_file()


def test_random_filler_can_export(media, tmp_path):
    worker = make_worker([media[0]], tmp_path / 'exports', filler_path=RANDOM_FILLER,
                         output_format=REELS_FORMAT_NAME)
    errors = []
    worker.error.connect(errors.append)
    worker.run()
    assert not errors, errors
    assert len(worker.output_paths) == 1


def test_original_batch_ignores_unneeded_background_library(media, tmp_path, monkeypatch):
    def empty_library():
        raise FileNotFoundError('Empty library')
    monkeypatch.setattr('workers.worker.pick_random_filler', empty_library)
    worker = make_worker([media[0]], tmp_path / 'exports', filler_path=RANDOM_FILLER)
    worker.run()
    assert not worker.errors
    assert len(worker.output_paths) == 1


def test_batch_continues_after_failure_without_leaving_partial_files(media, tmp_path):
    exports = tmp_path / 'exports'
    worker = make_worker([tmp_path / 'missing.mp4', media[0]], exports)
    progress = []
    worker.progress.connect(lambda done, total: progress.append((done, total)))
    worker.run()
    assert len(worker.errors) == 1
    assert len(worker.output_paths) == 1
    assert progress == [(1, 2), (2, 2)]
    assert list(exports.iterdir()) == [Path(worker.output_paths[0])]


def test_two_inputs_with_the_same_name_get_distinct_outputs(media, tmp_path):
    import shutil
    other = tmp_path / 'other' / media[0].name
    other.parent.mkdir()
    shutil.copyfile(media[0], other)
    worker = make_worker([media[0], other], tmp_path / 'exports')
    worker.run()
    assert not worker.errors
    assert len(set(worker.output_paths)) == 2
    assert all(Path(path).stat().st_size > 0 for path in worker.output_paths)


def test_error_does_not_release_running_worker(app, monkeypatch):
    from ui.main_window import VideoUnicApp
    from PyQt5.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'critical', lambda *args: None)
    window = VideoUnicApp()
    widget = window.processing_widget
    worker = make_worker([], '.')
    widget.processing_thread = worker
    widget.set_controls_enabled(False)
    widget.on_err('Test failure')
    assert widget.processing_thread is worker
    assert not widget.process_button.isEnabled()
    widget.processing_thread = None
    widget.codec_probe.wait()
    window.close()


def test_filter_checkbox_click_toggles_once(app, monkeypatch):
    from ui.main_window import VideoUnicApp
    from PyQt5.QtCore import Qt, QPoint
    from PyQt5.QtTest import QTest
    from PyQt5.QtWidgets import QTabWidget
    window = VideoUnicApp()
    widget = window.processing_widget
    window.show()
    widget.findChild(QTabWidget).setCurrentIndex(1)
    app.processEvents()
    # Test the actual checkbox hit target, not only the item text.
    widget.filter_group.show()
    widget.filter_list.show()
    item = widget.filter_list.item(1)
    rect = widget.filter_list.visualItemRect(item)
    try:
        QTest.mouseClick(widget.filter_list.viewport(), Qt.LeftButton, pos=QPoint(rect.left() + 18, rect.center().y()))
        assert item.checkState() == Qt.Checked
        QTest.mouseClick(widget.filter_list.viewport(), Qt.LeftButton, pos=QPoint(rect.left() + 80, rect.center().y()))
        assert item.checkState() == Qt.Unchecked
    finally:
        widget.codec_probe.stop()
        widget.codec_probe.wait()
        window.close()
