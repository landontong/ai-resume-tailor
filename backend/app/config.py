from pathlib import Path
from dotenv import load_dotenv
import os

# Load backend/.env deterministically
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

if not OPENAI_API_KEY:
    raise RuntimeError(f"OPENAI_API_KEY missing. Expected it in {ENV_PATH}")
