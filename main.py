from flask import Flask, request
import os
import time
import datetime
import requests
import traceback

from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

BOT_TOKEN = '8026104755:AAHQ31YSCJjGHP6mVA1vaAg7zmgHC7gvaNo'
CHAT_ID = '5455197940'

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Merhaba! Uygun biletleri kontrol etmek için /kontrol yaz.\n\nÖrnek:\n/kontrol 2025-04-20 2025-04-30 750")

# --- WIZZAIR (belirli destinasyon listesiyle) ---
def get_wizzair_flights(start_date, end_date, max_price, update=None):
    return []

# --- KONTROL KOMUTU ---
def kontrol(update: Update, context: CallbackContext):
    update.message.reply_text("🚫 Bot geçici olarak devre dışı.")
    return

# --- WEBHOOK ---
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Flight bot is running!"

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("kontrol", kontrol))

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
