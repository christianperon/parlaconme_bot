import os
import logging
from flask import Flask, request
import requests

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # obbligatorio
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")  # opzionale

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# --------------------------------------------------
# APP
# --------------------------------------------------
app = Flask(__name__)

# --------------------------------------------------
# WEBHOOK
# --------------------------------------------------
@app.post("/webhook")
def webhook():
    try:
        data = request.get_json(force=True)
        logger.debug(f"Update ricevuto: {data}")

        # --- sicurezza opzionale ---
        if WEBHOOK_SECRET:
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret != WEBHOOK_SECRET:
                logger.warning("Webhook secret NON valido")
                return "ok", 200

        # --- messaggio testuale ---
        if "message" in data and "text" in data["message"]:
            chat_id = data["message"]["chat"]["id"]
            text = data["message"]["text"]

            reply = f"Hai scritto: {text}"

            send_message(chat_id, reply)

        return "ok", 200

    except Exception:
        logger.exception("ERRORE dentro /webhook")
        # SEMPRE 200 → Telegram smette di ritentare
        return "ok", 200


# --------------------------------------------------
# SEND MESSAGE
# --------------------------------------------------
def send_message(chat_id, text):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload)
    logger.debug(f"Risposta Telegram: {r.status_code} - {r.text}")


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@app.get("/")
def health():
    return "ok", 200
