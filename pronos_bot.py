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
    "Tu connais la différence entre moi et un politicien ? Moi, au moins, j'admets que je suis un monstre !",
    "Si la vie te donne des citrons... Jette-les sur Batman et rigole !",
    "On m'appelle un criminel... Mais qui a mis un homme déguisé en chauve-souris dans une ville pleine de fous ?",
    "Ma santé mentale ? Aussi stable que le pont que j'ai fait exploser hier !",
    "Le chaos est une échelle, mais moi, je préfère le toboggan !",
    "Tu veux entendre une blague sur la justice ? Regarde Batman essayer de m’arrêter encore une fois !",
    "Pourquoi je ris tout le temps ? Parce que c’est plus amusant que pleurer !",
    "Tu veux voir un tour de magie ? Regarde-moi faire disparaître toute la moralité de Gotham !",
    "Pourquoi le Joker ne va jamais en prison ? Parce que c'est bien plus drôle de s'en échapper !",
    "Les psychiatres me disent malade, mais moi, je dis que je suis l’homme le plus sain d’esprit ici !",
    "J'ai proposé un pique-nique à Batman... Il a refusé. Peut-être qu'il n'aime pas les sandwichs à la dynamite ?",
    "La ville de Gotham est comme un cirque... Moi, je suis le clown, et Batman est le lion en cage !",
    "Tu veux savoir pourquoi je peins mon sourire ? Parce que la réalité est trop fade !",
    "Batman dit qu’il est la nuit... Alors moi, je suis l’insomnie !",
    "Quand la vie te donne des ennuis... Transforme-les en blague mortelle !",
    "Pourquoi je porte du violet ? Parce que c’est la couleur du chaos, et moi, j’adore ça !",
    "On dit que la folie est une maladie... Mais moi, je l’appelle liberté !",
    "Tu veux un petit conseil ? Si tu veux survivre à Gotham, apprends à rigoler !",
    "Pourquoi le Joker n'a pas de miroir chez lui ? Parce qu’il préfère voir la peur dans les yeux des autres !",
    "L’argent, c’est surfait… Brûle un tas de billets et regarde la ville paniquer !",
    "Je voulais envoyer un message à Batman... Alors j’ai fait exploser une banque, c’est plus direct !",
    "Pourquoi je mets du rouge à lèvres ? Parce que c’est plus joli quand je souris… et saigne en même temps !",
    "La seule règle à Gotham ? Il n’y a pas de règles, sauf celles que je décide !",
    "Tu veux savoir ce qui est drôle ? Un clown en costard essayant de m’arrêter !",
    "La différence entre moi et Batman ? Moi, je sais m’amuser !",
    "Pourquoi j’adore les fêtes foraines ? Parce que c’est rempli de cris et de lumières… Comme mes plans !",
    "Si tu veux être comme moi, commence par jeter ta moralité à la poubelle !",
    "Les super-héros sont tellement ennuyants… Moi, je rends tout plus amusant !",
    "Pourquoi je n’aime pas les banques ? Parce que l’argent est plus utile en cendres !",
    "Si tu veux comprendre le chaos, arrête d’essayer de le contrôler !",
    "Tu veux voir un vrai tour de magie ? Regarde-moi transformer Gotham en enfer !",
    "Pourquoi le Joker aime les blagues ? Parce que la vie elle-même est une blague !",
    "Batman pense qu'il peut me changer... Il est plus naïf qu'un enfant !",
    "Pourquoi j'adore le gaz hilarant ? Parce que tout est plus beau quand les gens rient... et suffoquent !",
    "Tu veux une anecdote drôle ? J’ai kidnappé un juge hier, et il a crié plus fort que Batman !",
    "Pourquoi la justice est un mensonge ? Parce que c’est moi qui décide du jeu maintenant !",
    "Le crime, c'est comme l’art... Il faut savoir être créatif !",
    "On me dit psychopathe, mais moi, je préfère le terme visionnaire !",
    "Pourquoi les gens ont peur de moi ? Parce qu’ils savent que je ne joue pas avec les mêmes règles qu’eux !",
    "La folie est comme la gravité… Il suffit d’une petite poussée !",
    "Gotham avait besoin d'un héros… Moi, j'ai décidé qu'elle avait besoin d'un monstre !",
    "Pourquoi je laisse Batman en vie ? Parce que sinon, je m’ennuierais !",
    "Quand je rentre dans une pièce, la tension monte… Et les bombes explosent !",
    "La vie est courte… Alors pourquoi ne pas en faire un spectacle explosif ?",
    "Pourquoi je rigole tout le temps ? Parce que sinon, je pleurerais… et ce serait bien moins drôle !",
    "Tu veux voir Gotham brûler ? Reste près de moi, et profite du spectacle !",
    "Pourquoi le Joker ne joue jamais aux échecs ? Parce que je préfère jouer avec les gens qu’avec des pions !",
    "Tu veux un secret ? Les monstres ne se cachent pas sous ton lit… Ils dirigent la ville !",
    "Pourquoi j'aime les jeux vidéo ? Parce qu'on peut toujours recommencer après avoir tout détruit !",
    "On dit que la vengeance est un plat qui se mange froid… Moi, je préfère le servir avec une explosion !",
    "Si la vie est un film, alors moi, je suis le méchant principal !"
]


