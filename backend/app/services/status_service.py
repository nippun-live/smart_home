from __future__ import annotations

import shutil
import socket
import time
from datetime import datetime, timezone
from pathlib import Path


class StatusService:
    def __init__(self, root_path: Path):
        self.root_path = Path(root_path)
        self._boot_time = time.time()

    def read_status(self) -> dict[str, object]:
        usage = shutil.disk_usage(self.root_path)
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "online",
            "ip_address": self._ip_address(),
            "disk_free_gb": round(usage.free / (1024 ** 3), 1),
            "cpu_temp_c": self._cpu_temp(),
            "uptime_seconds": int(time.time() - self._boot_time),
        }

    def _ip_address(self) -> str:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return "127.0.0.1"

    def _cpu_temp(self) -> float | None:
        cpu_file = Path("/sys/class/thermal/thermal_zone0/temp")
        if not cpu_file.exists():
            return None
        try:
            return round(float(cpu_file.read_text().strip()) / 1000.0, 1)
        except (ValueError, OSError):
            return None
