"""Cancellation and subprocess lifetime management shared by media workers."""
import os
import subprocess
import threading

class ProcessingCancelled(Exception):
    """Raised when the user cancels a media job."""

class ProcessController:
    def __init__(self):
        self._cancelled = threading.Event()
        self._lock = threading.Lock()
        self._process = None

    def check(self):
        if self._cancelled.is_set():
            raise ProcessingCancelled('Processing cancelled.')

    def attach(self, process):
        with self._lock:
            self._process = process
            if self._cancelled.is_set() and process.poll() is None:
                process.terminate()

    def detach(self, process):
        with self._lock:
            if self._process is process:
                self._process = None

    def cancel(self):
        self._cancelled.set()
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                try:
                    self._process.terminate()
                except ProcessLookupError:
                    pass

def hidden_process_options():
    return {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}

def finish_process(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

def run_capture(command, timeout=30, controller=None):
    if controller:
        controller.check()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, text=True, encoding='utf-8',
                               errors='replace', **hidden_process_options())
    if controller:
        controller.attach(process)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        if controller:
            controller.check()
        return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    finally:
        finish_process(process)
        if controller:
            controller.detach(process)
        process.stdout.close()
        process.stderr.close()
