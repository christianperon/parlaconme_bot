import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
application = app

FRASE_DEL_GIORNO = "“Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio.”"


def send_message(chat_id: int, text: str) -> None:
    if not BOT_TOKEN:
        return
    requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )


@app.get("/")
def healthcheck():
    return "OK", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        update = request.get_json(force=True) or {}
        print("UPDATE:", update)

        message = update.get("message") or update.get("edited_message") or {}
        chat_id = (message.get("chat") or {}).get("id")
        text = (message.get("text") or "").strip()

        if chat_id and text == "/start":
            send_message(chat_id, "✅ Bot vivo. /start ricevuto.")

        return "ok", 200

    except Exception as e:
        print("WEBHOOK_ERROR:", e)
        return "error", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
