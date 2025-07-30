CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    username TEXT,
    wallet_address TEXT,
    points INT DEFAULT 0,
    total_earned INT DEFAULT 0,
    is_staking TEXT DEFAULT NULL,
    last_tap TIMESTAMP,
    mining_until TIMESTAMP
);
