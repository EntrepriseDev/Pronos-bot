import os
import json
import logging
import requests
import anthropic
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# 🔑 Chargement des variables d'environnement
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
WEBHOOK_URL = "https://pronos-bot.onrender.com"
SPECIFIC_GROUPS = ["@VpnAfricain"]
ADMIN_IDS = [5427497623, 987654321]

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 📂 Gestion des fichiers JSON
def load_user_data():
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_data(user_data):
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, indent=4, ensure_ascii=False)

# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {"paris": 0}
        save_user_data(user_data)
    await update.message.reply_text(
        f"Bienvenue *{update.message.from_user.first_name}* ! 🎉\n"
        "📌 Utilise `/predire équipe1 vs équipe2` pour obtenir une prédiction.\n"
        "Exemple : `/predire PSG vs City`",
        parse_mode="Markdown"
    )

# Vérification de l'adhésion aux groupes
def can_predict(user_id):
    user_data = load_user_data()
    return user_data.get(str(user_id), {"paris": 0})["paris"] < 15

async def check_group_membership(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        return True
    for group in SPECIFIC_GROUPS:
        try:
            chat_member = await context.bot.get_chat_member(group, user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                return True
        except Exception as e:
            logging.error(f"Erreur lors de la vérification du groupe {group}: {e}")
            continue
    return False

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    if not await check_group_membership(update, context):
        await update.message.reply_text("⚠️ Tu dois être membre d'un groupe autorisé.")
        return
    
    if len(context.args) < 3 or "vs" not in context.args:
        await update.message.reply_text("⚠️ Usage : /predire [équipe1] vs [équipe2]")
        return
    
    team1, team2 = " ".join(context.args).split(" vs ")
    prompt = f"Prédiction du match {team1} vs {team2} selon les performances récentes."
    
    try:
        response = client.messages.create(
            model="Claude 3 Opus",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        prediction = response.content.strip()
        await update.message.reply_text(f"🔮 Prédiction : {prediction}")
    except Exception as e:
        logging.error(f"Erreur API Claude : {e}")
        await update.message.reply_text("❌ Erreur avec l'API Claude.")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    paris = user_data.get(user_id, {}).get("paris", 0)
    await update.message.reply_text(f"📊 Tu as utilisé {paris}/15 pronostics aujourd'hui.")

# 🔄 Commande /reset (Admin uniquement)
async def reset(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Commande réservée aux admins.")
        return
    save_user_data({})
    await update.message.reply_text("🔄 Toutes les stats ont été réinitialisées !")

# 🚀 Application Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot Telegram de pronostics en cours d'exécution !", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    if application:
        update = Update.de_json(request.get_json(), application.bot)
        application.process_update(update)
    return "OK", 200

# 🚀 Configuration du bot Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predire", predict_score))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("reset", reset))

# 🚀 Fonction principale
def main():
    port = int(os.getenv("PORT", 10000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
