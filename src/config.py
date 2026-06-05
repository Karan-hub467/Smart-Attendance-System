import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "attendance_system"),
}

CAMERA_ID = int(os.getenv("CAMERA_ID", 0))
RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", 60.0))

KNOWN_FACES_DIR = BASE_DIR / "known_faces"
LOGS_DIR = BASE_DIR / "logs"

DB_SETUP_PATH = BASE_DIR / "database" / "schema.sql"

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
