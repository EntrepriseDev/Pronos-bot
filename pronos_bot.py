import os
import json
import logging
import requests
import random
import cohere
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# ⚠️ Clés API
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
COHERE_API_KEY = "DvcWz4XL4lEKitKJERUfmqx0V5MWDP01AJbfGz37"
WEBHOOK_URL = "https://pronos-bot.onrender.com"

# 📂 Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# 🔥 Liste des admins (ajoute les ID Telegram des admins ici)
ADMINS = {5427497623, 0}

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

# 🤡 Blagues du Joker (exemple, peut être amélioré avec IA)
JOKER_JOKES = [
    "Pourquoi Batman n'aime pas les blagues ? Parce qu'il n'a pas de parents ! HAHAHA !",
    "Tu veux savoir pourquoi je souris toujours ? Parce que ça rend les gens nerveux...",
    "On vit dans une société où le bonheur est un crime, et moi, je suis coupable !",
]

# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"Bienvenue {update.message.from_user.first_name}! 🎉\n"
        "Utilise /predire [équipe1] vs [équipe2] pour obtenir une prédiction.\nExemple: /predire PSG vs City"
    )

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage correct : /predire [équipe1] vs [équipe2]")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = match.split(" vs ")
    prompt = f"Donne une estimation du score final de {team1.strip()} vs {team2.strip()}"

    try:
        response = co.chat(model="command-r-plus-08-2024", messages=[{"role": "user", "content": prompt}])
        prediction = response.message.content[0].text.strip()
        await update.message.reply_text(f"🔮 Prédiction : {prediction}")
    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une prédiction.")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    remaining = user_data.get(user_id, {}).get("predictions_left", 15)
    await update.message.reply_text(f"🤡 Il te reste {remaining} prédictions aujourd'hui... Ne gâche pas ta chance, HAHAHA!")

# 👑 Commande /admin (réservé aux admins)
async def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("HAHA! Tu crois être un roi ici ? Nope! Accès refusé! 😈")
        return
    await update.message.reply_text("Bienvenue dans le repaire du chaos, Ô grand administrateur! Que désires-tu ?")

# 🃏 Commande /joke (blague du Joker)
async def joke(update: Update, context: CallbackContext):
    joke = random.choice(JOKER_JOKES)
    await update.message.reply_text(f"🤡 {joke}")

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
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("admin", admin))
application.add_handler(CommandHandler("joke", joke))

# 🚀 Lancer le bot
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
