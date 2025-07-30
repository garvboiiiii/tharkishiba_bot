from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from bot.db import c, conn
from bot.utils import can_tap, calculate_mining

# Constants
MAX_EARN = 5000
TAP_REWARD = 500
MINING_INTERVAL_HOURS = 3
MAX_GLOBAL_WITHDRAW = 1_000_000

def menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🪙 Tap", "⛏️ Mine")
    kb.row("💰 Withdraw", "📊 Stats")
    kb.row("🔗 Connect Wallet", "🪙 Stake")
    return kb

def is_valid_ton_wallet(address):
    return address.startswith("EQ") and len(address) == 48

def setup_handlers(bot):

    @bot.message_handler(commands=["start"])
    def start(msg):
        uid = msg.from_user.id
        username = msg.from_user.username or f"user{uid}"
        c.execute("SELECT id FROM users WHERE id = %s", (uid,))
        if not c.fetchone():
            c.execute("INSERT INTO users (id, username) VALUES (%s, %s)", (uid, username))
            conn.commit()
        bot.send_message(uid, "🌸 Welcome to TharkiShiba Miner ($TSBA)!", reply_markup=menu())

    @bot.message_handler(func=lambda m: m.text == "🪙 Tap")
    def tap(msg):
        uid = msg.from_user.id
        c.execute("SELECT points, last_tap, total_earned FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row:
            return
        points, last_tap, earned = row

        if not can_tap(last_tap):
            bot.send_message(uid, "⏳ Wait 3 hours before tapping again.")
            return

        if earned >= MAX_EARN:
            bot.send_message(uid, "🚫 Withdraw cap reached. Keep earning, but can't withdraw more.")
            return

        points += TAP_REWARD
        earned += TAP_REWARD
        c.execute("UPDATE users SET points = %s, last_tap = %s, total_earned = %s WHERE id = %s",
                  (points, datetime.utcnow(), earned, uid))
        conn.commit()
        bot.send_message(uid, f"✅ +{TAP_REWARD} TSBA! Total balance: {points}")

    @bot.message_handler(func=lambda m: m.text == "⛏️ Mine")
    def mine(msg):
        uid = msg.from_user.id
        now = datetime.utcnow()
        c.execute("SELECT mining_until, is_staking FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row:
            return
        mining_until, stake = row
        if mining_until and mining_until > now:
            bot.send_message(uid, "⛏️ You're already mining.")
            return

        reward = calculate_mining(stake)
        c.execute(
            "UPDATE users SET points = points + %s, total_earned = total_earned + %s, mining_until = %s WHERE id = %s",
            (reward, reward, now + timedelta(hours=MINING_INTERVAL_HOURS), uid)
        )
        conn.commit()
        bot.send_message(uid, f"⛏️ Mining started! You’ll earn {reward} TSBA in {MINING_INTERVAL_HOURS} hours.")

    @bot.message_handler(func=lambda m: m.text == "💰 Withdraw")
    def withdraw(msg):
        uid = msg.from_user.id

        # Check global cap
        c.execute("SELECT SUM(total_earned) FROM users")
        total_distributed = c.fetchone()[0] or 0
        if total_distributed >= MAX_GLOBAL_WITHDRAW:
            bot.send_message(uid, "🚫 Early withdraw window is closed globally.")
            return

        c.execute("SELECT points, wallet_address, total_earned FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row:
            return
        points, wallet, earned = row

        if not wallet:
            bot.send_message(uid, "🔗 Connect your TON wallet with '🔗 Connect Wallet'")
            return

        if earned > MAX_EARN:
            bot.send_message(uid, "❌ You hit the 5K withdraw limit.")
            return

        bot.send_message(uid, f"💸 {points} TSBA sent to {wallet} (mock transfer).")
        c.execute("UPDATE users SET points = 0 WHERE id = %s", (uid,))
        conn.commit()

    @bot.message_handler(func=lambda m: m.text == "📊 Stats")
    def stats(msg):
        uid = msg.from_user.id
        c.execute("SELECT points, total_earned, is_staking FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row:
            return
        points, earned, stake = row
        bot.send_message(uid, f"📊 Balance: {points} TSBA\n🧮 Earned: {earned}\n💎 Staking: {stake or 'None'}")

    @bot.message_handler(func=lambda m: m.text == "🔗 Connect Wallet")
    def connect_wallet(msg):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("🌐 Open TON Web Wallet", url="https://wallet.ton.org"))
        kb.add(InlineKeyboardButton("💼 Open Telegram @wallet", url="https://t.me/wallet"))

        bot.send_message(
            msg.chat.id,
            "🔗 Choose a wallet to connect:\n\n"
            "• Tap below to open your TON wallet\n"
            "• Or manually paste your wallet address (starts with `EQ...`)",
            reply_markup=kb
        )
        bot.register_next_step_handler(msg, save_wallet)

    def save_wallet(msg):
        uid = msg.from_user.id
        address = msg.text.strip()

        if not is_valid_ton_wallet(address):
            bot.send_message(uid, "⚠️ Invalid TON wallet address. Please make sure it starts with `EQ` and is 48 characters.")
            return connect_wallet(msg)

        c.execute("UPDATE users SET wallet_address = %s WHERE id = %s", (address, uid))
        conn.commit()
        bot.send_message(uid, f"✅ Wallet connected: `{address}`", parse_mode="Markdown")

    @bot.message_handler(func=lambda m: m.text == "🪙 Stake")
    def stake_menu(msg):
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.row("Half Stake", "Full Stake", "Cancel")
        bot.send_message(msg.chat.id, "Choose your staking level:", reply_markup=kb)

    @bot.message_handler(func=lambda m: m.text in ["Half Stake", "Full Stake"])
    def stake(msg):
        level = "half" if "Half" in msg.text else "full"
        c.execute("UPDATE users SET is_staking = %s WHERE id = %s", (level, msg.from_user.id))
        conn.commit()
        bot.send_message(msg.chat.id, f"✅ You're now staking: {level.upper()}")
