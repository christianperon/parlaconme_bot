import os
from flask import Flask, request
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

FRASE_DEL_GIORNO = "“Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio.”"

def send_message(chat_id: int, text: str) -> None:
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
    if not BOT_TOKEN:
        return "BOT_TOKEN missing", 500

    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return "no chat", 200

    if text == "/start":
        reply = f"🌱 Frase del giorno\n{FRASE_DEL_GIORNO}\n\nParlaConMe è qui. Torna quando vuoi."
        send_message(chat_id, reply)

    return "ok", 200

if __name__ == "__main__":
    # Render setta automaticamente la PORT
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
