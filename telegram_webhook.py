from flask import Flask, request, jsonify
import os
import requests
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# === Setup: Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = os.getenv("SHEET_ID")
SHEET_TAB_NAME = os.getenv("SHEET_TAB_NAME", "GreeNest Farm Tracker")
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)

# === Telegram Bot Config ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# === Send Telegram Message ===
def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload)
    except Exception as e:
        print("❌ Telegram message failed:", e)

# === Mock Image Analyzer (to be replaced with real ML model) ===
def mock_image_analysis(image_url, tray_name):
    return {
        "tray_name": tray_name,
        "seed_type": "Chia",
        "growth_percent": 92.4,
        "health": 9.1,
        "days_since_sowing": 5,
        "est_harvest": "In 2 days",
        "lighting_stage": "Daylight",
        "mist_level": "Moderate",
        "notes": "Healthy & dense growth",
        "recommended_action": "Harvest tomorrow",
        "environment_flags": "None",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# === Push data to Google Sheet ===
def push_to_sheet(data):
    headers = sheet.row_values(1)
    row = [data.get(h, "N/A") for h in headers]
    sheet.append_row(row)
    print("✅ Row pushed to sheet:", row)

# === Health Check ===
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "📡 Telegram Webhook for GreeNest is active"}), 200

# === Telegram Webhook Endpoint ===
@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    body = request.json
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")

    # Check for image
    if "photo" in message:
        tray_name = message.get("caption", "").strip()
        if not tray_name:
            send_telegram(chat_id, "⚠️ Please send the tray name in the *caption* of the image.")
            return jsonify({"status": "missing_caption"}), 200

        # Get the largest image file
        photo = message["photo"][-1]
        file_id = photo["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        # Analyze tray (mock model for now)
        result = mock_image_analysis(image_url, tray_name)

        # Push to Google Sheet
        push_to_sheet(result)

        # Notify Telegram user
        summary = f"""🌱 *Tray Update*: `{tray_name}`
• *Growth*: {result['growth_percent']}%
• *Health*: {result['health']}
• *Action*: {result['recommended_action']}
• *Time*: {result['timestamp']}"""
        send_telegram(chat_id, summary)

        return jsonify({"status": "image_processed", "tray": tray_name}), 200

    # No image uploaded
    send_telegram(chat_id, "📸 Please upload an image with a tray name as the caption.")
    return jsonify({"status": "no_image"}), 200

# === Run Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
