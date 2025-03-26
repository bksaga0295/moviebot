import os
import json
import asyncio
import nest_asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
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

# ========== CONFIG ========== #
DELETE_AFTER_MINUTES = 1 # 24 hours (Change this value)
# ============================ #

def load_posts():
    try:
        with open("posts.json", "r") as f:
            return json.load(f)
    except:
        return {}

async def delete_message(context: CallbackContext):
    try:
        await context.bot.delete_message(
            chat_id=context.job.chat_id,
            message_id=context.job.message_id
        )
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🚫 Direct access not allowed!\n\n"
            "Visit: https://www.moviewave.online/"
        )
        return

    raw_id = unquote(context.args[0]).upper()
    posts = load_posts()
    
    if raw_id in posts:
        post = posts[raw_id]
        message = f"🎬 *{post['title']}*\n📅 {post['date']}\n\n"
        
        # Handle multiple links
        if isinstance(post['download_url'], list):
            for i, link in enumerate(post['download_url'], 1):
                message += f"🔗 Part {i}: {link}\n\n"
        else:
            message += f"🔗 {post['download_url']}\n\n"
            
        message += f"_⚠️ Links auto-delete in {DELETE_AFTER_MINUTES//60} hours_"
        
        msg = await update.message.reply_text(message, parse_mode='Markdown')
        
        # Schedule deletion
        context.job_queue.run_once(
            delete_message,
            DELETE_AFTER_MINUTES * 60,
            chat_id=msg.chat_id,
            message_id=msg.message_id
        )
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
