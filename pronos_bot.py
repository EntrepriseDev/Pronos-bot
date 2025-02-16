import os
import json
import logging
import requests
from flask import Flask, request
from dotenv import load_dotenv  # Importation de dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# 🔑 Chargement des variables d'environnement depuis le fichier .env
load_dotenv()  # Charge les variables d'environnement depuis le fichier .env

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Assure-toi d'avoir stocké cette clé dans ton fichier .env
GPT_API_KEY = os.getenv("GPT_API_KEY")  # Charge la clé GPT depuis la variable d'environnement
WEBHOOK_URL = "https://pronos-bot.onrender.com"

# 📌 Liste des groupes autorisés
SPECIFIC_GROUPS = ["@VpnAfricain"]  # Ajoute d'autres groupes ici
ADMIN_IDS = [5427497623, 987654321]  # Ajoute tes IDs d'admin
GPT_API_URL = "https://api.openai.com/v1/chat/completions"

# 📂 Gestion des fichiers JSON
def load_user_data():
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r") as f:
            return json.load(f)
    return {}

def save_user_data(user_data):
    with open("user_data.json", "w") as f:
        json.dump(user_data, f)

# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        user_data[user_id] = {"paris": 0}
        save_user_data(user_data)

    await update.message.reply_text(
        f"Bienvenue {update.message.from_user.first_name}! 🎉\n"
        "Utilise /predire [équipe1] vs [équipe2] pour obtenir une prédiction.\n"
        "Exemple: /predire PSG vs City"
    )

# 🚨 Vérifier si l'utilisateur est dans un groupe autorisé
async def check_group_membership(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        return True
    for group in SPECIFIC_GROUPS:
        try:
            chat_member = await context.bot.get_chat_member(group, user_id)
            if chat_member.status in ["member", "administrator", "creator"]:
                return True
        except:
            continue
    return False

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    if not await check_group_membership(update, context):
        await update.message.reply_text("⚠️ Tu dois être membre d'un groupe autorisé.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Usage : /predire [équipe1] vs [équipe2]")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Format : /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = match.split(" vs ")
    prompt = f"Prédiction du match {team1} vs {team2} selon les performances récentes."

    headers = {
        "Authorization": f"Bearer {GPT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o",  # Utilisation de GPT-3.5, tu peux choisir un autre modèle comme "gpt-4"
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }

    try:
        response = requests.post(GPT_API_URL, json=data, headers=headers)
        response.raise_for_status()  # Lève une exception en cas d'erreur HTTP
        prediction = response.json()["choices"][0]["message"]["content"].strip()
        await update.message.reply_text(f"🔮 Prédiction : {prediction}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur API GPT : {e}")
        await update.message.reply_text("❌ Erreur avec GPT.")
    except KeyError:
        await update.message.reply_text("❌ Erreur avec le format de la réponse de GPT.")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    paris = user_data.get(user_id, {}).get("paris", 0)
    await update.message.reply_text(f"📊 Tu as utilisé {paris}/15 pronostics aujourd'hui.")

# 🔄 Commande /reset (Admin uniquement)
async def reset(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Commande réservée aux admins.")
        return
    user_data = {}
    save_user_data(user_data)
    await update.message.reply_text("🔄 Toutes les stats ont été réinitialisées !")

# ⚙️ Commande /admin
async def admin(update: Update, context: CallbackContext):
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Commande réservée aux admins.")
        return
    await update.message.reply_text("📌 Commandes Admin :\n/reset - Réinitialiser les stats")

# 📌 Commande /groupes
async def groupes(update: Update, context: CallbackContext):
    await update.message.reply_text(f"📢 Le bot est actif dans : {', '.join(SPECIFIC_GROUPS)}")

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
application.add_handler(CommandHandler("reset", reset))
application.add_handler(CommandHandler("admin", admin))
application.add_handler(CommandHandler("groupes", groupes))

# 🚀 Fonction principale
def main():
    port = int(os.getenv("PORT", 10000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TELEGRAM_BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TELEGRAM_BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
