import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_PATH = BASE_DIR / "data" / "library.db"
