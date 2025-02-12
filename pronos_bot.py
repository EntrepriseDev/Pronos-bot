import os
import logging
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.ext import MessageHandler, filters

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token du bot Telegram (via variables d’environnement)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas défini !")

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
        logger.info("Données utilisateur sauvegardées avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des données : {e}")

# Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Bienvenue sur le bot de paris sportifs !\n\n"
        "Utilisez /help pour connaître toutes les commandes disponibles."
    )

# Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "/start - Démarrer le bot\n"
        "/help - Voir la liste des commandes\n"
        "/paris - Voir vos paris\n"
        "/parier [match] [cote] - Parier sur un match\n"
        "/solde - Voir votre solde\n"
        "/historique - Voir votre historique de paris\n"
    )
    await update.message.reply_text(help_text)

# Commande /paris
async def view_bets(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA:
        await update.message.reply_text("Vous n'avez pas encore effectué de paris.")
        return

    bets = USER_DATA[user_id].get("bets", [])
    if not bets:
        await update.message.reply_text("Aucun pari effectué pour le moment.")
    else:
        bet_text = "Voici vos paris en cours :\n"
        for bet in bets:
            bet_text += f"{bet['match']} - Cote: {bet['odds']} - Montant: {bet['amount']}€\n"
        await update.message.reply_text(bet_text)

# Commande /parier
async def place_bet(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /parier [match] [cote] [montant]")
        return

    match = context.args[0]
    odds = context.args[1]
    amount = context.args[2]

    try:
        amount = float(amount)
    except ValueError:
        await update.message.reply_text("Le montant doit être un nombre valide.")
        return

    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": 100, "bets": []}

    balance = USER_DATA[user_id]["balance"]
    if amount > balance:
        await update.message.reply_text("Vous n'avez pas assez d'argent pour parier.")
        return

    USER_DATA[user_id]["balance"] -= amount
    bet = {"match": match, "odds": odds, "amount": amount}
    USER_DATA[user_id]["bets"].append(bet)
    save_user_data()

    await update.message.reply_text(f"Pari effectué sur {match} avec une cote de {odds} pour {amount}€.")

# Commande /solde
async def check_balance(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": 100, "bets": []}

    balance = USER_DATA[user_id]["balance"]
    await update.message.reply_text(f"Votre solde actuel est de {balance}€.")

# Commande /historique
async def view_history(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in USER_DATA or "bets" not in USER_DATA[user_id]:
        await update.message.reply_text("Aucun historique de paris trouvé.")
        return

    bets = USER_DATA[user_id].get("bets", [])
    if not bets:
        await update.message.reply_text("Vous n'avez pas d'historique de paris.")
    else:
        history_text = "Historique de vos paris :\n"
        for bet in bets:
            history_text += f"{bet['match']} - Cote: {bet['odds']} - Montant: {bet['amount']}€\n"
        await update.message.reply_text(history_text)

# Initialisation de Flask pour le webhook
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Le bot de paris sportifs est en ligne ! 🚀"

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
    application.add_handler(CommandHandler("paris", view_bets))
    application.add_handler(CommandHandler("parier", place_bet))
    application.add_handler(CommandHandler("solde", check_balance))
    application.add_handler(CommandHandler("historique", view_history))

    # Définir le webhook
    webhook_url = f"https://pronos-bot.onrender.com/{TELEGRAM_BOT_TOKEN}"
    application.bot.set_webhook(url=webhook_url)

    # Démarrer Flask
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
