import threading
import time

import pytest
from utils import ffmpeg_utils as ff


def test_active_encoder_can_be_cancelled(tmp_path):
    from utils.process_utils import ProcessController, ProcessingCancelled
    controller = ProcessController()
    timer = threading.Timer(0.5, controller.cancel)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(ProcessingCancelled):
            ff.run_ffmpeg(['-re', '-f', 'lavfi', '-i', 'color=s=160x90:d=30',
                           '-f', 'null', '-'], controller=controller)
        assert time.monotonic() - started < 5
    finally:
        timer.cancel()
