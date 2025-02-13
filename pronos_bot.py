import logging
import os
import json
import openai
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# 🔒 Charger les clés de sécurité depuis les variables d'environnement
openai.api_key = "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"
BOT_TOKEN = "7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M"

# Vérification des clés 🔴 (Supprimez ce print en production)
if not openai.api_key or not BOT_TOKEN:
    print("⚠️ ERREUR : Clés API manquantes ! Définissez les variables d'environnement.")

# Charger/Sauvegarder les données des utilisateurs
def load_user_data():
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as f:
            return json.load(f)
    return {}

def save_user_data(user_data):
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

# Prédiction via OpenAI
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /predire [équipe1] vs [équipe2]")
        return

    team1, team2 = context.args[:2]
    prompt = f"Prédisez le score final pour le match {team1} vs {team2}."

    try:
        response = openai.Completion.create(model="text-davinci-003", prompt=prompt, max_tokens=50)
        prediction = response.choices[0].text.strip()
        await update.message.reply_text(f"Prédiction {team1} vs {team2}: {prediction}")
    except Exception as e:
        logging.error(f"Erreur OpenAI: {e}")
        await update.message.reply_text("Erreur lors de la prédiction.")

# Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()

    if user_id not in user_data:
        user_data[user_id] = {'paris': 0}
        save_user_data(user_data)

    await update.message.reply_text(f"Bienvenue {update.message.from_user.first_name} ! Utilisez /predire pour obtenir des prédictions.")

# Commande /solde
async def balance(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    solde = user_data.get(user_id, {}).get('paris', 0)
    await update.message.reply_text(f"Votre solde de paris : {solde} points.")

# 🔥 Création de l'application Telegram
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# Ajout des handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("predire", predict_score))
application.add_handler(CommandHandler("solde", balance))

# Webhook Telegram
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.process_update(update)
    return "OK", 200

# Démarrer l'application Flask
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000)
