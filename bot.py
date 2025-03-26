import os
import json
import asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.helpers import escape_markdown  # Added for safety
from flask import Flask
from threading import Thread
import nest_asyncio

nest_asyncio.apply()

# ================== CUSTOMIZE BELOW ================== #
DELETE_AFTER_SECONDS = 300  # 5 minutes (300 sec)
MESSAGE_TEMPLATE = """🎬 *{title}*

🔗 {link}

_This message auto-deletes in {minutes}m_"""
# ====================================================== #

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
    
    if post_id in posts:
        post = posts[post_id]
        # Safe formatting with escaped special characters
        message = MESSAGE_TEMPLATE.format(
            title=escape_markdown(post['title'], version=2),
            date=escape_markdown(post.get('date', 'N/A'), version=2),
            link=post['download_url'],
            minutes=DELETE_AFTER_SECONDS // 60
        )
    else:
        message = "❌ Invalid link! Use only website buttons."

    msg = await update.message.reply_text(message, parse_mode='MarkdownV2')
    
    if post_id in posts:  # Only schedule deletion for valid links
        context.job_queue.run_once(
            callback=delete_message,
            when=DELETE_AFTER_SECONDS,
            chat_id=msg.chat_id,
            message_id=msg.message_id
        )

async def main():
    Thread(target=run_flask).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
