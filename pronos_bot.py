import os
import json
import logging
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext
)

# ⚠️ Clés API
TELEGRAM_BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"
MISTRAL_API_KEY = "fmoYHJAndvZ46SntHcmO8ow7YdNHlcxp" 
WEBHOOK_URL = "https://pronos-bot.onrender.com"

# 📂 Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# 🔥 URL de l'API Mistral
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

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
        "Exemple: /predire PSG vs City\n"
        "Autres commandes utiles : /stats, /derniers"
    )

# 🔮 Commande /predire (Prédiction de score avec Mistral AI)
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage correct : /predire [équipe1] vs [équipe2]")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Utilise le format correct : /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = map(str.strip, match.split("vs"))
    prompt = f"Donne une estimation du score final de ce match en 2024-2025: {team1} vs {team2}"

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "pixtral-12b-2409", "messages": [{"role": "user", "content": prompt}], "max_tokens": 600, "temperature": 0.7}

    try:
        response = requests.post(MISTRAL_API_URL, json=data, headers=headers)
        if response.status_code == 200:
            prediction = response.json()["choices"][0]["message"]["content"].strip()
            await update.message.reply_text(f"🔮 Prédiction : {prediction}")
        else:
            logger.error(f"Erreur API Mistral : {response.status_code} - {response.text}")
            await update.message.reply_text("❌ Erreur lors de la récupération de la prédiction.")
    except Exception as e:
        logger.error(f"Erreur API Mistral : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une réponse.")

# 📊 Commande /stats (Afficher les statistiques des prédictions)
async def stats(update: Update, context: CallbackContext):
    user_data = load_user_data()
    total_users = len(user_data)
    total_predictions = sum(len(data.get("predictions", [])) for data in user_data.values())
    await update.message.reply_text(
        f"📊 Statistiques du bot :\n"
        f"👥 Utilisateurs : {total_users}\n"
        f"🔮 Prédictions générées : {total_predictions}"
    )

# 🕰️ Commande /derniers (Afficher les dernières prédictions de l'utilisateur)
async def last_predictions(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data().get(user_id, {}).get("predictions", [])
    if not user_data:
        await update.message.reply_text("🔍 Aucune prédiction trouvée.")
        return
    latest = "\n".join(user_data[-5:])  # Dernières 5 prédictions
    await update.message.reply_text(f"🕰️ Dernières prédictions :\n{latest}")

# 📌 Commande /help
async def help_command(update: Update, context: CallbackContext):
    help_text = (
        "📌 Commandes disponibles :\n"
        "/start - Démarrer le bot\n"
        "/predire [équipe1] vs [équipe2] - Prédiction de score\n"
        "/stats - Afficher les statistiques du bot\n"
        "/derniers - Voir les dernières prédictions\n"
    )
    await update.message.reply_text(help_text)

# 🚀 Application Flask
app = Flask(__name__)
@app.route("/", methods=["GET"])
def home():
    return "✅ Bot Telegram en cours d'exécution !", 200

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
application.add_handler(CommandHandler("derniers", last_predictions))
application.add_handler(CommandHandler("help", help_command))

# 🚀 Fonction principale
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
