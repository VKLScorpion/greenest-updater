import os
import requests
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
BACKEND_URL = os.getenv("GSHEET_BACKEND_URL", "https://greenest-updater.onrender.com/analyze_tray")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message.photo:
            await update.message.reply_text("❌ No image found. Please upload a tray image.")
            return

        tray_name = update.message.caption or "Unnamed_Tray"
        photo = update.message.photo[-1]  # Get highest resolution

        # Download the image file
        file = await photo.get_file()
        file_path = f"/tmp/{file.file_id}.jpg"
        await file.download_to_drive(file_path)

        # Send image + tray_name to backend
        with open(file_path, "rb") as img:
            files = {"image": img}
            data = {"tray_name": tray_name}
            res = requests.post(BACKEND_URL, data=data, files=files)

        if res.status_code == 200:
            reply = res.json().get("summary") or "✅ Image processed and data pushed to sheet."
        else:
            reply = f"❌ Backend error: {res.text}"

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    print("✅ Telegram bot running...")
    app.run_polling()
