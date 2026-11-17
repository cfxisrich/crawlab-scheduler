"""Create the initial local deployment configuration without overwriting it."""

from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
content = (root / ".env.example").read_text(encoding="utf-8")
content = content.replace("MONGO_PASSWORD=", f"MONGO_PASSWORD={secrets.token_hex(24)}")
content = content.replace("ENGINE_AUTH_KEY=", f"ENGINE_AUTH_KEY={secrets.token_hex(32)}")
content = content.replace("SESSION_SECRET=", f"SESSION_SECRET={secrets.token_hex(32)}")
with (root / ".env").open("x", encoding="utf-8", newline="\n") as config:
    config.write(content)
print("Created .env. Start with: docker compose up -d --build")
