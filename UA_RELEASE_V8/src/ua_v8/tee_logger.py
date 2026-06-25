"""
UA Test v8.0 — Real-time tee logger (stdout + file).
"""
import sys


class TeeLogger:
    """Duplicate stdout to a log file in real time."""

    def __init__(self, log_path):
        self._log = open(log_path, "w", encoding="utf-8", buffering=1)
        self._stdout = sys.__stdout__

    def write(self, msg):
        self._stdout.write(msg)
        self._stdout.flush()
        self._log.write(msg)
        self._log.flush()

    def flush(self):
        self._stdout.flush()
        self._log.flush()

    def fileno(self):
        return self._stdout.fileno()
