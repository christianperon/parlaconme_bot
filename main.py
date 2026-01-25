import os
from flask import Flask, request
import requests

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CRON_SECRET = os.getenv("CRON_SECRET", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

FRASE_DEL_GIORNO = "Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio."

TEST_CHAT_ID = 1222867929  # il tuo chat_id

# ===== APP =====
app = Flask(__name__)
application = app

# ===== UTILS =====
def send_message(chat_id: int, text: str) -> None:
    r = requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    print("SENDMESSAGE_STATUS:", r.status_code)
    print("SENDMESSAGE_BODY:", r.text)

# ===== HEALTHCHECK =====
@app.get("/")
def health():
    return "OK", 200

# ===== WEBHOOK TELEGRAM =====
@app.post("/webhook")
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return "no chat", 200

    if text == "/start":
        reply = (
            "🌱 Frase del giorno\n\n"
            f"{FRASE_DEL_GIORNO}\n\n"
            "ParlaConMe è qui. Torna quando vuoi."
        )
        send_message(chat_id, reply)

    return "ok", 200

# ===== CRON =====
@app.route("/cron", methods=["GET"])
def cron():
    secret = (request.args.get("secret") or "").strip()
    if not CRON_SECRET or secret != CRON_SECRET:
        return "forbidden", 403

    send_message(TEST_CHAT_ID, "🌅 Buongiorno. Messaggio giornaliero automatico.")
    return "ok", 200

