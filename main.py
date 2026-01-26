import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request
import requests

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # obbligatorio
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")  # opzionale
CRON_SECRET = os.environ.get("CRON_SECRET")  # consigliato (per /cron/daily)

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN non impostato nelle variabili ambiente!")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

DB_PATH = os.environ.get("DB_PATH", "bot.db")

# -----------------------------
# APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# DB
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            first_seen TEXT,
            last_seen TEXT
        )
    """)
    conn.commit()
    conn.close()

def upsert_subscriber(chat_id: int):
    now = datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO subscribers(chat_id, first_seen, last_seen)
        VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET last_seen=excluded.last_seen
    """, (chat_id, now, now))
    conn.commit()
    conn.close()

def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM subscribers")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

init_db()

# -----------------------------
# TELEGRAM SEND
# -----------------------------
def send_message(chat_id: int, text: str):
    payload = {"chat_id": chat_id, "text": text}
    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=20)
    logger.debug(f"Telegram sendMessage: {r.status_code} - {r.text}")
    return r

# -----------------------------
# HEALTH
# -----------------------------
@app.get("/")
def health():
    return "ok", 200

# -----------------------------
# WEBHOOK
# -----------------------------
@app.post("/webhook")
def webhook():
    try:
        # Security opzionale: Telegram secret header
        if WEBHOOK_SECRET:
            secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            if secret != WEBHOOK_SECRET:
                logger.warning("Webhook secret NON valido")
                return "ok", 200  # sempre 200 per non creare retry

        data = request.get_json(force=True) or {}
        logger.debug(f"Update ricevuto: {data}")

        msg = data.get("message") or data.get("edited_message")
        if not msg:
            return "ok", 200

        chat = msg.get("chat") or {}
        chat_id = chat.get("id")
        text = msg.get("text", "")

        if not chat_id:
            return "ok", 200

        # salva/aggiorna iscritto
        upsert_subscriber(int(chat_id))

        # comandi base
        if text == "/start":
            send_message(int(chat_id),
                         "Ciao! Da ora sei iscritto.\n"
                         "Ogni giorno puoi ricevere una frase.\n"
                         "Scrivi qualunque cosa e ti rispondo.")
            return "ok", 200

        if text == "/help":
            send_message(int(chat_id),
                         "Comandi:\n"
                         "/start - iscriviti\n"
                         "/help - aiuto\n"
                         "La frase del giorno arriva automaticamente.")
            return "ok", 200

        # risposta normale (placeholder)
        if text:
            send_message(int(chat_id), f"Hai scritto: {text}")

        return "ok", 200

    except Exception:
        logger.exception("ERRORE dentro /webhook")
        return "ok", 200  # IMPORTANTISSIMO: mai 500 verso Telegram

# -----------------------------
# CRON: FRASE DEL GIORNO
# -----------------------------
def get_daily_phrase() -> str:
    # Qui puoi mettere le tue 100 frasi.
    # Per ora ne metto 10 di esempio (poi me ne dai 100 e le inserisco).
    phrases = [
        "Oggi fai una cosa piccola, ma falla davvero.",
        "Non serve correre: serve andare.",
        "La costanza batte il talento quando il talento si distrae.",
        "Se ti senti fermo, cambia angolo di visuale.",
        "Hai più controllo sulle abitudini che sulle emozioni.",
        "Una scelta giusta oggi vale una settimana di scuse domani.",
        "Non aspettare motivazione: crea disciplina.",
        "Anche cinque minuti contano.",
        "Smetti di rimandare la vita che dici di volere.",
        "Il coraggio non fa rumore. Ma cambia tutto."
    ]
    day_index = datetime.utcnow().timetuple().tm_yday % len(phrases)
    return phrases[day_index]

@app.get("/cron/daily")
def cron_daily():
    try:
        # Protezione cron
        if CRON_SECRET:
            secret = request.args.get("secret") or request.headers.get("X-Cron-Secret")
            if secret != CRON_SECRET:
                logger.warning("CRON secret NON valido")
                return "forbidden", 403

        phrase = get_daily_phrase()
        subs = get_all_subscribers()
        logger.info(f"Invio frase del giorno a {len(subs)} iscritti")

        sent = 0
        for chat_id in subs:
            try:
                send_message(int(chat_id), f"Frase del giorno:\n{phrase}")
                sent += 1
            except Exception:
                logger.exception(f"Errore invio a chat_id={chat_id}")

        return {"ok": True, "subscribers": len(subs), "sent": sent}, 200

    except Exception:
        logger.exception("ERRORE dentro /cron/daily")
        return {"ok": False}, 500
