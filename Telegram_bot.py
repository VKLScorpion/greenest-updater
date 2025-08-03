import os
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from io import BytesIO

# Load config
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Should be set to 8386540429:AAFpezbraNgUJgpGkV97dp0jBH-QYkLzwYY
GROUP_CHAT_ID = os.environ.get("TELEGRAM_GROUP_ID")  # Should be -1002115751010
BACKEND_URL = "https://greenest-updater.onrender.com/analyze_tray"

# Handle image + caption
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message.caption:
        await message.reply_text("❗ Please provide the tray name in the image caption.")
        return

    tray_name = message.caption.strip()
    photo_file = await message.photo[-1].get_file()
    photo_bytes = BytesIO()
    await photo_file.download(out=photo_bytes)
    photo_bytes.seek(0)

    # Send image to backend analyzer
    files = {"image": ("tray.jpg", photo_bytes, "image/jpeg")}
    data = {"tray_name": tray_name}

    try:
        response = requests.post(BACKEND_URL, files=files, data=data)
        if response.status_code == 200:
            result = response.json()
            reply = format_analysis(result)
            await message.reply_text(reply)
        else:
            await message.reply_text("❌ Error processing the image. Please try again.")
    except Exception as e:
        await message.reply_text(f"⚠️ Failed to analyze: {str(e)}")

# Format tray analysis summary
def format_analysis(result):
    return f"""
📦 Tray: {result.get('tray_name')}
🌱 Seed: {result.get('seed_type')}
📈 Growth: {result.get('growth_percent')}%
❤️ Health: {result.get('health')}
🕒 Sowing Day: {result.get('days_since_sowing')}
🌞 Light: {result.get('lighting_stage')}
💧 Mist: {result.get('mist_level')}
📝 Notes: {result.get('notes')}
✅ Action: {result.get('recommended_action')}
📅 Time: {result.get('timestamp')}
"""

# Start bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ Telegram bot is running...")
    app.run_polling()
