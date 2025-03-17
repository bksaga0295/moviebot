import os
import json
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread
import nest_asyncio

nest_asyncio.apply()  # Fix event loop issues

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

BOT_TOKEN = os.environ['BOT_TOKEN']

def load_posts():
    try:
        # Load current posts
        with open("posts.json", "r") as f:
            current_posts = json.load(f)
        
        # Load old posts (if file exists)
        try:
            with open("old_post.json", "r") as f:
                old_posts = json.load(f)
        except FileNotFoundError:
            old_posts = {}
        
        # Merge both (current posts override old ones)
        return {**old_posts, **current_posts}
        
    except Exception as e:
        print(f"Error loading posts: {e}")
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🚫 Direct access not allowed!\n\n"
            "Visit: https://www.moviewave.online/"
        )
        return

    post_id = context.args[0].upper()
    posts = load_posts()
    await update.message.reply_text(
        posts[post_id]["download_url"] if post_id in posts else "❌ Invalid Link!"
    )

async def main():
    Thread(target=run_flask).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
