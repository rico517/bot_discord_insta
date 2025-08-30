import asyncio
import discord
import time
from instagrapi import Client
from dotenv import load_dotenv
import os

# Charger les variables depuis le fichier .env
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
INSTA_USERNAME = os.getenv("INSTA_USERNAME")
INSTA_PASSWORD = os.getenv("INSTA_PASSWORD")

# --- Instagram ---
insta = Client()
insta.login(INSTA_USERNAME, INSTA_PASSWORD)

# --- Discord ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Dictionnaire pour stocker les derniers timestamps par user
last_checked = {}
CHECK_DELAY = 30  # secondes entre 2 checks

async def check_insta_messages():
    """Boucle qui check les nouveaux DMs Instagram et les envoie sur Discord"""
    global last_checked
    while True:
        inbox = insta.direct_threads()
        for thread in inbox:
            for user in thread.users:
                username = user.username
                if username == INSTA_USERNAME:
                    continue  # ignore soi-même

                for msg in thread.messages:
                    ts = msg.timestamp.timestamp()
                    if last_checked.get(username, 0) < ts:
                        channel = client.get_channel(DISCORD_CHANNEL_ID)
                        await channel.send(f"[Insta] **{username}**: {msg.text}")
                        last_checked[username] = ts
        await asyncio.sleep(CHECK_DELAY)

@client.event
async def on_ready():
    print(f"✅ Connecté à Discord en tant que {client.user}")
    client.loop.create_task(check_insta_messages())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Commande reply
    if message.channel.id == DISCORD_CHANNEL_ID and message.content.startswith("!reply "):
        try:
            parts = message.content.split(" ", 2)
            target_username = parts[1].strip()
            text = parts[2].strip()

            user_id = insta.user_id_from_username(target_username)
            insta.direct_send(text, [user_id])
            await message.channel.send(f"📤 Réponse envoyée à **{target_username}** : {text}")
        except Exception as e:
            await message.channel.send(f"⚠️ Erreur: {e}")

# Lancer le bot Discord
client.run(DISCORD_TOKEN)
