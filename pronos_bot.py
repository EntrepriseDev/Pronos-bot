import os
import logging
import json
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import openai
from telegram import Bot

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot Telegram (via variables d’environnement)
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

# Clé API OpenAI (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)
openai.api_key = "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"

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
        "/bet [événement] - Placer un pari sur un événement\n"
        "/predictions [événement] - Obtenir un pronostic\n"
        "/bets - Voir vos paris\n"
    )
    await update.message.reply_text(help_text)

# Commande /bet
async def place_bet(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("Usage incorrect. Vous devez spécifier un événement après la commande. Exemple : /bet Match de football entre équipe A et équipe B.")
        return

    event = ' '.join(context.args)
    
    # Enregistrer le pari de l'utilisateur
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"bets": [], "predictions_today": 0, "last_prediction_date": str(datetime.now().date())}

    USER_DATA[user_id]["bets"].append({"event": event, "status": "pending"})
    save_user_data()

    await update.message.reply_text(f"Pari sur l'événement '{event}' effectué. Vous pouvez maintenant demander un pronostic avec /predictions.")

# Commande /predictions
async def get_predictions(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"bets": [], "predictions_today": 0, "last_prediction_date": str(datetime.now().date())}

    # Vérifier le nombre de prédictions pour aujourd'hui
    today = str(datetime.now().date())
    if USER_DATA[user_id]["last_prediction_date"] != today:
        USER_DATA[user_id]["predictions_today"] = 0  # Reset daily counter
        USER_DATA[user_id]["last_prediction_date"] = today

    if USER_DATA[user_id]["predictions_today"] >= 15:
        await update.message.reply_text("Vous avez atteint la limite de 15 prédictions par jour. Pour plus de pronostics, faites une transaction au numéro suivant : +7935826757.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage incorrect. Vous devez spécifier un événement après la commande. Exemple : /predictions Match de football entre équipe A et équipe B.")
        return

    event = ' '.join(context.args)
    
    # Demander un pronostic à OpenAI pour l'événement
    prompt = f"Fournis un pronostic détaillé pour l'événement suivant : {event}. Que peuvent être les résultats ?"
    response = openai.Completion.create(
        engine="text-davinci-003", 
        prompt=prompt, 
        max_tokens=100
    )
    
    prediction = response.choices[0].text.strip()

    # Enregistrer la prédiction
    USER_DATA[user_id]["predictions_today"] += 1
    save_user_data()

    # Répondre à l'utilisateur avec le pronostic
    await update.message.reply_text(f"Pronostic pour l'événement '{event}':\n{prediction}")

# Commande /bets
async def show_bets(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA or not USER_DATA[user_id]["bets"]:
        await update.message.reply_text("Vous n'avez pas encore placé de paris. Utilisez la commande /bet pour placer un pari.")
        return

    bet_text = "Voici vos paris en cours :\n"
    for bet in USER_DATA[user_id]["bets"]:
        bet_text += f"Événement : {bet['event']}\nStatut : {bet['status']}\n\n"
    
    await update.message.reply_text(bet_text)

# Initialisation de Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot Telegram est en ligne ! 🚀"

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
async def webhook():
    """Route du webhook qui traite les mises à jour de Telegram"""
    data = request.get_json()
    logger.info(f"Requête reçue : {json.dumps(data, indent=4)}")

    if not data:
        return "Bad Request", 400

    update = Update.de_json(data, application.bot)
    await application.initialize()
    await application.process_update(update)

    return "OK", 200

# Démarrer le bot et Flask
def main():
    load_user_data()

    # Ajouter les handlers de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("bet", place_bet))
    application.add_handler(CommandHandler("predictions", get_predictions))
    application.add_handler(CommandHandler("bets", show_bets))

    # Définir le webhook
    webhook_url = f"https://ton-domaine-sur-render.com/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
