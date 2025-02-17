import os
import json
import logging
import requests
import cohere
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ⚠️ Clés API
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
COHERE_API_KEY = "DvcWz4XL4lEKitKJERUfmqx0V5MWDP01AJbfGz37"
WEBHOOK_URL = "https://pronos-bot.onrender.com"  # Remplace par ton URL Render

# 📂 Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# 📌 Initialisation de Cohere
co = cohere.ClientV2(COHERE_API_KEY)

# 📝 Configuration du logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# 📂 Charger les données des utilisateurs
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# 📂 Sauvegarder les données des utilisateurs
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_data, f)

# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"Bienvenue {update.message.from_user.first_name}! 🎉\n"
        "Utilise /predire [équipe1] vs [équipe2] pour obtenir une prédiction. \n Exemple: /predire PSG vs City"
    )

# 🔮 Commande /predire (Prédiction de score avec Cohere)
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage correct : /predire [équipe1] vs [équipe2]")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = match.split(" vs ")
    team1, team2 = team1.strip(), team2.strip()

    prompt = f"Donne une estimation du score final de ce match au vue de leurs performances 2024-2025: {team1} vs {team2}"

    try:
        # Demander la prédiction à Cohere en utilisant le modèle command-r-plus-08-2024
        response = co.chat(
            model="command-r-plus-08-2024",  # Modèle mis à jour
            messages=[{"role": "user", "content": prompt}]
        )
        
        # La réponse est dans `response['generations'][0]['text']`
        prediction = response['generations'][0]['text'].strip()
        await update.message.reply_text(f"🔮 Prédiction : {prediction}")
    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une prédiction.")

# 📌 Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/predire [équipe1] vs [équipe2] - Prédiction de score\n"
        "/help - Afficher cette aide\n"
    )
    await update.message.reply_text(help_text)

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

# Ajouter les handlers de commandes
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predire", predict_score))
application.add_handler(CommandHandler("help", help_command))

# 🚀 Fonction principale pour lancer le bot en webhook
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
