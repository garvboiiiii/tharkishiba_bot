from telebot.types import ReplyKeyboardMarkup
from datetime import datetime, timedelta
from bot.db import c, conn
from bot.utils import can_tap, calculate_mining

def menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🪙 Tap", "⛏️ Mine")
    kb.row("💰 Withdraw", "📊 Stats")
    kb.row("🔗 Connect Wallet", "🪙 Stake")
    return kb

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
        if not row: return
        points, last_tap, earned = row
        if not can_tap(last_tap):
            bot.send_message(uid, "⏳ Wait 3 hours before tapping again.")
            return
        if earned >= 5000:
            bot.send_message(uid, "🚫 Withdraw cap reached. Keep earning, but can't withdraw more.")
        points += 500
        earned += 500
        c.execute("UPDATE users SET points = %s, last_tap = %s, total_earned = %s WHERE id = %s",
                  (points, datetime.utcnow(), earned, uid))
        conn.commit()
        bot.send_message(uid, f"✅ +500 TSBA! Total balance: {points}")

    @bot.message_handler(func=lambda m: m.text == "⛏️ Mine")
    def mine(msg):
        uid = msg.from_user.id
        now = datetime.utcnow()
        c.execute("SELECT mining_until, is_staking FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row: return
        mining_until, stake = row
        if mining_until and mining_until > now:
            bot.send_message(uid, "⛏️ You're already mining.")
            return
        reward = calculate_mining(stake)
        c.execute("UPDATE users SET points = points + %s, total_earned = total_earned + %s, mining_until = %s WHERE id = %s",
                  (reward, reward, now + timedelta(hours=3), uid))
        conn.commit()
        bot.send_message(uid, f"⛏️ Mining started! You’ll earn {reward} TSBA in 3 hours.")

    @bot.message_handler(func=lambda m: m.text == "💰 Withdraw")
    def withdraw(msg):
        uid = msg.from_user.id
        c.execute("SELECT points, wallet_address, total_earned FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row: return
        points, wallet, earned = row
        if not wallet:
            bot.send_message(uid, "🔗 First connect your TON wallet using '🔗 Connect Wallet'")
            return
        if earned > 5000:
            bot.send_message(uid, "❌ Withdraw window closed. You've hit the 5000 TSBA cap.")
            return
        bot.send_message(uid, f"💸 Withdrawn {points} TSBA to {wallet} (simulated).")
        c.execute("UPDATE users SET points = 0 WHERE id = %s", (uid,))
        conn.commit()

    @bot.message_handler(func=lambda m: m.text == "📊 Stats")
    def stats(msg):
        uid = msg.from_user.id
        c.execute("SELECT points, total_earned, is_staking FROM users WHERE id = %s", (uid,))
        row = c.fetchone()
        if not row: return
        points, earned, stake = row
        bot.send_message(uid, f"📊 Balance: {points} TSBA\n🧮 Earned: {earned}\n💎 Staking: {stake or 'None'}")

    @bot.message_handler(func=lambda m: m.text == "🔗 Connect Wallet")
    def connect_wallet(msg):
        bot.send_message(msg.chat.id, "Send your TON wallet address (starts with EQ):")
        bot.register_next_step_handler(msg, save_wallet)

    def save_wallet(msg):
        if msg.text.startswith("EQ") and len(msg.text.strip()) >= 48:
            c.execute("UPDATE users SET wallet_address = %s WHERE id = %s", (msg.text.strip(), msg.from_user.id))
            conn.commit()
            bot.send_message(msg.chat.id, "✅ Wallet linked.")
        else:
            bot.send_message(msg.chat.id, "❌ Invalid wallet format.")

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
