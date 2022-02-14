import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class DurationTimer:
    start: float = None
    end: float = None
    seconds: float = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.end = time.time()
        self.seconds = self.end - self.start

    def format(self):
        return format_time(self.seconds)


def format_time(seconds):
    """Returns a short string human readable duration (5 chars)

    Args:
        seconds (float)
    """

    if seconds < 1:
        return f"{seconds:.3f}s"[1:]  # e.g. .652s

    if seconds < 10:
        return f"{seconds:.2f}s"  # e.g. 5.21s

    if seconds < 100:
        return f"{seconds:.1f}s"  # e.g. 85.2s

    if seconds < 180:
        return f"{seconds:4.0f}s"  # e.g.  152s

    minutes = seconds // 60
    seconds = seconds % 60

    if minutes < 100:
        return f"{minutes:2.0f}m{seconds:02.0f}"

    return f"{minutes:4.0f}m"
