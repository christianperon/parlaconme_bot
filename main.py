import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
application = app
FRASE_DEL_GIORNO = "Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio."

CRON_SECRET = os.getenv("CRON_SECRET", "").strip()
@app.route("/cron", methods=["GET", "POST"])
def cron():
    secret = (request.args.get("secret") or request.headers.get("X-Cron-Secret") or "").strip()
    if not CRON_SECRET or secret != CRON_SECRET:
        return "forbidden", 403

    # TEST: manda un messaggio fisso a te
    TEST_CHAT_ID = 1222867929  # il tuo chat_id (dai log)
    send_message(TEST_CHAT_ID, f"🌅 Buongiorno.\n\n🌱 Frase del giorno\n{frase_di_oggi()}")

    return "ok", 200

from datetime import date

FRASI = [
    "Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio.",
    "Se oggi ti senti lento, non sei rotto: stai solo tornando a te.",
    "Non devi dimostrare nulla. Devi respirare e continuare.",
    "La pace non arriva quando finisce il rumore, ma quando smetti di inseguirlo.",
    "Un passo piccolo oggi vale più di una promessa enorme domani.",
]

def frase_di_oggi() -> str:
    # Rotazione semplice: una frase diversa ogni giorno, riparte quando finisce la lista
    i = date.today().toordinal() % len(FRASI)
    return FRASI[i]

def send_message(chat_id: int, text: str) -> None:
    r = requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )
    print("SENDMESSAGE_STATUS:", r.status_code)
    print("SENDMESSAGE_BODY:", r.text)

@app.get("/")
def healthcheck():
    return "OK", 200

import traceback  # <-- aggiungi questo import in alto insieme agli altri

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json(force=True) or {}

        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()

        if not chat_id:
            return "ok", 200
            remember_chat(chat_id)

       if text == "/start":
    reply = f"🌱 Frase del giorno\n{frase_di_oggi()}\n\nParlaConMe è qui. Torna quando vuoi."
    send_message(chat_id, reply)

        return "ok", 200

    except Exception as e:
        print("WEBHOOK_ERROR:", repr(e))
        print(traceback.format_exc())
        return "error", 500

CRON_SECRET = os.getenv("CRON_SECRET", "").strip()

# memoria semplice (per ora) dei chat_id che hanno scritto al bot
KNOWN_CHATS = set()

def remember_chat(chat_id: int) -> None:
    if chat_id:
        KNOWN_CHATS.add(int(chat_id))

# --- dentro la tua webhook(), subito dopo aver letto chat_id ---
# remember_chat(chat_id)

@app.route("/cron", methods=["POST"])
def cron_send_daily():
    # protezione base
    incoming = request.args.get("secret", "").strip()
    if not CRON_SECRET or incoming != CRON_SECRET:
        return "forbidden", 403


    if not KNOWN_CHATS:
        return "no chats", 200

    text = f"🌱 Frase del giorno\n{FRASE_DEL_GIORNO}"
    for cid in list(KNOWN_CHATS):
        try:
            send_message(cid, text)
        except Exception:
            pass

    return "sent", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
