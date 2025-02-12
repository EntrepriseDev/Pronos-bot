import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import openai
import json
import os
from flask import Flask, request

# Clé API OpenAI 
openai.api_key = "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"  # Remplacez par votre clé API

# Charger les données des utilisateurs à partir de 'user_data.json'
def load_user_data():
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as f:
            return json.load(f)
    return {}

# Sauvegarder les données des utilisateurs dans 'user_data.json'
def save_user_data(user_data):
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

# Fonction pour prédire le score d'un match via OpenAI
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /predire [équipe1] vs [équipe2]")
        return

    team1 = context.args[0]
    team2 = context.args[1]
    
    # Demander à OpenAI une prédiction de score
    prompt = f"Prédisez le score final pour le match {team1} vs {team2}. Prédiction de score :"
    
    try:
        response = openai.Completion.create(
            model="text-davinci-003",  # Utilisation de GPT-3
            prompt=prompt,
            max_tokens=50
        )
        
        prediction = response.choices[0].text.strip()
        await update.message.reply_text(f"Prédiction pour {team1} vs {team2}: {prediction}")
    
    except Exception as e:
        logging.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
        await update.message.reply_text("Une erreur s'est produite lors de la prédiction du score. Essayez à nouveau.")

# Fonction pour démarrer le bot
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = load_user_data()
    
    # Vérifier si l'utilisateur existe dans les données
    if user_id not in user_data:
        user_data[user_id] = {'paris': 0}  # Initialisation du solde de paris
        save_user_data(user_data)
    
    await update.message.reply_text(f"Bienvenue, {update.message.from_user.first_name}! Utilisez /predire [équipe1] vs [équipe2] pour obtenir une prédiction de score.")

# Fonction pour gérer les paris
async def bet(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = load_user_data()

    # Vérifier si l'utilisateur a un solde
    if user_id not in user_data or user_data[user_id]['paris'] <= 0:
        await update.message.reply_text("Vous n'avez pas de paris disponibles. Utilisez /predire pour faire des prédictions.")
        return

    # Gérer le pari
    bet_amount = int(context.args[0]) if context.args else 0
    if bet_amount <= 0:
        await update.message.reply_text("Veuillez spécifier un montant de pari valide.")
        return

    user_data[user_id]['paris'] -= bet_amount
    save_user_data(user_data)

    await update.message.reply_text(f"Vous avez parié {bet_amount} sur ce match!")

# Fonction pour afficher le solde de paris de l'utilisateur
async def balance(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_data = load_user_data()
    
    if user_id not in user_data:
        await update.message.reply_text("Vous n'avez pas encore de solde.")
        return
    
    balance = user_data[user_id].get('paris', 0)
    await update.message.reply_text(f"Votre solde de paris : {balance} points.")

# Fonction pour réinitialiser le solde de paris (réservée à l'admin)
async def reset(update: Update, context: CallbackContext):
    admin_id = "votre_id_admin"  # Remplacez par votre ID Telegram
    if update.message.from_user.id != admin_id:
        await update.message.reply_text("Vous n'avez pas les droits pour utiliser cette commande.")
        return
    
    user_data = load_user_data()
    for user in user_data.values():
        user['paris'] = 0
    save_user_data(user_data)

    await update.message.reply_text("Tous les soldes ont été réinitialisés.")

# Fonction pour afficher l'aide
async def help(update: Update, context: CallbackContext):
    help_text = """
    Commandes disponibles :
    /start - Démarrer le bot
    /predire [équipe1] vs [équipe2] - Obtenez une prédiction de score
    /parier [montant] - Pariez un certain montant sur un match
    /solde - Afficher votre solde de paris
    """
    await update.message.reply_text(help_text)

# Configuration du logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask application
app = Flask(__name__)

# Fonction principale pour démarrer le serveur et le bot avec Webhook
def main():
    """Démarre le bot avec un webhook"""
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Ajouter les gestionnaires de commandes
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("predire", predict_score))
    application.add_handler(CommandHandler("parier", bet))
    application.add_handler(CommandHandler("solde", balance))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CommandHandler("help", help))

    # Définir l'URL du webhook
    webhook_url = "https://your-server.com/YOUR_BOT_TOKEN"

    # Lancer le webhook
    application.start_webhook(listen="0.0.0.0", port=10000, url_path="7935826757:AAFKEABJCDLbm891KDIkVBgR2AaEBkHlK4M")
    application.bot.set_webhook(url=webhook_url)

    # Lancer l'application Flask
    app.run(host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
