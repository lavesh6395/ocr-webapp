"""
Application Configuration

Single source of truth for environment-specific settings.
Deployed on Oracle Cloud Ubuntu VM via systemd + Uvicorn.
"""

from pathlib import Path
import os
import logging

# ---------- Logging ----------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = logging.getLogger("notebook-ai")

# ---------- Project Paths ----------

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

PROCESSED_DIR = BASE_DIR / "processed"
PROCESSED_DIR.mkdir(exist_ok=True)

MODEL_CACHE_DIR = BASE_DIR / "model_cache"
MODEL_CACHE_DIR.mkdir(exist_ok=True)

# ---------- Application ----------

APP_NAME = "Notebook-to-PDF AI"
APP_VERSION = "1.0.0"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# ---------- Upload Limits ----------

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))

# ---------- PaddleOCR ----------

PADDLE_HOME = os.getenv(
    "PADDLE_HOME",
    str(MODEL_CACHE_DIR)
)

os.environ["PADDLE_HOME"] = PADDLE_HOME
