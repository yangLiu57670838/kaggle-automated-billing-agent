from pathlib import Path

from dotenv import load_dotenv

def load_env() -> None:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")