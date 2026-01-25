import os
from flask import Flask, request
import requests

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CRON_SECRET = os.getenv("CRON_SECRET", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

import random

FRASI = [
    "Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio.",
    "Anche il silenzio è una risposta, se impari ad ascoltarlo.",
    "Non devi correre. Devi solo non fermarti.",
    "Alcune cose fanno male perché stanno funzionando.",
    "Respira. Non sei in ritardo sulla tua vita.",
    "Ciò che oggi pesa, domani ti sosterrà.",
    "Non tutto va capito subito. Alcune cose maturano.",
    "La calma non è assenza di caos, è presenza di direzione.",
    "Se ti senti stanco, forse stai crescendo.",
    "Non spiegarti troppo: chi vuole capire, capisce.",
    "A volte la risposta è smettere di fare domande.",
    "Non sei fragile: sei sensibile in un mondo rumoroso.",
    "Ogni passo lento è comunque un passo.",
    "Non serve avere tutto chiaro. Serve essere sinceri.",
    "Anche fermarsi è una forma di avanzamento.",
    "Se qualcosa ti costa pace, è troppo caro.",
    "Non tutto ciò che perdi è una sconfitta.",
    "Il cambiamento non avvisa, ma arriva sempre puntuale.",
    "La tua voce conta, anche quando trema.",
    "Non devi essere forte oggi. Devi solo esserci.",
    "Alcune porte si chiudono per salvarti.",
    "La lucidità arriva dopo il dolore, non prima.",
    "Non sei sbagliato: sei fuori contesto.",
    "Anche i giorni storti fanno parte del disegno.",
    "La coerenza vale più dell’approvazione.",
    "Non rincorrere ciò che ti ignora.",
    "Ogni fine è un inizio che non conosci ancora.",
    "Se ti senti perso, forse stai cambiando strada.",
    "La pace non fa rumore, ma resta.",
    "Non tutto va sistemato oggi.",
    "Il tuo tempo non è in ritardo rispetto a nessuno.",
    "A volte la risposta è riposare.",
    "Non devi dimostrare nulla per valere.",
    "La chiarezza arriva quando smetti di forzare.",
    "Ciò che ti calma ti appartiene.",
    "Non avere fretta di guarire.",
    "Anche il dubbio è un segnale di coscienza.",
    "La forza non è resistere sempre.",
    "Non sei obbligato a restare dove non respiri.",
    "Il cambiamento spaventa prima di liberare.",
    "Ogni giorno è meno uguale di quanto credi.",
    "Non tutto va detto. Ma va sentito.",
    "La tua stanchezza ha una storia.",
    "Scegli ciò che ti fa dormire sereno.",
    "Non minimizzare ciò che senti.",
    "La lentezza è una forma di cura.",
    "Non sei solo, anche quando lo sembri.",
    "La direzione conta più della velocità.",
    "A volte mollare è un atto di lucidità.",
    "Non tutto è un problema da risolvere.",
    "La tua sensibilità è una bussola.",
    "Non sei in competizione con nessuno.",
    "Ogni giorno impari qualcosa, anche quando non sembra.",
    "La pace non chiede spiegazioni.",
    "Non devi piacere a tutti per essere vero.",
    "Ciò che ti pesa ti sta parlando.",
    "La calma arriva dopo la scelta giusta.",
    "Non forzare ciò che non fluisce.",
    "Anche dire no è una forma di rispetto.",
    "Non tutto ciò che finisce fallisce.",
    "La tua autenticità vale più del consenso.",
    "Non sei debole se chiedi spazio.",
    "Ogni confine è una protezione.",
    "La lucidità nasce dal silenzio.",
    "Non ignorare ciò che ti spegne.",
    "La direzione giusta spesso è scomoda.",
    "Non tutto va condiviso.",
    "La tua pace viene prima delle spiegazioni.",
    "Anche fermarsi è una scelta.",
    "Non sei in ritardo: stai arrivando.",
    "Ciò che ti rispetta non ti consuma.",
    "Ogni giorno è un piccolo riequilibrio.",
    "Non devi salvare nessuno per valere.",
    "La chiarezza arriva quando smetti di scappare.",
    "Non tutto va capito, alcune cose vanno attraversate.",
    "La tua verità non ha bisogno di rumore.",
    "Non restare dove devi fingere.",
    "La calma è una decisione quotidiana.",
    "Non sei sbagliato, stai cambiando.",
    "Ogni respiro è un ritorno a te.",
    "La pace è una scelta ripetuta.",
    "Non tutto va aggiustato oggi.",
    "Il tuo sentire è valido.",
    "Non minimizzare la tua stanchezza.",
    "La tua direzione conta.",
    "Non restare dove non cresci.",
    "La serenità non è noia, è equilibrio.",
    "Ogni giorno è un nuovo punto di partenza."
]

def frase_del_giorno():
    return random.choice(FRASI)

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
        reply = f"🌱 Frase del giorno\n{frase_del_giorno()}\n\nParlaConMe è qui. Torna quando vuoi."

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

