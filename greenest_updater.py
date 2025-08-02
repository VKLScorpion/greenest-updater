import os
from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import requests

# === CONFIG ===
SHEET_ID = "1-KbaMwtf33eXfYl5BDydEvaCYpPYH3xSYTQc6fCqFT4"
SHEET_TAB_NAME = "GreeNest Farm Tracker"
TELEGRAM_BOT_TOKEN = "8386540429:AAFpezbraNgUJgpGkV97dp0jBH-QYkLzwYY"
TELEGRAM_CHAT_ID = "-1002115751010"  # GreeNest Farms group

# === GOOGLE SHEETS SETUP ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("greenest-farms-7416ab35f7f4.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)

# === FLASK SERVER ===
app = Flask(__name__)

@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "Greenest API Live"}), 200

@app.route("/push_tray_data", methods=["POST"])
def push_data():
    data = request.json
    tray_name = data.get("tray_name")
    growth = data.get("growth", "")
    health = data.get("health", "")
    light = data.get("lighting", "")
    mist = data.get("mist_level", "")
    harvest = data.get("estimated_harvest", "")
    medium = data.get("medium", "")
    notes = data.get("notes", "")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Append to Google Sheet
    row = [timestamp, tray_name, growth, health, light, mist, harvest, medium, notes]
    sheet.append_row(row)

    # Send Telegram message
    message = f"""🌿 *GreeNest Farms – Tray Update*

📅 {timestamp}
🧺 *Tray:* {tray_name}
📈 *Growth:* {growth}
💚 *Health:* {health}
💡 *Lighting:* {light}
💧 *Mist Level:* {mist}
🗓 *Est. Harvest:* {harvest}
🪴 *Medium:* {medium}
📝 *Notes:* {notes}
"""
    send_telegram_message(message)

    return jsonify({"status": "success", "message": "Data pushed"}), 200

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(debug=True)