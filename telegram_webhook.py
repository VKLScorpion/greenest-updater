# telegram_webhook.py (with real Hugging Face model integration)

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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TRIGGER_SECRET = os.getenv("TRIGGER_SECRET")
HF_INFERENCE_API = os.getenv("HF_INFERENCE_API")  # Hugging Face Inference Endpoint URL

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

# === Real Image Analyzer via Hugging Face ===
def analyze_tray_real(image_url, tray_name):
    try:
        response = requests.post(
            HF_INFERENCE_API,
            json={"image_url": image_url, "tray_name": tray_name},
            timeout=60
        )
        return response.json()
    except Exception as e:
        print("❌ Analysis failed:", e)
        return {
            "tray_name": tray_name,
            "seed_type": "N/A",
            "growth_percent": "N/A",
            "health": "N/A",
            "days_since_sowing": "N/A",
            "est_harvest": "N/A",
            "lighting_stage": "N/A",
            "mist_level": "N/A",
            "notes": "Analysis failed",
            "recommended_action": "Check manually",
            "environment_flags": "Error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# === Push data to Google Sheet ===
def push_to_sheet(data):
    headers = sheet.row_values(1)
    row = [data.get(h, "N/A") for h in headers]
    sheet.append_row(row)
    print("✅ Row pushed to sheet:", row)

# === Build Dashboard Summary ===
def build_dashboard_summary():
    data = sheet.get_all_records()
    grouped = {}
    for row in data:
        tray = row.get("Tray Name", "Unknown")
        if tray not in grouped:
            grouped[tray] = []
        grouped[tray].append(row)

    summary = "📊 *Daily Microgreens Summary*\n\n"
    for tray, entries in grouped.items():
        latest = entries[-1]
        summary += f"""🌱 `{tray}`\n• Growth: {latest['Growth %']}%\n• Health: {latest['Health']}\n• Action: {latest['Recommended Action']}\n• Time: {latest['Timestamp']}\n\n"""

    return summary

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

    if "photo" in message:
        tray_name = message.get("caption", "").strip()
        if not tray_name:
            send_telegram(chat_id, "⚠️ Please send the tray name in the *caption* of the image.")
            return jsonify({"status": "missing_caption"}), 200

        photo = message["photo"][-1]
        file_id = photo["file_id"]
        file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}").json()
        file_path = file_info["result"]["file_path"]
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        result = analyze_tray_real(image_url, tray_name)
        push_to_sheet(result)

        summary = f"""🌱 *Tray Update*: `{tray_name}`\n• *Growth*: {result['growth_percent']}%\n• *Health*: {result['health']}\n• *Action*: {result['recommended_action']}\n• *Time*: {result['timestamp']}"""
        send_telegram(chat_id, summary)

        return jsonify({"status": "image_processed", "tray": tray_name}), 200

    elif message.get("text", "").strip().lower() == "/summary":
        summary = build_dashboard_summary()
        send_telegram(chat_id, summary)
        return jsonify({"status": "summary_sent"}), 200

    send_telegram(chat_id, "📸 Please upload an image with a tray name as the caption.")
    return jsonify({"status": "no_image"}), 200

# === Summary Trigger Endpoint (for GitHub Actions or cron) ===
@app.route("/trigger_summary", methods=["POST"])
def trigger_summary():
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {TRIGGER_SECRET}":
        return jsonify({"status": "unauthorized"}), 403

    summary = build_dashboard_summary()
    send_telegram(TELEGRAM_CHAT_ID, summary)
    return jsonify({"status": "summary_sent"}), 200

# === Run Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
