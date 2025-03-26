import os
import json
import asyncio
import nest_asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread

# Apply nest_asyncio for Render compatibility
nest_asyncio.apply()

# Initialize Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Telegram Bot
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
            "Visit: https://www.moviewave.online/"  # Your original website link maintained
        )
        return

    post_id = unquote(context.args[0]).upper()
    posts = load_posts()
    
    if post_id in posts:
        post = posts[post_id]
        message = f"🎬 *{post['title']}*\n\n🔗 {post['download_url']}"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Invalid link!")

async def main():
    # Start Flask in separate thread
    Thread(target=run_flask, daemon=True).start()
    
    # Start Telegram bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