# 🚀 Commande /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        f"🤡🚬Ah, tu es là... Enfin. Bienvenue {update.message.from_user.first_name} ! 🎉\n"
        "Tu veux des prédictions ? rejoint moi dans mon equipe pour obtenir certaines offres spéciaux: \n https://t.me/FreeSurf237_Canal_INTECH \n https://t.me/+pmj78cr6mYBhMTM8\n"
        "Pour predire: /predire [équipe1] vs [équipe2]."
    )

# 🔮 Commande /predire
async def predict_score(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ Quoi, tu veux prédire sans même savoir de quoi tu parles ?! Utilise le format correct : /predire [équipe1] vs [équipe2] ! HAHAHA!")
        return

    match = " ".join(context.args)
    if "vs" not in match:
        await update.message.reply_text("⚠️ Le chaos ne suit pas de règles, mais même lui sait que tu dois utiliser le format : /predire [équipe1] vs [équipe2].")
        return

    team1, team2 = match.split(" vs ")
    prompt = f"Imagine que tu es le Joker. Fais une estimation du score final en -100mots pour {team1} vs {team2} en tenant compte de leurs performances de cette annee 2025 dans le style du Joker sans blaguer avec le score."

    try:
        response = co.chat(model="command-r-plus-08-2024", messages=[{"role": "user", "content": prompt}])
        prediction = response.message.content[0].text.strip()
        await update.message.reply_text(f"[Rejoignez la communauté du Joker 🎭](https://t.me/the_jokers_community) \n \n 😈 *Le Joker dit* : {prediction}", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Erreur avec Cohere : {e}")
        await update.message.reply_text("❌ Impossible d'obtenir une prédiction. Mais qui s'en soucie ? Le chaos continue !")

# 📊 Commande /stats
async def stats(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    user_data = load_user_data()
    remaining = user_data.get(user_id, {}).get("predictions_left", 15)
    await update.message.reply_text(f"🤡 Il te reste {remaining} prédictions aujourd'hui... Comme si ça allait vraiment changer quelque chose. N'oublie pas, l'important, c'est de s'amuser avant que tout ne s'effondre ! HAHAHA!")

# 👑 Commande /admin (réservé aux admins)
async def admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("❌❌❌ HAHAHA! Tu crois vraiment que tu peux contrôler le chaos ? Accès refusé. 😈")
        return
    await update.message.reply_text("Bienvenue, Oui vous êtes un de mes chers administrateurs. Le chaos nous attends maître 🤡👑 HAHAHAHA!")

# 🃏 Commande /joke (blague du Joker)
async def joke(update: Update, context: CallbackContext):
    joke = random.choice(JOKER_JOKES)
    await update.message.reply_text(f"🤡 {joke}")

# 🆘 Commande /help (aide du Joker)
async def help(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "🤡📃Oh, tu veux de l'aide ? C'est amusant, parce que je ne suis pas là pour t'aider... mais bon, voici ce que tu peux faire :\n\n"
        "/start - Bienvenue, cher visiteur !\n"
        "/predire [équipe1] vs [équipe2] - Si tu veux des prédictions... \n"
        "/stats - Voir combien de prédictions il te reste... mais tu sais, tu as 15 prédictions/jrs😈 !\n"
        "/admin - Pour les élus, les contrôleurs du chaos... Si tu as ce privilège 👑 !\n"
        "/joke - Une petite blague pour égayer ta journée... Si tu penses que tu peux encore rire après tout ça 🚬!"
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
