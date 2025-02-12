import os
import logging
import json
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import openai
import requests

# 🔹 Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Token du bot Telegram (via variables d’environnement)
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# 🔹 Clé API OpenAI
openai.api_key = "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"
if not openai.api_key:
    raise ValueError("La clé API OpenAI n'est pas définie !")

# 🔹 Initialisation de l'application Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# 🔹 Base de données JSON pour stocker les utilisateurs et leurs paris
USER_DATA_FILE = "user_data.json"
USER_DATA = {}

# 🔹 Charger les données des utilisateurs
def load_user_data():
    global USER_DATA
    try:
        with open(USER_DATA_FILE, 'r') as f:
            USER_DATA = json.load(f)
    except FileNotFoundError:
        USER_DATA = {}

# 🔹 Sauvegarder les données des utilisateurs
def save_user_data():
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(USER_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")

# 🔹 Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes disponibles.")

# 🔹 Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Démarrer le bot\n"
        "/help - Voir la liste des commandes\n"
        "/bet [événement] - Placer un pari\n"
        "/predictions [événement] - Obtenir un pronostic\n"
        "/bets - Voir vos paris\n"
    )
    await update.message.reply_text(help_text)

# 🔹 Commande /bet
async def place_bet(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("Usage : /bet [événement]")
        return

    event = ' '.join(context.args)
    user_id = str(update.message.from_user.id)

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"bets": [], "predictions_today": 0, "last_prediction_date": str(datetime.now().date())}

    USER_DATA[user_id]["bets"].append({"event": event, "status": "pending"})
    save_user_data()
    await update.message.reply_text(f"Pari sur '{event}' enregistré !")

# 🔹 Commande /predictions
async def get_predictions(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    today = str(datetime.now().date())

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"bets": [], "predictions_today": 0, "last_prediction_date": today}

    if USER_DATA[user_id]["last_prediction_date"] != today:
        USER_DATA[user_id]["predictions_today"] = 0
        USER_DATA[user_id]["last_prediction_date"] = today

    if USER_DATA[user_id]["predictions_today"] >= 15:
        await update.message.reply_text("Limite de 15 prédictions atteinte aujourd’hui !")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage : /predictions [événement]")
        return

    event = ' '.join(context.args)

    # 🔹 Obtenir un pronostic depuis OpenAI
    prompt = f"Donne un pronostic détaillé pour : {event}"
    try:
        response = openai.Completion.create(
            engine="text-davinci-003", prompt=prompt, max_tokens=100
        )
        prediction = response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Erreur lors de la demande à OpenAI: {e}")
        await update.message.reply_text("Désolé, une erreur s'est produite lors de la génération du pronostic.")
        return

    USER_DATA[user_id]["predictions_today"] += 1
    save_user_data()
    await update.message.reply_text(f"Pronostic pour '{event}':\n{prediction}")

# 🔹 Commande /bets
async def show_bets(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA or not USER_DATA[user_id]["bets"]:
        await update.message.reply_text("Aucun pari en cours.")
        return

    bet_text = "📌 **Vos paris en cours** :\n"
    for bet in USER_DATA[user_id]["bets"]:
        bet_text += f"📍 {bet['event']} - **{bet['status']}**\n"

    await update.message.reply_text(bet_text)

# ===========================
# 🔹 Initialisation de Flask
# ===========================
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    logger.info(f"Reçu une mise à jour : {data}")
    update = Update.de_json(data, application.bot)
    application.process_update(update)
    return "OK", 200

def set_webhook():
    """Configurer le webhook pour le bot Telegram"""
    webhook_url = f'https://pronos-bot.onrender.com/{TELEGRAM_BOT_TOKEN}'
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}'
    response = requests.get(url)
    logger.info(f"Réponse de Telegram : {response.text}")

if __name__ == "__main__":
    # Définir le webhook
    set_webhook()
    
    # Charger les données utilisateur
    load_user_data()
    
    # Lancer Flask
    app.run(host="0.0.0.0", port=10000)
