from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class MediaService:
    def __init__(self, media_dir: Path):
        self.media_dir = Path(media_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def create_mock_snapshot(self, prefix: str = "capture") -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        path = self.media_dir / f"{prefix}_{timestamp}.svg"
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360">'
            '<rect width="100%" height="100%" fill="#0f1d24"/>'
            '<text x="32" y="96" fill="#e8ffff" font-size="28">Smart Home Mock Snapshot</text>'
            f'<text x="32" y="152" fill="#7fe7db" font-size="22">{prefix}</text>'
            f'<text x="32" y="208" fill="#8baeb1" font-size="18">{timestamp}</text>'
            '</svg>'
        )
        path.write_text(svg, encoding="utf-8")
        return path
