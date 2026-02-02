import os
import logging
import sqlite3
from datetime import datetime
from flask import Flask, request
import requests
from openai import OpenAI

# -----------------------------
# OPENAI
# -----------------------------
# Usa OPENAI_API_KEY dalle variabili ambiente (su Render l'hai già messa).
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
client = OpenAI()

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------
# CONFIG
# -----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # obbligatorio
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")  # opzionale
CRON_SECRET = os.environ.get("CRON_SECRET")  # consigliato (per /cron/daily)
DB_PATH = os.environ.get("DB_PATH", "bot.db")

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN non impostato nelle variabili ambiente!")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

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
# CHATGPT REPLY
# -----------------------------
def chatgpt_reply(user_text: str) -> str:
    try:
        system_prompt = (
            "Sei ParlaConMe. Rispondi in italiano. "
            "Tono umano, diretto, non prolisso. "
            "Massimo 4-5 righe. "
            "Se la richiesta è vaga, fai UNA domanda di chiarimento. "
            "Niente moralismi, niente prediche. "
            "Se l'utente chiede consigli pratici (lavoro, viaggi, tecnologia, ecc.), sii concreto."
        )

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        )

        txt = (response.output_text or "").strip()
        return txt if txt else "Dimmi meglio cosa intendi."

    except Exception:
        logger.exception("Errore ChatGPT")
        return "Ho avuto un attimo di vuoto. Me lo riscrivi in modo più semplice?"

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
            send_message(
                int(chat_id),
                "Ciao! Da ora sei iscritto.\n"
                "Ogni giorno puoi ricevere una frase.\n"
                "Scrivi qualunque cosa e ti rispondo."
            )
            return "ok", 200

        if text == "/help":
            send_message(
                int(chat_id),
                "Comandi:\n"
                "/start - iscriviti\n"
                "/help - aiuto\n"
                "La frase del giorno arriva automaticamente."
            )
            return "ok", 200

        # risposta con ChatGPT
        if text:
            reply = chatgpt_reply(text)
            send_message(int(chat_id), reply)

        return "ok", 200

    except Exception:
        logger.exception("ERRORE dentro /webhook")
        return "ok", 200  # IMPORTANTISSIMO: mai 500 verso Telegram

