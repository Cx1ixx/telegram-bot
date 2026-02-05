import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import yt_dlp
import logging

# 🔐 Set your token as environment variable for security
BOT_TOKEN = os.getenv("8502968935:AAHy31hXNv1391hNKAGeThwjfCck282jZ7Y", "8502968935:AAHy31hXNv1391hNKAGeThwjfCck282jZ7Y")  # Use environment variable

# ✅ Your channel (make sure it's a valid public channel)
CHANNEL_USERNAME = "@zonexdevelopment_socialmedia_bot"  # Replace with actual channel username

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- CHECK CHANNEL MEMBERSHIP ----------------
async def is_user_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False

# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    
    logger.info(f"User {user_id} (@{user_name}) started the bot")
    
    try:
        if not await is_user_member(user_id, context):
            await update.message.reply_text(
                f"🚫 To use this bot, you must join our channel first:\n\n"
                f"{CHANNEL_USERNAME}\n\n"
                "After joining, press /start again."
            )
            return

        await update.message.reply_text(
            "✅ Welcome!\n\n"
            "📥 Send any social media video link (YouTube, Instagram, Twitter, TikTok, etc.) to download.\n\n"
            "⚠️ Please note: Some platforms may have restrictions."
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")

# ---------------- VIDEO DOWNLOAD ----------------
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    logger.info(f"User {user_id} requested download for: {url}")
    
    # Check if it's a URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return

    try:
        # 🔒 Check membership
        if not await is_user_member(user_id, context):
            await update.message.reply_text(
                "🚫 You are not a member of our channel.\n\n"
                f"Please join first:\n{CHANNEL_USERNAME}"
            )
            return

        await update.message.reply_text("⏳ Downloading, please wait...")

        ydl_opts = {
            "format": "best",
            "outtmpl": f"downloads/{user_id}_%(title)s.%(ext)s",
            "noplaylist": True,
            "quiet": False,
            "no_warnings": False,
            "extract_flat": False,
        }

        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)
            
            # Ensure the file exists before sending
            if os.path.exists(file_name):
                # Check file size (Telegram has a 50MB limit for bots)
                file_size = os.path.getsize(file_name)
                if file_size > 50 * 1024 * 1024:  # 50MB limit
                    await update.message.reply_text(
                        f"❌ File is too large ({file_size/1024/1024:.1f}MB). "
                        "Telegram bot limit is 50MB."
                    )
                    os.remove(file_name)
                    return
                
                # Send the video
                with open(file_name, "rb") as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"✅ Downloaded successfully!\nTitle: {info.get('title', 'Unknown')}"
                    )
                
                # Clean up
                os.remove(file_name)
                logger.info(f"Video sent successfully to user {user_id}")
            else:
                await update.message.reply_text("❌ Download failed. File not found.")
                
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("❌ Download failed. The link might be invalid or private.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

# ---------------- MAIN ----------------
def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set your BOT_TOKEN as an environment variable!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    logger.info("✅ Bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()