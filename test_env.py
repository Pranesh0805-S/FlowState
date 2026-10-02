"""Check SMTP configuration without printing credential values."""
import os
from pathlib import Path

from dotenv import load_dotenv

env_local = Path(__file__).resolve().with_name(".env.local")
load_dotenv(env_local if env_local.exists() else Path(__file__).resolve().with_name(".env"))
for key in ("PRODUCTIVITY_SMTP_EMAIL", "PRODUCTIVITY_SMTP_APP_PASSWORD"):
    print(f"{key}: {'configured' if os.getenv(key) else 'not configured'}")
