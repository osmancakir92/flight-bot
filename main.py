from flask import Flask, request
import os
import datetime
import requests
import traceback

from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackContext

BOT_TOKEN = '8026104755:AAHQ31YSCJjGHP6mVA1vaAg7zmgHC7gvaNo'
CHAT_ID = '5455197940'
WEBHOOK_SECRET = 'abc123xyz'

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

def start(update: Update, context: CallbackContext):
    if update.message.chat.id != int(CHAT_ID):
        return
    update.message.reply_text("Merhaba!\n\nGidiş uçuşları için: /gidis YYYY-AA-GG YYYY-AA-GG fiyat\nGeliş uçuşları için: /gelis YYYY-AA-GG YYYY-AA-GG fiyat")

# --- GIDIŞ KONTROL KOMUTU ---
def gidis(update: Update, context: CallbackContext):
    if update.message.chat.id != int(CHAT_ID):
        return
    try:
        args = context.args
        if len(args) != 3:
            update.message.reply_text(
                "Lütfen şu formatı kullan:\n/gidis YYYY-AA-GG YYYY-AA-GG maksimum_fiyat\n"
                "Örnek:\n/gidis 2025-04-20 2025-04-30 750"
            )
            return

        start_date, end_date, max_price = args
        max_price = int(max_price)

        update.message.reply_text("🔎 Ryanair gidiş verileri kontrol ediliyor...")

        ryanair_flights = []
        try:
            url = (
                "https://www.ryanair.com/api/farfnd/3/oneWayFares"
                f"?departureAirportIataCode=ARN"
                f"&language=en&market=se-en"
                f"&outboundDepartureDateFrom={start_date}"
                f"&outboundDepartureDateTo={end_date}"
            )
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            data = response.json()
            for item in data.get("fares", []):
                fare = item.get("outbound", {})
                price_info = fare.get("price", {})
                amount = price_info.get("value", 9999)
                if amount <= max_price:
                    ryanair_flights.append({
                        "destination": fare.get("arrivalAirport", {}).get("name", "Unknown"),
                        "airport_code": fare.get("arrivalAirport", {}).get("iataCode", ""),
                        "price": amount,
                        "date": fare.get("departureDate", "")[:10],
                        "time": fare.get("departureDate", "")[11:16],
                        "airline": "Ryanair"
                    })
        except Exception as e:
            update.message.reply_text("🚨 Ryanair verisi alınamadı.")
            traceback.print_exc()

        if not ryanair_flights:
            update.message.reply_text("❌ Bu aralıkta uygun fiyatlı Ryanair gidiş uçuşu bulunamadı.")
        else:
            for deal in ryanair_flights:
                msg = (
                    f"✈️ *Ucuz bilet bulundu!*\n"
                    f"🏢 Havayolu: *{deal['airline']}*\n"
                    f"📍 Varış: *{deal['destination']}* ({deal['airport_code']})\n"
                    f"📅 Tarih: *{deal['date']}*\n"
                    f"🕒 Saat: *{deal['time']}*\n"
                    f"💸 Fiyat: *{deal['price']} SEK*"
                )
                update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")
        traceback.print_exc()

# --- GELIŞ KONTROL KOMUTU ---
def gelis(update: Update, context: CallbackContext):
    if update.message.chat.id != int(CHAT_ID):
        return
    try:
        args = context.args
        if len(args) != 3:
            update.message.reply_text(
                "Lütfen şu formatı kullan:\n/gelis YYYY-AA-GG YYYY-AA-GG maksimum_fiyat\n"
                "Örnek:\n/gelis 2025-04-20 2025-04-30 750"
            )
            return

        start_date, end_date, max_price = args
        max_price = int(max_price)

        update.message.reply_text("🔎 Stockholm varışlı Ryanair geliş verileri kontrol ediliyor...")

        ryanair_flights = []
        try:
            url = (
                "https://www.ryanair.com/api/farfnd/3/oneWayFares"
                f"?arrivalAirportIataCode=ARN"
                f"&language=en&market=se-en"
                f"&outboundDepartureDateFrom={start_date}"
                f"&outboundDepartureDateTo={end_date}"
            )
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            data = response.json()
            for item in data.get("fares", []):
                fare = item.get("outbound", {})
                price_info = fare.get("price", {})
                amount = price_info.get("value", 9999)
                if amount <= max_price:
                    ryanair_flights.append({
                        "destination": fare.get("departureAirport", {}).get("name", "Unknown"),
                        "airport_code": fare.get("departureAirport", {}).get("iataCode", ""),
                        "price": amount,
                        "date": fare.get("departureDate", "")[:10],
                        "time": fare.get("departureDate", "")[11:16],
                        "airline": "Ryanair"
                    })
        except Exception as e:
            update.message.reply_text("🚨 Ryanair verisi alınamadı.")
            traceback.print_exc()

        if not ryanair_flights:
            update.message.reply_text("❌ Bu aralıkta Stockholm varışlı uygun geliş uçuşu bulunamadı.")
        else:
            for deal in ryanair_flights:
                msg = (
                    f"🛬 *Ucuz geliş bileti bulundu!*\n"
                    f"🏢 Havayolu: *{deal['airline']}*\n"
                    f"📍 Kalkış: *{deal['destination']}* ({deal['airport_code']})\n"
                    f"📅 Tarih: *{deal['date']}*\n"
                    f"🕒 Saat: *{deal['time']}*\n"
                    f"💸 Fiyat: *{deal['price']} SEK*"
                )
                update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")
        traceback.print_exc()

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    secret = request.args.get("secret", "")
    if secret != WEBHOOK_SECRET:
        return "Unauthorized secret", 403

    update = Update.de_json(request.get_json(force=True), bot)
    if not update.message or update.message.chat.id != int(CHAT_ID):
        return "Unauthorized or ignored", 200

    dispatcher.process_update(update)
    return "OK"

@app.route("/", methods=["GET"])
def home():
    return "Flight bot is running!"

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("gidis", gidis))
dispatcher.add_handler(CommandHandler("gelis", gelis))

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
