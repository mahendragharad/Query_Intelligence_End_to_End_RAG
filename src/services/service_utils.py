from pathlib import Path
from typing import Optional

BASE_DIR = Path.cwd().resolve()
DEFAULT_UPLOAD_DIR = BASE_DIR / "config" / "data" / "uploads"
DEFAULT_VECTOR_DIR = BASE_DIR / "config" / "data" / "vector_db"


def ensure_storage_directories(upload_dir: Optional[Path] = None, vector_dir: Optional[Path] = None) -> tuple[Path, Path]:
    upload_dir = upload_dir or DEFAULT_UPLOAD_DIR
    vector_dir = vector_dir or DEFAULT_VECTOR_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    vector_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir, vector_dir
