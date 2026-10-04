"""Bounded stderr collection for media subprocesses."""

from collections import deque
from subprocess import Popen
from threading import Thread
from typing import IO


class StderrTail:
    def __init__(self, stream: IO[bytes]) -> None:
        self.lines: deque[bytes] = deque(maxlen=40)
        self.thread = Thread(target=self._drain, args=(stream,), daemon=True)
        self.thread.start()

    def _drain(self, stream: IO[bytes]) -> None:
        while chunk := stream.readline(4096):
            self.lines.append(chunk)

    def text(self) -> str:
        self.thread.join(timeout=5)
        return b"".join(self.lines).decode(errors="replace")[-4000:]


def stop(process: Popen[bytes]) -> None:
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)
    for stream in (process.stdout, process.stdin, process.stderr):
        if stream is not None:
            try:
                stream.close()
            except (BrokenPipeError, OSError):
                pass  # Process is already reaped; a broken output pipe is expected on failure.
