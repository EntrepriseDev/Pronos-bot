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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
WEBHOOK_URL = "https://pronos-bot.onrender.com"

# 📂 Fichier de stockage des utilisateurs
USER_DATA_FILE = "user_data.json"

# 🔥 Liste des admins (ajoute les ID Telegram des admins ici)
ADMINS = {5427497623, 904367221}

# 📌 Groupes ou canaux obligatoires
REQUIRED_CHANNELS = ["@FreeSurf237_Canal_INTECH", "@PronoScoreExact22", "@pmj78cr6mYBhMTM8"]

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
        json.dump(user_data, f, indent=4)

# 🔄 Initialiser ou mettre à jour les données utilisateur
def get_or_create_user(user_id):
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {"predictions_left": 15}
        save_user_data(user_data)
    return user_data

# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    # Vérification de l'adhésion aux groupes ou canaux obligatoires
    member_status = await check_channel_membership(update.message.from_user.id)

    if not member_status:
        await update.message.reply_text(
            "❌ Tu dois rejoindre les groupes ou canaux suivants pour utiliser ce bot : \n"
            + "\n".join(REQUIRED_CHANNELS) + "\n\n"
            "Clique sur les liens pour rejoindre et réessaie."
        )
        return

    await update.message.reply_text(
        f"🤡🚬Ah, tu es là... Enfin. \n \n *Bienvenue ꧁𓊈𒆜{update.message.from_user.first_name}𒆜𓊉꧂* ! 🎉\n"
        "Tu veux des prédictions ? \n Rejoins-moi dans mon équipe pour des offres spéciales : \n\n"
        "[Free Surf INTECH](https://t.me/FreeSurf237_Canal_INTECH) \n"
        "[1xbet Pronostic/ PariETGagner⚽️ 🔥](https://t.me/PronoScoreExact22) \n"
        "[JK PRONO 🏆](https://t.me/+pmj78cr6mYBhMTM8) \n\n"
        "👁️Pour prédire : /predire [équipe1] vs [équipe2].", 
        parse_mode="Markdown"
    )

# Fonction pour vérifier l'adhésion aux groupes ou canaux obligatoires
async def check_channel_membership(user_id):
    for channel in REQUIRED_CHANNELS:
        response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}")
        if response.status_code == 200:
            data = response.json()
            if data["result"]["status"] not in ["member", "administrator"]:
                return False
    return True

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = get_or_create_user(user_id)

    if int(user_id) not in ADMINS and user_data[user_id]["predictions_left"] <= 0:
        await update.message.reply_text("❌ Plus de prédictions pour aujourd’hui, petit ᶠᶸᶜᵏᵧₒᵤ! 😂 \n Reviens demain, ou deviens admin... HAHAHA!")
        return

    if len(context.args) < 3 or context.args[1].lower() != "vs":
        await update.message.reply_text("🎭 Oh là là ! On dirait que tu as raté le coche, mon petit. 🤡 Tu devrais utiliser : /predire [équipe1] vs [équipe2]. \n \n 🚬C'est comme une blague mal placée, ça ne marche pas sans le bon timing !")
        return

    team1, team2 = context.args[0], context.args[2]
    prompt = f"Imagine que tu es le Joker. Fais une estimation du score final en -100mots avec des emojis que utilise le Joker pour {team1} vs {team2} en tenant compte de leurs performances de 2025 dans le style du Joker sans blaguer avec le score qui doit etre bien analyse"

    try:
        response = co.chat(model="command-r-plus-08-2024", messages=[{"role": "user", "content": prompt}])
        prediction = response.message.content[0].text.strip()
        await update.message.reply_text(f"[Rejoignez la communauté du Joker 🎭](https://t.me/the_jokers_community) \n \n *Le Joker dit* 🃏: {prediction}", parse_mode="Markdown")

        # Réduction du nombre de pronostics restants pour les non-admins
        if user_id not in ADMINS:
            user_data[user_id]["predictions_left"] -= 1
            save_user_data(user_data)

    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une prédiction. Mais qui s'en soucie ? Le chaos continue !")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = get_or_create_user(user_id)
    remaining = "∞" if int(user_id) in ADMINS else user_data[user_id]["predictions_left"]

    await update.message.reply_text(f"🤡 Il te reste {remaining} prédictions aujourd’hui... Amuse-toi bien avant que tout ne s'effondre ! HAHAHA!")

# 👑 Commande /admin (réservé aux admins)
async def admin(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if int(user_id) not in ADMINS:
        await update.message.reply_text("❌ HAHAHA! Tu crois vraiment que tu peux contrôler le chaos ? Accès refusé. 😈 \n /̵͇̿̿/'̿'̿ ̿ ̿̿ ̿̿ ̿̿💥")
        return
    await update.message.reply_text("Bienvenue, maître du chaos ! Tes prédictions sont illimitées ! 🤡👑 HAHAHAHA! \n 「✔ ᵛᵉʳᶦᶠᶦᵉᵈ」")

# 🃏 Commande /joke (blague du Joker)
JOKER_JOKES = [
    "Pourquoi Batman n'aime pas les blagues ? Parce qu'il n'a pas de parents ! HAHAHA !",
    "Tu veux savoir pourquoi je souris toujours ? Parce que ça rend les gens nerveux...",
    "On vit dans une société où le bonheur est un crime, et moi, je suis coupable !",
    "Pourquoi les criminels adorent Gotham ? Parce que la police est plus drôle que moi !",
    "Le rire, c'est comme une maladie... Et moi, je suis le virus !",
    "Ils disent que je suis fou, mais... les fous, c'est eux ! HAHAHA !",
    "Pourquoi Batman n'aime pas les dîners en famille ? Parce qu'il est toujours seul à table !",
    "Un sourire vaut mille mots... Mais une explosion, c'est encore plus expressif !",
    "Tu veux savoir ce qui rend une blague vraiment drôle ? La peur dans tes yeux !",
    "Gotham est ma cour de récréation, et moi, je suis le maître du chaos !",
    # Ajoute d'autres blagues ici
]

async def joke(update: Update, context: CallbackContext):
    await update.message.reply_text(f"🤡 {random.choice(JOKER_JOKES)}")

# 🆘 Commande /help
async def help(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🤡📃Ah, tu veux de l'aide ? C'est amusant, parce que je ne suis pas là pour ça... mais bon :\n\n"
        "/start - Présentation du chaos\n"
        "/predire [équipe1] vs [équipe2] - Demande une prédiction 🎭\n"
        "/stats - Voir ton nombre de prédictions restantes\n"
        "/admin - Vérifier si tu es un maître du chaos 👑\n"
        "/joke - Une blague pour te faire rire... ou pleurer 🚬!"
    )

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
application.add_handler(CommandHandler("help", help))

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
