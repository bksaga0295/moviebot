import os
import json
import re
import asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.helpers import escape_markdown
from flask import Flask
from threading import Thread

# ================== CONFIGURATION ================== #
DELETE_AFTER_SECONDS = 300  # 5 minutes
POST_ID_PATTERN = re.compile(r'^POST\d+(?:\.\d+)?$', re.IGNORECASE)
MESSAGE_TEMPLATE = """🎬 *{title}*
📅 {date}

🔗 [Download Here]({link})

⚠️ Link expires in {minutes} minutes"""
# ==================================================== #

app = Flask(__name__)

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def load_posts():
    try:
        with open("posts.json", "r") as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if POST_ID_PATTERN.match(k)}
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
            await update.message.reply_text(
                "🚫 Please use the buttons from our website!\n"
                "Visit: https://www.moviewave.online/"
            )
            return

        raw_id = unquote(context.args[0]).strip().upper().replace('%2E', '.')
        posts = load_posts()
        post_id = next(
            (k for k in posts.keys() if k.upper() == raw_id.upper()),
            None
        )

        if post_id:
            post = posts[post_id]
            message = MESSAGE_TEMPLATE.format(
                title=escape_markdown(post['title'], version=2),
                date=escape_markdown(post.get('date', 'N/A'), version=2),
                link=escape_markdown(post['download_url'], version=2),
                minutes=DELETE_AFTER_SECONDS // 60
            )
            
            msg = await update.message.reply_text(
                message, 
                parse_mode='MarkdownV2',
                disable_web_page_preview=True
            )
            
            context.job_queue.run_once(
                delete_message,
                DELETE_AFTER_SECONDS,
                chat_id=msg.chat_id,
                message_id=msg.message_id,
                name=str(msg.message_id)
                
        else:
            await update.message.reply_text(
                "❌ Invalid link detected!\n"
                "Please use only the buttons from our website."
            )
            
    except Exception as e:
        print(f"Command error: {e}")
        await update.message.reply_text(
            "⚠️ Service temporarily unavailable.\n"
            "Our team has been notified. Please try again later."
        )

def main():
    bot_app = Application.builder().token(os.environ['BOT_TOKEN']).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    Thread(target=run_flask, daemon=True).start()
    
    print("Bot starting...")
    bot_app.run_polling()

if __name__ == "__main__":
    main()
