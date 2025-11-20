import os
from pathlib import Path


env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip()

BOT_TOKEN = os.getenv("BOT_TOKEN", "NO_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "8016108614").split(",") if x.isdigit()]
MANAGER_ID = int(os.getenv("MANAGER_ID", "8016108614"))
