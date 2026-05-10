"""
Manages a persistent Picamera2 instance for MJPEG streaming.
- start()               called once at server startup
- stop()                called on shutdown
- get_frame()           returns the latest JPEG bytes (used by capture_snapshot)
- stream_generator()    yields MJPEG boundary chunks for StreamingResponse
"""

import io
import threading
from pathlib import Path

_output: "_FrameBuffer | None" = None
_cam = None
_lock = threading.Lock()


class _FrameBuffer(io.BufferedIOBase):
    """Receives encoded JPEG frames from picamera2's MJPEG encoder."""

    def __init__(self) -> None:
        self.frame: bytes | None = None
        self.condition = threading.Condition()

    def write(self, buf: bytes) -> int:
        with self.condition:
            self.frame = bytes(buf)
            self.condition.notify_all()
        return len(buf)


def start() -> bool:
    """Initialize and start the streaming camera. Returns True on success."""
    global _output, _cam
    with _lock:
        if _cam is not None:
            return True
        try:
            from picamera2 import Picamera2
            from picamera2.encoders import MJPEGEncoder
            from picamera2.outputs import FileOutput

            buf = _FrameBuffer()
            cam = Picamera2()
            cam.configure(cam.create_video_configuration(main={"size": (1280, 720)}))
            cam.start_recording(MJPEGEncoder(), FileOutput(buf))
            _output = buf
            _cam = cam
            print("[camera] streaming started — 1280×720 MJPEG")
            return True
        except Exception as exc:
            print(f"[camera] streaming start failed: {exc}")
            return False


def stop() -> None:
    global _cam, _output
    with _lock:
        if _cam is not None:
            try:
                _cam.stop_recording()
                _cam.close()
            except Exception:
                pass
            _cam = None
            _output = None


def get_frame(timeout: float = 2.0) -> bytes | None:
    """Return the latest JPEG frame, waiting up to *timeout* seconds."""
    if _output is None:
        return None
    with _output.condition:
        if not _output.condition.wait(timeout=timeout):
            return None
        return _output.frame


def capture_to_file(path: str) -> bool:
    """Grab the current stream frame and write it to *path*. Returns True on success."""
    frame = get_frame()
    if frame is None:
        return False
    try:
        Path(path).write_bytes(frame)
        return True
    except Exception as exc:
        print(f"[camera] capture_to_file failed: {exc}")
        return False


def stream_generator():
    """Yield MJPEG boundary chunks — pass directly to FastAPI StreamingResponse."""
    if _output is None:
        return
    while True:
        frame = get_frame()
        if frame is None:
            break
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
