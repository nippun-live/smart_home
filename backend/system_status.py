import socket
import time
from pathlib import Path

import psutil

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def get_status() -> dict:
    disk_free_gb = None
    cpu_temp_c = None
    uptime_seconds = None
    ip_address = "unavailable"

    try:
        stat = psutil.disk_usage(str(DATA_DIR))
        disk_free_gb = round(stat.free / (1024 ** 3), 1)
    except Exception:
        pass

    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
    except Exception:
        pass

    try:
        temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
        cpu_temp_c = round(int(temp_path.read_text().strip()) / 1000, 1)
    except Exception:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip_address = sock.getsockname()[0]
    except Exception:
        pass

    return {
        "status": "online",
        "ip_address": ip_address,
        "disk_free_gb": disk_free_gb,
        "cpu_temp_c": cpu_temp_c,
        "uptime_seconds": uptime_seconds,
    }
