from flask import Flask, request
import os
import requests

from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

BOT_TOKEN = '8026104755:AAHQ31YSCJjGHP6mVA1vaAg7zmgHC7gvaNo'
CHAT_ID = '5455197940'

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Merhaba! Uygun biletleri kontrol etmek için /kontrol yaz.")

def kontrol(update: Update, context: CallbackContext):
    update.message.reply_text("🔍 Uygun biletler aranıyor...\n(örnek cevap) ✈️ Stockholm - Budapest 230 SEK")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("kontrol", kontrol))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Flight bot is running!"

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
