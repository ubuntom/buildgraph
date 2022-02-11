import sys
from contextlib import contextmanager


class TabulatedWriter:
    """Overrides a binary writer to insert 2 space before each line."""

    def __init__(self, parent, writer_name):
        self.parent = parent
        self.writer_name = writer_name
        self.blank = True

        self.writer = getattr(parent, writer_name)
        setattr(parent, writer_name, self.write)

    def write(self, data):
        if self.blank:
            self.blank = False
            self.writer(b"  ")

        lines = data.split(b"\n")
        if lines[-1] == b"":
            lines.pop()
            self.blank = True

        self.writer(b"\n  ".join(lines) + b"\n")

    def shutdown(self):
        setattr(self.parent, self.writer_name, self.writer)
        if not self.blank:
            self.writer(b"\n")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.shutdown()


@contextmanager
def tabbuffer(
    enable=True,
):  # Some steps may choose to be untabulated, so this can be disabled
    if not enable:
        yield
        return
    with TabulatedWriter(sys.stderr.buffer, "write"):
        with TabulatedWriter(sys.stdout.buffer, "write"):
            yield
