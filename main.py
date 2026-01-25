import os
import sqlite3
import datetime
from flask import Flask, request
import requests

# ======================
# ENV
# ======================
BOT_TOKEN = os.getenv("B8098262880:AAHAnZVv7uAGI0vF8roZY6ndpKPg1hKyO40", "").strip()
CRON_SECRET = os.getenv("pcm_2026_secret", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()  # opzionale

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
application = app

# ======================
# DB (salva chat_id di chi fa /start)
# Nota: su Render Free senza Disk la persistenza può resettarsi.
# ======================
DB_PATH = os.getenv("DB_PATH", "bot.db").strip()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY
        )
        """
    )
    conn.commit()
    conn.close()

def save_chat(chat_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO chats(chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def get_all_chats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM chats")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

init_db()

# ======================
# 100 frasi (puoi aggiungerne quante vuoi)
# ======================
PHRASES = [
    "Non tutto ciò che pesa è sbagliato. A volte sta solo chiedendo spazio.",
    "La calma non è assenza di problemi: è la scelta di non farsi trascinare.",
    "Se ti senti confuso, fai una cosa piccola. Il resto si riallinea.",
    "Non devi dimostrare niente. Devi proteggere quello che sei.",
    "La forza è restare gentile senza diventare ingenuo.",
    "Non rincorrere risposte da chi vive di silenzi.",
    "Una giornata storta non è una vita storta.",
    "Riduci il rumore: sentirai meglio te stesso.",
    "La disciplina è un atto d’amore verso il tuo futuro.",
    "Non ti manca motivazione: ti manca chiarezza.",
    "Stai meglio quando smetti di negoziare con chi ti svuota.",
    "La tua pace vale più di qualsiasi reazione.",
    "Se ti costa dignità, costa troppo.",
    "Le cose importanti non urlano: si ripetono piano.",
    "Oggi non serve vincere: serve non mollare.",
    "Non fare spazio a chi porta caos e lo chiama carattere.",
    "Quando ti rispetti, cambi le regole del gioco.",
    "Non aspettare di sentirti pronto: muoviti e diventi pronto.",
    "Smetti di spiegarti a chi ha già deciso di non capire.",
    "La libertà inizia quando finisce la paura di dispiacere.",
    "Non è egoismo: è manutenzione.",
    "Ciò che proteggi, cresce.",
    "La mente corre. Tu resta presente.",
    "È okay essere stanco. Non è okay arrendersi.",
    "Non devi essere perfetto: devi essere costante.",
    "Se oggi fai il 60%, hai fatto il tuo.",
    "Non tutto merita una risposta. Alcune cose meritano un confine.",
    "Fai pace con i tempi lunghi: costruiscono fondamenta.",
    "Il coraggio è dire ‘basta’ senza bisogno di applausi.",
    "Se ti senti poco, cambia contesto. Non cambiare valore.",
    "Le priorità vere si vedono quando smetti di correre.",
    "Non rincorrere chi ti tratta come opzione.",
    "Ogni ‘no’ giusto è un ‘sì’ a te.",
    "A volte la svolta è una scelta che fai in silenzio.",
    "La coerenza batte l’intensità.",
    "Smetti di tornare dove ti sei perso.",
    "La tua energia non è infinita: usala bene.",
    "Non chiedere permesso per guarire.",
    "Non stai indietro: stai maturando.",
    "La serenità è una competenza, non un regalo.",
    "Chi ti vuole bene non ti confonde.",
    "Meglio solo che dimezzato.",
    "Se ti spegne, non è amore: è abitudine.",
    "Non devi meritarti il rispetto: è il minimo.",
    "Il tuo valore non cambia in base a chi non lo vede.",
    "Fai una cosa per volta, ma falla davvero.",
    "Non serve essere duro: serve essere fermo.",
    "La ripartenza è spesso discreta.",
    "Chiudi ciò che ti consuma, anche se ti manca.",
    "Non trattenere ciò che ti trattiene.",
    "Oggi scegli la versione di te che non scappa.",
    "La pazienza è potere quando sai dove stai andando.",
    "Se ti fa dubitare di te, non è per te.",
    "La chiarezza è pace.",
    "Quando ti ascolti, smetti di tradirti.",
    "L’autostima è un muscolo: si allena.",
    "Non sei in ritardo: sei in evoluzione.",
    "Dove c’è rispetto, c’è spazio. Dove non c’è, c’è ansia.",
    "Non confondere nostalgia con destino.",
    "La tua attenzione è una valuta: spendila bene.",
    "La stabilità è sexy.",
    "Non devi salvare tutti. Devi salvare te.",
    "Se è vero, non serve inseguirlo.",
    "Scegli ciò che ti semplifica.",
    "Non sei fragile: sei sensibile. E non è un difetto.",
    "Taglia il superfluo, torna all’essenziale.",
    "Ciò che non cambi, lo accetti.",
    "Non fare pace con ciò che ti ferisce.",
    "Non è ‘troppo’: è il tuo limite che sta parlando.",
    "Se ti senti spento, torna alle cose semplici.",
    "La mente crea scenari. Tu crea abitudini.",
    "Non servono grandi gesti: serve continuità.",
    "Il rispetto di te viene prima della comprensione altrui.",
    "Non restare dove devi mendicare attenzione.",
    "Ciò che è sano non ti mette alla prova ogni giorno.",
    "Se ti perdi, respira e ricomincia da qui.",
    "Non devi dimostrare di valere: devi ricordarlo.",
    "Se una cosa ti costa salute, non è un affare.",
    "Non trasformare la fatica in identità.",
    "Fai meno, ma meglio.",
    "La tua vita non è un tribunale: non devi difenderti sempre.",
    "Il silenzio può essere una risposta. E una protezione.",
    "Se vuoi cambiare, cambia ambiente o abitudini: uno dei due.",
    "Non cercare conferme, costruisci prove.",
    "Smetti di giustificare chi ti ferisce.",
    "Non è fretta: è fame di vita.",
    "Oggi scegli ciò che ti rende leggero.",
    "Non si guarisce in un giorno, ma si inizia in un minuto.",
    "Non devi vincere contro qualcuno: devi tornare a te.",
    "Se ti fa male spesso, non è ‘normale’.",
    "La dignità è un’abitudine.",
    "Non rinunciare a te per restare.",
    "Il tuo tempo è sacro: proteggilo.",
    "Non temere di cambiare idea: temere di restare uguale per paura.",
    "La pace è una decisione quotidiana.",
    "Dove c’è amore vero, non c’è umiliazione.",
    "Non sei solo: sei in costruzione.",
    "Oggi fai spazio al bene, anche se è piccolo.",
    "La tua storia non finisce in un capitolo difficile.",
    "Sii gentile con te: ci sei dentro ogni giorno.",
]

def phrase_for_today() -> str:
    today = datetime.date.today().toordinal()
    idx = today % len(PHRASES)
    return f"“{PHRASES[idx]}”"

# ======================
# Telegram send
# ======================
def send_message(chat_id: int, text: str) -> requests.Response:
    return requests.post(
        f"{API_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=15,
    )

# ======================
# Routes
# ======================
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

    # salva chat_id per invii futuri
    save_chat(int(chat_id))

    if text == "/start":
        reply = (
            "🌱 Frase del giorno\n"
            f"{phrase_for_today()}\n\n"
            "ParlaConMe è qui. Torna quando vuoi."
        )
        r = send_message(int(chat_id), reply)
        print("SEND /start:", r.status_code, r.text)

    return "ok", 200

@app.route("/cron", methods=["GET", "POST"])
def cron():
    # protezione
    secret = (request.args.get("secret") or "").strip()
    if not CRON_SECRET or secret != CRON_SECRET:
        return "forbidden", 403

    text = "🌅 Buongiorno\n" + phrase_for_today()

    targets = []
    if ADMIN_CHAT_ID.isdigit():
        targets = [int(ADMIN_CHAT_ID)]
    else:
        targets = get_all_chats()

    if not targets:
        return "no targets", 200

    for cid in targets:
        r = send_message(cid, text)
        print("CRON SEND:", cid, r.status_code, r.text)

    return "ok", 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
