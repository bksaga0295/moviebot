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
from waitress import serve

nest_asyncio.apply()

# ========== CONFIGURATION ========== #
DELETE_AFTER_HOURS = 24  # Auto-delete time (change here)
PORT = int(os.environ.get('PORT', 10000))
# =================================== #

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    serve(app, host='0.0.0.0', port=PORT)

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

        # Auto-clean old posts
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
            msg = [
                f"🎬 *{post['title']}*",
                f"📅 {post['date']}",
                "\n📥 Download Links:"
            ]
            
            # Handle all link formats
            links = post['download_url']
            if isinstance(links, dict):
                for name, url in links.items():
                    msg.append(f"➤ {name}: {url}")
            elif isinstance(links, list):
                for i, url in enumerate(links, 1):
                    msg.append(f"🔗 Part {i}: {url}")
            else:
                msg.append(f"🔗 {links}")
            
            msg.append(f"\n_⏳ Auto-deletes in {DELETE_AFTER_HOURS} hours_")
            
            sent_msg = await update.message.reply_text("\n".join(msg), parse_mode='Markdown')
            
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
    # Stop any existing instances
    await Application.builder().token(BOT_TOKEN).build().stop()
    
    # Initialize new bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    
    # Start production server
    Thread(target=run_flask, daemon=True).start()
    
    print("🤖 Bot started successfully!")
    await bot_app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
