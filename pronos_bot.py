import os
import logging
import json
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
import openai

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot Telegram
TELEGRAM_BOT_TOKEN = "7935826757:AAF..."
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# Clé API OpenAI
openai.api_key = "sk-proj-9l1Ihld..."

# Initialisation de l'application Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Base de données JSON pour stocker les informations des utilisateurs
USER_DATA_FILE = "user_data.json"
USER_DATA = {}

# Charger les données des utilisateurs
def load_user_data():
    global USER_DATA
    try:
        with open(USER_DATA_FILE, 'r') as f:
            USER_DATA = json.load(f)
    except FileNotFoundError:
        USER_DATA = {}

# Sauvegarder les données des utilisateurs
def save_user_data():
    try:
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(USER_DATA, f, indent=4)
        logger.info("Données sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde : {e}")

# Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Bienvenue ! Utilisez /help pour voir les commandes disponibles.")

# Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Démarrer le bot\n"
        "/help - Voir la liste des commandes\n"
        "/bet [événement] - Placer un pari\n"
        "/predictions [événement] - Obtenir un pronostic\n"
        "/bets - Voir vos paris\n"
    )
    await update.message.reply_text(help_text)

# Commande /bet
async def place_bet(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("Usage : /bet [événement]")
        return
    event = ' '.join(context.args)
    user_id = str(update.message.from_user.id)
    USER_DATA.setdefault(user_id, {"bets": [], "predictions_today": 0, "last_prediction_date": str(datetime.now().date())})
    USER_DATA[user_id]["bets"].append({"event": event, "status": "pending"})
    save_user_data()
    await update.message.reply_text(f"Pari sur '{event}' enregistré.")

# Commande /predictions
async def get_predictions(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    USER_DATA.setdefault(user_id, {"bets": [], "predictions_today": 0, "last_prediction_date": str(datetime.now().date())})
    if len(context.args) < 1:
        await update.message.reply_text("Usage : /predictions [événement]")
        return
    event = ' '.join(context.args)
    response = openai.Completion.create(engine="text-davinci-003", prompt=f"Pronostic pour {event}", max_tokens=100)
    prediction = response.choices[0].text.strip()
    USER_DATA[user_id]["predictions_today"] += 1
    save_user_data()
    await update.message.reply_text(f"Pronostic pour '{event}':\n{prediction}")

# Commande /bets
async def show_bets(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if not USER_DATA.get(user_id, {}).get("bets"):
        await update.message.reply_text("Aucun pari enregistré.")
        return
    bets = "\n".join([f"Événement : {bet['event']} | Statut : {bet['status']}" for bet in USER_DATA[user_id]["bets"]])
    await update.message.reply_text(f"Vos paris :\n{bets}")

# Initialisation de Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot Telegram est en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json()
    logger.info(f"Requête reçue : {json.dumps(data, indent=4)}")
    if not data:
        return "Bad Request", 400
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK", 200

# Démarrer le bot et Flask
async def main():
    load_user_data()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("bet", place_bet))
    application.add_handler(CommandHandler("predictions", get_predictions))
    application.add_handler(CommandHandler("bets", show_bets))
    webhook_url = f"https://pronos-bot.orender.com/{TELEGRAM_BOT_TOKEN}"
    await application.bot.set_webhook(url=webhook_url)
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    asyncio.run(main())
