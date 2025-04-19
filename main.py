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
    try:
        args = context.args
        if len(args) != 3:
            update.message.reply_text(
                "Lütfen şu formatı kullan:\n/kontrol YYYY-AA-GG YYYY-AA-GG maksimum_fiyat\n"
                "Örnek:\n/kontrol 2025-04-20 2025-04-30 750"
            )
            return

        start_date, end_date, max_price = args
        max_price = int(max_price)

        update.message.reply_text("🔎 Gerçek Ryanair verileriyle biletler aranıyor...")

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

        flights = []
        for item in data.get("fares", []):
            fare = item.get("outbound", {})
            price_info = fare.get("price", {})
            amount = price_info.get("value", 9999)
            if amount <= max_price:
                flights.append({
                    "destination": fare.get("arrivalAirport", {}).get("name", "Unknown"),
                    "airport_code": fare.get("arrivalAirport", {}).get("iataCode", ""),
                    "price": amount,
                    "date": fare.get("departureDate", "")[:10],
                    "time": fare.get("departureDate", "")[11:16]
                })

        if not flights:
            update.message.reply_text("❌ Bu aralıkta uygun fiyatlı Ryanair uçuşu bulunamadı.")
        else:
            for deal in flights:
                msg = (
                    f"✈️ *Ucuz bilet bulundu!*\n"
                    f"📍 Varış: *{deal['destination']}* ({deal['airport_code']})\n"
                    f"📅 Tarih: *{deal['date']}*\n"
                    f"🕒 Saat: *{deal['time']}*\n"
                    f"💸 Fiyat: *{deal['price']} SEK*"
                )
                update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        print(f"Hata: {e}")
        update.message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")


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
