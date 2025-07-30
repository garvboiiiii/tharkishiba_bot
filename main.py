from flask import Flask, request
import telebot
from bot.config import BOT_TOKEN, WEBHOOK_URL
from bot.handlers import setup_handlers

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
setup_handlers(bot)

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "TharkiShiba Bot Running!"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=8080)
  
