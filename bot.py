import os
import json
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread
import nest_asyncio  # Add this line

# Allow nested event loops
nest_asyncio.apply()

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

BOT_TOKEN = os.environ['BOT_TOKEN']

def load_posts():
    try:
        with open("posts.json", "r") as f:
            return json.load(f)
    except:
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🚫 Direct access not allowed!\n\n"
            "Visit our website:\nhttps://www.moviewave.online/"
        )
        return

    post_id = context.args[0].upper()
    posts = load_posts()
    await update.message.reply_text(
        posts[post_id]["download_url"] if post_id in posts else "❌ Invalid Link!"
    )

async def main():
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    
    # Start Telegram bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
