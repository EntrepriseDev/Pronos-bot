import logging
import os
import json
import anthropic
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ⚠️ Clés API (remplace par tes vraies clés)
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
CLAUDE_API_KEY = "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"
WEBHOOK_URL = "https://pronos-bot.onrender.com"  # Remplace par ton URL

# Initialisation du client Claude.ai
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

# Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# Configuration du logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les données des utilisateurs
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Sauvegarder les données des utilisateurs
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        user_data[user_id] = {"paris": 0}
        save_user_data(user_data)

    await update.message.reply_text(
        f"Bienvenue {update.message.from_user.first_name}! 🎉\n"
        "Utilise /predire [équipe1] vs [équipe2] pour obtenir une prédiction."
    )

# Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = context.args[0], context.args[1]
    prompt = f"Prédisez le score final pour {team1} vs {team2}. Score :"

    try:
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        prediction = response.content.strip()
        await update.message.reply_text(f"🔮 Prédiction : {prediction}")
    except Exception as e:
        logger.error(f"Erreur avec Claude.ai : {e}")
        await update.message.reply_text("❌ Une erreur s'est produite avec l'IA.")

# Commande /solde
async def balance(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    balance = user_data.get(user_id, {}).get("paris", 0)
    await update.message.reply_text(f"💰 Ton solde : {balance} points.")

# 🚀 Application Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot Telegram de pronostics en cours d'exécution !", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return "OK", 200

# 🚀 Configuration du bot Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predire", predict_score))
application.add_handler(CommandHandler("solde", balance))

# Fonction principale
def main():
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
