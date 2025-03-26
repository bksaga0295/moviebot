import os
import json
import asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.helpers import escape_markdown
from flask import Flask
from threading import Thread

# ================== CONFIGURATION ================== #
DELETE_AFTER_SECONDS = 60  # 5 minutes
MESSAGE_TEMPLATE = """🎬 *{title}*
📅 {date}

🔗 {link}

_This message auto-deletes in {minutes}m_"""
# ==================================================== #

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
    except Exception as e:
        print(f"Error loading posts: {e}")
        return {}

async def delete_message(context: CallbackContext):
    try:
        await context.bot.delete_message(
            chat_id=context.job.chat_id,
            message_id=context.job.message_id
        )
    except Exception as e:
        print(f"Delete error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("🚫 Direct access not allowed!\nVisit: https://www.moviewave.online/")
            return

        # Case-insensitive matching and URL decoding
        raw_id = unquote(context.args[0]).strip().upper()
        posts = load_posts()
        post_id = next((k for k in posts.keys() if k.upper() == raw_id), None)

        if post_id:
            post = posts[post_id]
            message = MESSAGE_TEMPLATE.format(
                title=escape_markdown(post['title'], version=2),
                date=escape_markdown(post.get('date', 'N/A'), version=2),
                link=post['download_url'],
                minutes=DELETE_AFTER_SECONDS // 60
            )
            msg = await update.message.reply_text(message, parse_mode='MarkdownV2')
            context.job_queue.run_once(
                delete_message,
                DELETE_AFTER_SECONDS,
                chat_id=msg.chat_id,
                message_id=msg.message_id
            )
        else:
            await update.message.reply_text("❌ Invalid link! Use buttons from website.")
            
    except Exception as e:
        print(f"Command error: {e}")
        await update.message.reply_text("⚠️ Service temporary unavailable. Try again later.")

async def main():
    # Initialize bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    # Start Flask in separate thread
    Thread(target=run_flask, daemon=True).start()
    
    # Start polling
    await bot_app.initialize()
    await bot_app.start()
    print("Bot is now running...")
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
