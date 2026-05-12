from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class MediaService:
    def __init__(self, media_dir: Path, camera_enabled: bool = True, mock_fallback: bool = True, resolution: tuple[int, int] = (1280, 720), fake_hardware: bool = False):
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.camera_enabled = camera_enabled
        self.mock_fallback = mock_fallback
        self.resolution = resolution
        self.fake_hardware = fake_hardware
        self._camera = None

    def capture_snapshot(self, prefix: str = "capture") -> Path:
        if self.fake_hardware or not self.camera_enabled:
            return self.create_mock_snapshot(prefix)
        try:
            return self._capture_picamera2(prefix)
        except Exception:
            if self.mock_fallback:
                return self.create_mock_snapshot(prefix)
            raise

    def _capture_picamera2(self, prefix: str) -> Path:
        from picamera2 import Picamera2
        import time

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        path = self.media_dir / f"{prefix}_{timestamp}.jpg"
        if self._camera is None:
            self._camera = Picamera2()
            self._camera.configure(
                self._camera.create_still_configuration(
                    main={"size": self.resolution}
                )
            )
            self._camera.start()
            time.sleep(1.5)
        self._camera.capture_file(str(path))
        return path

    def create_mock_snapshot(self, prefix: str = "capture") -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        path = self.media_dir / f"{prefix}_{timestamp}.svg"
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">'
            '<rect width="100%" height="100%" fill="#0f1d24"/>'
            '<text x="32" y="96" fill="#e8ffff" font-size="28">Smart Home Snapshot</text>'
            f'<text x="32" y="152" fill="#7fe7db" font-size="22">{prefix}</text>'
            f'<text x="32" y="208" fill="#8baeb1" font-size="18">{timestamp}</text>'
            '</svg>'
        )
        path.write_text(svg, encoding="utf-8")
        return path
