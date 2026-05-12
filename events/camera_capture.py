import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = PROJECT_ROOT / "data" / "snapshots"


def capture_snapshot(event_type: str) -> str:
    """Save a JPEG to data/snapshots/. Grabs a frame from the live stream when
    the camera_manager is running; falls back to a single-shot capture otherwise.
    Returns the saved file path, or '' on failure."""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = SNAPSHOT_DIR / f"{event_type}_{ts}.jpg"

    from events import camera_manager
    if camera_manager.capture_to_file(str(path)):
        print(f"[camera] snapshot saved from stream: {path.name}")
        return str(path)

    # Fallback: open camera independently (used when streaming hasn't started yet)
    try:
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.configure(cam.create_still_configuration(main={"size": (1280, 720)}))
        cam.start()
        time.sleep(1)
        cam.capture_file(str(path))
        cam.stop()
        print(f"[camera] snapshot saved (single-shot): {path.name}")
        return str(path)
    except Exception as exc:
        print(f"[camera] capture failed: {exc}")
        return ""
