import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

# Get token from Koyeb environment variable
BOT_TOKEN = os.getenv("8502968935:AAHbjrbbpj3MkydJMabiKT1VOtjQ5JpEDtM")

# Setup logging for Koyeb
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store active downloads to prevent multiple requests
active_downloads = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    await update.message.reply_text(
        "🤖 **Video Download Bot**\n\n"
        "✅ Hosted 24/7 on Koyeb\n\n"
        "📥 Send me any video link from:\n"
        "• YouTube\n• Instagram\n• TikTok\n• Twitter/X\n• Facebook\n\n"
        "I'll download and send it to you!\n\n"
        "⚠️ Max file size: 50MB (Telegram limit)"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    await update.message.reply_text(
        "📖 **Help**\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n\n"
        "How to use:\n"
        "1. Send me any video URL\n"
        "2. I'll download it\n"
        "3. I'll send the video back to you\n\n"
        "Supported sites:\n"
        "YouTube, Instagram, TikTok, Twitter, Facebook, Reddit, etc."
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Download video from URL"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    # Check if user already has active download
    if user_id in active_downloads:
        await update.message.reply_text("⏳ Please wait for your current download to finish...")
        return
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return
    
    # Check if it's a known video platform
    video_domains = ['youtube.com', 'youtu.be', 'instagram.com', 'tiktok.com', 'twitter.com', 'x.com', 'facebook.com']
    if not any(domain in url for domain in video_domains):
        await update.message.reply_text("⚠️ This might not be a supported video site. Trying anyway...")
    
    try:
        # Mark user as downloading
        active_downloads[user_id] = True
        
        await update.message.reply_text("⏳ Downloading your video... This may take a moment.")
        
        # YouTube DL configuration
        ydl_opts = {
            'format': 'best[filesize<50M]',  # Telegram max 50MB
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': True,
        }
        
        # Create downloads directory
        os.makedirs("downloads", exist_ok=True)
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'video')
            
            # Check file size
            formats = info.get('formats', [])
            best_format = None
            for fmt in formats:
                filesize = fmt.get('filesize') or fmt.get('filesize_approx')
                if filesize and filesize < 50 * 1024 * 1024:  # 50MB limit
                    best_format = fmt
                    break
            
            if not best_format:
                await update.message.reply_text("❌ Video is too large (over 50MB). Try a shorter video.")
                return
            
            # Download the video
            ydl.download([url])
            
            # Find downloaded file
            video_id = info.get('id', 'video')
            ext = best_format.get('ext', 'mp4')
            filename = f"downloads/{video_id}.{ext}"
            
            if os.path.exists(filename):
                # Send video
                with open(filename, 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"✅ {video_title}",
                        supports_streaming=True
                    )
                
                # Clean up
                os.remove(filename)
                logger.info(f"✅ Video sent to user {user_id}")
            else:
                await update.message.reply_text("❌ Download failed. File not found.")
        
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        await update.message.reply_text("❌ Could not download video. Link might be private or invalid.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again.")
    finally:
        # Remove user from active downloads
        active_downloads.pop(user_id, None)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown commands"""
    await update.message.reply_text("❌ Unknown command. Send /help for instructions.")

def main():
    """Main function to run the bot"""
    # Check if BOT_TOKEN is set
    if not BOT_TOKEN:
        logger.error("❌ ERROR: BOT_TOKEN environment variable is not set!")
        logger.error("Please set BOT_TOKEN in Koyeb dashboard → Environment Variables")
        return
    
    logger.info("🚀 Starting Telegram Video Download Bot on Koyeb...")
    logger.info(f"Bot token: {BOT_TOKEN[:10]}...")  # Log first 10 chars only
    
    try:
        # Create bot application
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
        app.add_handler(MessageHandler(filters.COMMAND, unknown))
        
        # Start the bot
        logger.info("🤖 Bot is now running...")
        logger.info("Press Ctrl+C to stop")
        
        app.run_polling(
            drop_pending_updates=True,
            timeout=30,
            pool_timeout=30,
            connect_timeout=30,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        # Wait before restart (Koyeb will auto-restart)
        asyncio.sleep(5)

if __name__ == "__main__":
    main()