# -----------------------------
# CRON: FRASE DEL GIORNO
# -----------------------------
def get_daily_phrase() -> str:
    phrases = [
        "Oggi non serve essere motivati. Serve essere presenti.",
        "La disciplina è una forma di rispetto verso te stesso.",
        "Se aspetti il momento giusto, stai solo rimandando.",
        "Fai meno promesse. Mantienine una.",
        "La chiarezza arriva quando smetti di scappare.",
        "Non tutto deve piacerti. Deve servirti.",
        "Il cambiamento inizia quando smetti di raccontarti scuse.",
        "Un passo vero vale più di dieci pensati.",
        "La costanza batte l’entusiasmo, ogni volta.",
        "Sii coerente anche quando nessuno guarda.",

        "Oggi fai la cosa che stai evitando.",
        "Non devi fare tutto. Devi fare la cosa giusta.",
        "La tua energia è limitata: usala meglio.",
        "Chi sei si vede da ciò che ripeti ogni giorno.",
        "La paura non sparisce. Si attraversa.",
        "Non cercare conferme: crea risultati.",
        "La fatica di oggi è la libertà di domani.",
        "Se ti senti fermo, forse stai pensando troppo.",
        "Agire chiarisce più di mille riflessioni.",
        "Smetti di negoziare con la tua pigrizia.",

        "Il silenzio spesso è una risposta onesta.",
        "Non tutto va risolto. Alcune cose vanno accettate.",
        "La disciplina non è rigidità: è direzione.",
        "Oggi scegli chi vuoi essere, non come ti senti.",
        "La tua attenzione decide la tua vita.",
        "Non aspettare di capire tutto per iniziare.",
        "La semplicità è una scelta difficile.",
        "Se qualcosa ti pesa, guardala in faccia.",
        "Il coraggio non fa rumore.",
        "La verità personale viene prima del consenso.",

        "Non stai perdendo tempo: lo stai investendo o sprecando.",
        "La lucidità vale più della motivazione.",
        "Ogni abitudine è un voto a favore di qualcuno che diventerai.",
        "La direzione conta più della velocità.",
        "Non confondere stanchezza con mancanza di senso.",
        "Se vuoi cambiare risultati, cambia routine.",
        "La forza è fare anche quando non va.",
        "Scegli una cosa sola e portala fino in fondo.",
        "La coerenza costruisce fiducia.",
        "Non sei in ritardo. Sei responsabile.",

        "Oggi riduci il rumore. Aumenta l’intenzione.",
        "La disciplina è libertà mascherata.",
        "Se ti lamenti, stai cedendo potere.",
        "Non servono grandi gesti, ma gesti veri.",
        "La chiarezza nasce dall’azione.",
        "Smetti di cercare scuse eleganti.",
        "Ogni giorno allena ciò che vuoi diventare.",
        "Non sei fragile: sei in costruzione.",
        "La direzione giusta spesso è scomoda.",
        "Fai spazio a ciò che conta davvero.",

        "La vita migliora quando smetti di rimandare.",
        "Non tutto è un problema. Molto è solo rumore.",
        "La disciplina non tradisce.",
        "Oggi scegli il passo, non l’alibi.",
        "La consapevolezza è una forma di coraggio.",
        "Se vuoi rispetto, inizia da te.",
        "Ogni scelta ripetuta diventa identità.",
        "La semplicità richiede carattere.",
        "Non devi convincere nessuno: devi agire.",
        "Oggi fai meglio di ieri. Basta questo.",

        "Non aspettare di sentirti pronto: inizia e diventa pronto.",
        "Se ti manca energia, controlla dove la stai perdendo.",
        "Il tuo futuro dipende dai “no” che dici oggi.",
        "Una decisione piccola può salvarti la giornata.",
        "Non inseguire tutto: scegli e difendi una direzione.",
        "La calma non è assenza di problemi: è gestione.",
        "Se ti senti confuso, torna alle basi.",
        "Meno opinioni, più fatti.",
        "Smetti di spiegare. Inizia a dimostrare.",
        "La disciplina è un muscolo: si allena.",

        "Non devi vincere oggi: devi non mollare.",
        "Se vuoi pace, taglia ciò che ti spegne.",
        "Ogni volta che ti tradisci, ti indebolisci.",
        "Ogni volta che ti rispetti, ti rinforzi.",
        "Se hai paura, stai andando verso qualcosa che conta.",
        "Non serve controllo totale: serve una buona direzione.",
        "Il caos fuori diminuisce quando ordini dentro.",
        "Non riempire il vuoto: ascoltalo.",
        "Oggi fai una cosa sola, ma falla bene.",
        "Smetti di rimandare la vita che dici di volere.",

        "Non sei qui per compiacere: sei qui per vivere.",
        "La tua routine parla più dei tuoi obiettivi.",
        "Se vuoi cambiare, cambia l’ambiente prima della volontà.",
        "La mente è brava a giustificare: tu sii bravo a scegliere.",
        "La chiarezza arriva quando smetti di mentirti.",
        "Non ti serve il piano perfetto: ti serve un piano che fai.",
        "La differenza la fa la seconda settimana, non il primo giorno.",
        "Non confondere intensità con progresso.",
        "La costanza è una forma di coraggio quotidiano.",
        "Oggi scegli cosa non fare. È già crescita.",

        "Se ti senti bloccato, riduci la posta e riparti.",
        "Non tutto merita una risposta: scegli le tue battaglie.",
        "La tua pace vale più della tua ragione.",
        "Quando sei stanco, non decidere. Riposa e poi scegli.",
        "Il tuo tempo è la tua valuta: spendilo meglio.",
        "Non rincorrere chi non ti sceglie: scegli te.",
        "Se vuoi rispetto, smetti di svenderti.",
        "Non aspettare il “dopo”: il dopo è adesso.",
        "Taglia il superfluo, resta con l’essenziale.",
        "Non serve rumore per essere forti."
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
