import json
from pathlib import Path
from datetime import datetime
from typing import Any

BASE_DIR = Path("data")
CONFIG_DIR = BASE_DIR / "configs"
SESSION_DIR = BASE_DIR / "sessions"
REPORT_DIR = BASE_DIR / "reports"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def new_id(prefix: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{stamp}"


def save_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return str(path)


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def config_path(room_name: str) -> Path:
    return CONFIG_DIR / f"{room_name}.json"


def session_path(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.json"


def report_path(session_id: str) -> Path:
    return REPORT_DIR / f"{session_id}.json"