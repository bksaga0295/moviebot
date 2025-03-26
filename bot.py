import os
import json
import asyncio
import nest_asyncio
from urllib.parse import unquote
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from flask import Flask
from threading import Thread

nest_asyncio.apply()

app = Flask(__name__)

# ========== CONFIG ========== #
DELETE_AFTER_HOURS = 24  # Auto-delete timer (change here)
PORT = 10000
# ============================ #

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

BOT_TOKEN = os.environ['BOT_TOKEN']

def load_posts():
    try:
        # Load and auto-clean old posts
        with open("posts.json", "r") as f:
            current = json.load(f)
            
        old_posts = {}
        try:
            with open("old_post.json", "r") as f:
                old_posts = json.load(f)
        except FileNotFoundError:
            pass

        # Move posts older than 7 days
        today = datetime.now()
        to_move = []
        for pid in list(current.keys()):
            post_date = datetime.strptime(current[pid]["date"], "%Y-%m-%d")
            if (today - post_date).days > 7:
                old_posts[pid] = current.pop(pid)
                to_move.append(pid)

        if to_move:
            with open("old_post.json", "w") as f:
                json.dump(old_posts, f)
            with open("posts.json", "w") as f:
                json.dump(current, f)

        return {**old_posts, **current}
        
    except Exception as e:
        print(f"Post error: {e}")
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
    try:
        if not context.args:
            await update.message.reply_text("🚫 Direct access not allowed!\nVisit: https://www.moviewave.online/")
            return

        post_id = unquote(context.args[0]).upper()
        posts = load_posts()
        
        if post_id in posts:
            post = posts[post_id]
            msg_content = f"🎬 *{post['title']}*\n📅 {post['date']}\n\n"
            
            # Handle multiple links
            if isinstance(post['download_url'], list):
                for i, link in enumerate(post['download_url'], 1):
                    msg_content += f"🔗 Part {i}: {link}\n\n"
            elif isinstance(post['download_url'], dict):
                for name, link in post['download_url'].items():
                    msg_content += f"➤ {name}: {link}\n\n"
            else:
                msg_content += f"🔗 {post['download_url']}\n\n"
            
            msg_content += f"_⏳ Auto-deletes in {DELETE_AFTER_HOURS} hours_"
            
            msg = await update.message.reply_text(msg_content, parse_mode='Markdown')
            
            # Schedule deletion
            context.job_queue.run_once(
                delete_message,
                DELETE_AFTER_HOURS * 3600,
                chat_id=msg.chat_id,
                message_id=msg.message_id
            )
        else:
            await update.message.reply_text("❌ Invalid link!")
            
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ Temporary error. Try again!")

async def main():
    Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
