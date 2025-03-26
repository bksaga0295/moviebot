import os
import json
import asyncio
from urllib.parse import unquote
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from telegram.helpers import escape_markdown
from flask import Flask
from threading import Thread
import nest_asyncio

# Apply nest_asyncio to fix event loop conflicts
nest_asyncio.apply()

# ================== CONFIGURATION ================== #
DELETE_AFTER_SECONDS = 60 # 24 hours (in seconds)
PORT = int(os.environ.get('PORT', 10000))
# =================================================== #

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running and ready!"

def run_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=PORT)

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

        raw_id = unquote(context.args[0]).strip().upper()
        posts = load_posts()
        post_id = next((k for k in posts.keys() if k.upper() == raw_id), None)

        if post_id:
            post = posts[post_id]
            minutes = DELETE_AFTER_SECONDS // 60
            hours = minutes // 60
            days = hours // 24
            
            duration = (
                f"{days} day(s)" if days >= 1 else
                f"{hours} hour(s)" if hours >= 1 else
                f"{minutes} minute(s)"
            )
            
            message = f"""🎬 *{escape_markdown(post['title'], version=2)}*
📅 {escape_markdown(post.get('date', 'N/A'), version=2)}

🔗 {post['download_url']}

_This message will auto-delete in {duration}_"""
            
            msg = await update.message.reply_text(message, parse_mode='MarkdownV2')
            context.job_queue.run_once(
                delete_message,
                DELETE_AFTER_SECONDS,
                chat_id=msg.chat_id,
                message_id=msg.message_id
            )
        else:
            await update.message.reply_text("❌ Invalid link! Use only buttons from our website.")
            
    except Exception as e:
        print(f"Command error: {e}")
        await update.message.reply_text("⚠️ Bot is updating. Please try again in 5 minutes.")

async def main():
    # Initialize bot with cleanup
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    # Start Flask in separate thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run bot with proper cleanup
    try:
        print("🤖 Bot is now running and ready!")
        await bot_app.initialize()
        await bot_app.start()
        await bot_app.updater.start_polling()
        await bot_app.updater.idle()
    finally:
        await bot_app.stop()
        await bot_app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
