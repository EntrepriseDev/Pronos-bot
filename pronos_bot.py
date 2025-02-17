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
ADMIN_ID = 123456789  # Remplace par ton ID Telegram

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
        "Utilise /predire [équipe1] vs [équipe2] pour obtenir une prédiction.\n"
        "Exemple: /predire PSG vs City"
    )

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = load_user_data()
    
    if str(user_id) != str(ADMIN_ID):
        user_data.setdefault(str(user_id), {"predictions_left": 15})
        if user_data[str(user_id)]["predictions_left"] <= 0:
            await update.message.reply_text("😈 Tu n'as plus de prédictions aujourd'hui ! Tu veux parier ta santé mentale ? 😂")
            return
        user_data[str(user_id)]["predictions_left"] -= 1
        save_user_data(user_data)
    
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage correct : /predire [équipe1] vs [équipe2]")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = match.split(" vs ")
    team1, team2 = team1.strip(), team2.strip()

    prompt = f"Imagine que tu es le Joker. Fais une prédiction du score pour {team1} vs {team2} dans un style chaotique et imprévisible."

    try:
        response = co.chat(
            model="command-r-plus-08-2024",
            messages=[{"role": "user", "content": prompt}]
        )
        if response.message.content:
            prediction = response.message.content[0].text.strip()
            await update.message.reply_text(f"😈 *Le Joker dit* : {prediction}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Aucune prédiction générée. Trop de sérieux dans ce monde…")
    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une prédiction. Mais tu peux toujours faire exploser quelque chose ! 💥")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    predictions_left = user_data.get(user_id, {}).get("predictions_left", 15)
    await update.message.reply_text(f"😈 Il te reste *{predictions_left}* prédictions aujourd'hui. Fais-en bon usage… ou pas. 😂", parse_mode="Markdown")

# 🎭 Commande admin
async def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if str(user_id) == str(ADMIN_ID):
        await update.message.reply_text("👑 Bienvenue, Maître du Chaos ! Que voulez-vous faire aujourd'hui ?")
    else:
        await update.message.reply_text("❌ Tu crois que tu peux être le Joker ? Tu n'es qu'un clown…")

# 📌 Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/predire [équipe1] vs [équipe2] - Prédiction de score façon Joker\n"
        "/stats - Voir le nombre de prédictions restantes\n"
        "/admin - Accès admin (réservé)\n"
        "/help - Afficher cette aide"
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
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("admin", admin))
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
