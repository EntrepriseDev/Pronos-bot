import logging
import os
import json
import openai
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext
)

# ⚠️ Charger les clés API depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
OPENAI_API_KEY = "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"
WEBHOOK_URL = "https://pronos-bot.onrender.com"  # Remplace par ton URL Render

openai.api_key = OPENAI_API_KEY

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
        user_data[user_id] = {"paris": 0}  # Initialisation du solde
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
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    prediction = response["choices"][0]["text"].strip()
    await update.message.reply_text(f"🔮 Prédiction : {prediction}")
except openai.error.OpenAIError as e:
    logger.error(f"Erreur OpenAI : {e}")
    await update.message.reply_text("❌ Erreur OpenAI. Vérifie ta clé API et ton solde OpenAI.")
except Exception as e:
    logger.error(f"Erreur inattendue : {e}")
    await update.message.reply_text("❌ Une erreur inconnue s'est produite.")


# Commande /solde
async def balance(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    balance = user_data.get(user_id, {}).get("paris", 0)
    await update.message.reply_text(f"💰 Ton solde : {balance} points.")

# Commande /parier
async def bet(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data or user_data[user_id]["paris"] <= 0:
        await update.message.reply_text("Tu n'as pas de points pour parier. Utilise /predire pour en obtenir.")
        return

    try:
        bet_amount = int(context.args[0])
        if bet_amount <= 0:
            raise ValueError
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Usage : /parier [montant]")
        return

    user_data[user_id]["paris"] -= bet_amount
    save_user_data(user_data)

    await update.message.reply_text(f"✅ Pari de {bet_amount} points enregistré !")

# Commande /reset (admin)
async def reset(update: Update, context: CallbackContext):
    admin_id = 123456789  # Remplace avec ton ID Telegram
    if update.message.from_user.id != admin_id:
        await update.message.reply_text("🚫 Tu n'as pas les permissions pour cette action.")
        return

    user_data = load_user_data()
    for user in user_data:
        user_data[user]["paris"] = 0
    save_user_data(user_data)

    await update.message.reply_text("🔄 Tous les soldes ont été réinitialisés.")

# Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/predire [équipe1] vs [équipe2] - Prédiction de score\n"
        "/parier [montant] - Parier des points\n"
        "/solde - Voir ton solde\n"
        "/reset - (Admin) Réinitialiser les soldes\n"
    )
    await update.message.reply_text(help_text)

# 🚀 Application Flask
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "✅ Bot Telegram de pronostics en cours d'exécution !", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def webhook():
    """Réception des mises à jour de Telegram via Webhook"""
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return "OK", 200

# 🚀 Configuration du bot Telegram
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Ajouter les handlers de commandes
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predire", predict_score))
application.add_handler(CommandHandler("parier", bet))
application.add_handler(CommandHandler("solde", balance))
application.add_handler(CommandHandler("reset", reset))
application.add_handler(CommandHandler("help", help_command))

# Fonction principale pour lancer le bot en webhook
def main():
    """Lancer le bot avec un webhook"""
    application.run_webhook(
        listen="0.0.0.0",
        port=10000,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

    # Lancer Flask en parallèle
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    main()
