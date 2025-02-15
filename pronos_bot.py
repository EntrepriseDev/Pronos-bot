import logging
import os
import json
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext
)

# ⚠️ Charger les clés API depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = "TON_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "TON_OPENAI_API_KEY"
WEBHOOK_URL = "https://pronos-bot.onrender.com"

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

# Fonction pour interroger l'API OpenAI
def get_prediction(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Erreur lors de la requête OpenAI : {e}")
        return "❌ Une erreur s'est produite avec GPT-4."

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
    prediction = get_prediction(prompt)

    await update.message.reply_text(f"🔮 Prédiction : {prediction}")

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

# Fonction principale pour lancer le bot en webhook
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
