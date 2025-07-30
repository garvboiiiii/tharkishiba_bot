import psycopg2
from bot.config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()

def init_db():
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT PRIMARY KEY,
        username TEXT,
        wallet_address TEXT,
        points INT DEFAULT 0,
        total_earned INT DEFAULT 0,
        is_staking TEXT DEFAULT NULL,
        last_tap TIMESTAMP,
        mining_until TIMESTAMP
    )
    """)
    conn.commit()
