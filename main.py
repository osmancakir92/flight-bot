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
    update.message.reply_text("Merhaba!\n\nGidiş uçuşları için: /gidis YYYY-AA-GG YYYY-AA-GG fiyat\nGeliş uçuşları için: /gelis YYYY-AA-GG YYYY-AA-GG fiyat\nGidiş-Dönüş için: /tur YYYY-AA-GG YYYY-AA-GG fiyat [opsiyonel_havaalani_kodu]")

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
                    airport = fare.get("arrivalAirport", {})
                    ryanair_flights.append({
                        "destination": airport.get("name", "Unknown"),
                        "airport_code": airport.get("iataCode", ""),
                        "city": airport.get("city", {}).get("name", ""),
                        "country": airport.get("countryCode", ""),
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
                    f"📍 Varış: *{deal['destination']} / {deal['city']}, {deal['country'].upper()}* ({deal['airport_code']})\n"
                    f"📅 Tarih: *{deal['date']}*\n"
                    f"🕒 Saat: *{deal['time']}*\n"
                    f"💸 Fiyat: *{deal['price']} SEK*"
                )
                update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text("⚠️ Bir hata oluştu. Lütfen tekrar deneyin.")
        traceback.print_exc()

# --- TUR KOMUTU (GIDIŞ-DÖNÜŞ) ---
def tur(update: Update, context: CallbackContext):
    if update.message.chat.id != int(CHAT_ID):
        return

    try:
        args = context.args
        if len(args) not in [3, 4]:
            update.message.reply_text(
                "Lütfen şu formatı kullan:\n/tur YYYY-AA-GG YYYY-AA-GG maksimum_fiyat [opsiyonel_varış_havaalanı_kodu]\n"
                "Örnek:\n/tur 2025-04-25 2025-05-05 800\n"
                "veya belli lokasyon için: /tur 2025-04-25 2025-05-05 800 BVA"
            )
            return

        start_date, end_date, max_price = args[:3]
        max_price = int(max_price)
        hedef_havaalani = args[3].upper() if len(args) == 4 else None

        update.message.reply_text("🔁 Gidiş-Dönüş uçuşlar aranıyor...")

        headers = {"User-Agent": "Mozilla/5.0"}

        gidis_url = (
            f"https://www.ryanair.com/api/farfnd/3/oneWayFares"
            f"?departureAirportIataCode=ARN"
            f"&language=en&market=se-en"
            f"&outboundDepartureDateFrom={start_date}"
            f"&outboundDepartureDateTo={end_date}"
        )
        gidis_response = requests.get(gidis_url, headers=headers)
        gidis_data = gidis_response.json()

        tur_sonuclar = []

        for item in gidis_data.get("fares", []):
            g = item.get("outbound", {})
            gidis_fiyat = g.get("price", {}).get("value", 9999)
            if gidis_fiyat > max_price:
                continue
            airport = g.get("arrivalAirport", {})
            varis_havalimani = airport.get("iataCode", "")
            if hedef_havaalani and varis_havalimani != hedef_havaalani:
                continue

            gidis_tarih = g.get("departureDate", "")[:10]
            varis_adi = airport.get("name", "Unknown")
            varis_sehir = airport.get("city", {}).get("name", "")
            varis_ulke = airport.get("countryCode", "")
            kalkis_saat = g.get("departureDate", "")[11:16]

            gidis_date_obj = datetime.datetime.strptime(gidis_tarih, "%Y-%m-%d")
            donus_baslangic = gidis_date_obj + datetime.timedelta(days=1)

            donus_url = (
                f"https://www.ryanair.com/api/farfnd/3/oneWayFares"
                f"?departureAirportIataCode={varis_havalimani}"
                f"&arrivalAirportIataCode=ARN"
                f"&language=en&market=se-en"
                f"&outboundDepartureDateFrom={donus_baslangic.date()}"
                f"&outboundDepartureDateTo={end_date}"
            )
            try:
                donus_response = requests.get(donus_url, headers=headers)
                donus_data = donus_response.json()
                for d in donus_data.get("fares", []):
                    d_out = d.get("outbound", {})
                    donus_fiyat = d_out.get("price", {}).get("value", 9999)
                    if donus_fiyat > max_price:
                        continue
                    donus_tarih = d_out.get("departureDate", "")[:10]
                    donus_saat = d_out.get("departureDate", "")[11:16]

                    tur_sonuclar.append({
                        "lokasyon": varis_adi,
                        "kod": varis_havalimani,
                        "sehir": varis_sehir,
                        "ulke": varis_ulke,
                        "gidis_tarih": gidis_tarih,
                        "gidis_saat": kalkis_saat,
                        "gidis_fiyat": gidis_fiyat,
                        "donus_tarih": donus_tarih,
                        "donus_saat": donus_saat,
                        "donus_fiyat": donus_fiyat,
                        "toplam": gidis_fiyat + donus_fiyat
                    })
            except:
                continue

        if not tur_sonuclar:
            update.message.reply_text("❌ Gidiş-Dönüş uygun uçuş bulunamadı.")
        else:
            for d in tur_sonuclar:
                msg = (
                    f"🔁 *Gidiş-Dönüş bileti bulundu!*\n"
                    f"📍 Varış: *{d['lokasyon']} / {d['sehir']}, {d['ulke'].upper()}* ({d['kod']})\n"
                    f"🛫 Gidiş: *{d['gidis_tarih']} {d['gidis_saat']}* – 💸 *{d['gidis_fiyat']} SEK*\n"
                    f"🛬 Dönüş: *{d['donus_tarih']} {d['donus_saat']}* – 💸 *{d['donus_fiyat']} SEK*\n"
                    f"💰 Toplam: *{d['toplam']} SEK*"
                )
                update.message.reply_text(msg, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text("⚠️ Bir hata oluştu.")
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
dispatcher.add_handler(CommandHandler("tur", tur))

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
