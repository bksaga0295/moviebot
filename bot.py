import os
import json
import asyncio
import nest_asyncio
from urllib.parse import unquote
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
from flask import Flask
from threading import Thread

nest_asyncio.apply()

# ========== CONFIGURATION ========== #
DELETE_AFTER_HOURS = 24
PORT = 10000
# =================================== #

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

BOT_TOKEN = os.environ['BOT_TOKEN']

def load_posts():
    try:
        with open("posts.json", "r") as f:
            current = json.load(f)
        
        old_posts = {}
        try:
            with open("old_post.json", "r") as f:
                old_posts = json.load(f)
        except FileNotFoundError:
            pass

        cutoff = datetime.now().timestamp() - (7 * 86400)
        moved = []
        
        for pid in list(current.keys()):
            try:
                post_time = datetime.strptime(current[pid]["date"], "%Y-%m-%d").timestamp()
                if post_time < cutoff:
                    old_posts[pid] = current.pop(pid)
                    moved.append(pid)
            except:
                continue

        if moved:
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

        post_id = unquote(context.args[0]).strip().upper()
        posts = load_posts()
        
        if post_id in posts:
            post = posts[post_id]
            keyboard = []
            
            # Direct open links without confirmation
            if isinstance(post['download_url'], dict):
                for btn_text, url in post['download_url'].items():
                    keyboard.append([InlineKeyboardButton(
                        text=btn_text,
                        url=url,
                        callback_data="dummy"  # Bypass confirmation
                    )])
            elif isinstance(post['download_url'], list):
                for i, url in enumerate(post['download_url'], 1):
                    keyboard.append([InlineKeyboardButton(
                        text=f"Part {i}",
                        url=url,
                        callback_data="dummy"
                    )])
            else:
                keyboard.append([InlineKeyboardButton(
                    text="Download Now",
                    url=post['download_url'],
                    callback_data="dummy"
                )])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"🎬 *{post['title']}*\n"
                f"📅 {post['date']}\n\n"
                f"_⏳ Auto-deletes in {DELETE_AFTER_HOURS} hours_"
            )
            
            sent_msg = await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            context.job_queue.run_once(
                delete_message,
                DELETE_AFTER_HOURS * 3600,
                chat_id=sent_msg.chat_id,
                message_id=sent_msg.message_id
            )
        else:
            await update.message.reply_text("❌ Invalid link! Use website buttons.")
            
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ Temporary service issue. Try again later.")

async def main():
    Thread(target=run_flask, daemon=True).start()
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
