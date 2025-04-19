# ... diğer importlar aynı kalıyor ...
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

# --- WIZZAIR ---
def get_wizzair_flights(start_date, end_date, max_price, update=None):
    flights = []
    url = "https://be.wizzair.com/7.10.1/Api/search/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    departure_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    while departure_date <= end_date_dt:
        payload = {
            "flightList": [
                {
                    "departureStation": "ARN",
                    "arrivalStation": "ANY",
                    "departureDate": departure_date.strftime("%Y-%m-%d")
                }
            ],
            "priceType": "regular",
            "isFlightChange": False,
            "adultCount": 1,
            "childCount": 0,
            "infantCount": 0,
            "wdc": True
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            if update:
                update.message.reply_text(f"📡 WizzAir yanıt kodu: {response.status_code}")
                update.message.reply_text(f"🧾 Yanıt uzunluğu: {len(response.text)} karakter")

            if response.status_code == 200:
                data = response.json()
                for flight in data.get("outboundFlights", []):
                    price = flight.get("price", {}).get("amount", 9999)
                    if price <= max_price:
                        flights.append({
                            "destination": flight.get("arrivalStation", "Unknown"),
                            "airport_code": flight.get("arrivalStation", ""),
                            "price": price,
                            "date": flight.get("departureDate", "")[:10],
                            "time": flight.get("departureDate", "")[11:16],
                            "airline": "WizzAir"
                        })
        except Exception as e:
            print("🚨 WizzAir hatası:")
            traceback.print_exc()

        time.sleep(2)
        departure_date += datetime.timedelta(days=1)

    return flights

# --- KONTROL KOMUTU ---
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

        update.message.reply_text("🔎 Ryanair ve WizzAir verileri kontrol ediliyor...")

        # --- Ryanair ---
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

        # --- WizzAir ---
        update.message.reply_text("🧪 WizzAir fonksiyonu çağrılıyor...")
        wizzair_flights = get_wizzair_flights(start_date, end_date, max_price, update=update)
        update.message.reply_text(f"🔍 WizzAir uçuş sayısı: {len(wizzair_flights)}")

        all_flights = ryanair_flights + wizzair_flights

        if not all_flights:
            update.message.reply_text("❌ Bu aralıkta uygun fiyatlı uçuş bulunamadı.")
        else:
            for deal in all_flights:
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
        print("🚨 Genel hata:")
        traceback.print_exc()
        update.message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")

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
