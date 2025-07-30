import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "your-bot-token")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your.webhook.url")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")
