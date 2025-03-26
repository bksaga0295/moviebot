import os
import json
import asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from flask import Flask
from threading import Thread
import nest_asyncio

nest_asyncio.apply()

# ================== ADJUST TIMER HERE ================== #
DELETE_AFTER_SECONDS = 60  # 1 minute (60), 1 hour (3600), 1 week (604800)
# ======================================================== #

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
            current_posts = json.load(f)
        try:
            with open("old_post.json", "r") as f:
                old_posts = json.load(f)
        except FileNotFoundError:
            old_posts = {}
        return {**old_posts, **current_posts}
    except Exception as e:
        print(f"Error loading posts: {e}")
        return {}

async def delete_message(context: CallbackContext):
    await context.bot.delete_message(
        chat_id=context.job.chat_id,
        message_id=context.job.message_id
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🚫 Direct access not allowed!\n\nVisit: https://www.moviewave.online/")
        return

    post_id = unquote(context.args[0])
    posts = load_posts()
    
    # Send reply message
    msg = await update.message.reply_text(
        posts[post_id]["download_url"] if post_id in posts else "❌ Invalid Link!"
    )

    # Schedule message deletion
    context.job_queue.run_once(
        callback=delete_message,
        when=DELETE_AFTER_SECONDS,
        chat_id=msg.chat_id,
        message_id=msg.message_id,
        name=str(msg.message_id)
    )

async def main():
    Thread(target=run_flask).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
