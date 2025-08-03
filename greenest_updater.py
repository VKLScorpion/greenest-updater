from flask import Flask, request, jsonify
import gspread
import os
import json
import requests
from datetime import datetime
from werkzeug.utils import secure_filename
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = os.getenv("SHEET_ID")
SHEET_TAB_NAME = os.getenv("SHEET_TAB_NAME")

print("✅ Trying to open Sheet ID:", SHEET_ID)
print("✅ Tab name:", SHEET_TAB_NAME)

try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)
except Exception as e:
    print("❌ Failed to access sheet:", str(e))
    sheet = None

# === Telegram Setup ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Dashboard Headers ===
DASHBOARD_HEADERS = [
    "Tray Name", "Seed Type", "Growth %", "Health", "Days Since Sowing",
    "Est. Harvest", "Lighting Stage", "Mist Level", "Notes",
    "Recommended Action", "Environment Flags", "Timestamp"
]

# === Push Telegram Message ===
def send_telegram_message(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        res = requests.post(url, json=payload)
        print(f"📨 Telegram status: {res.status_code}")
    except Exception as e:
        print("❌ Telegram send error:", str(e))

# === Ensure Header Row ===
def set_headers_if_missing():
    try:
        existing = sheet.row_values(1)
        if existing != DASHBOARD_HEADERS:
            print("⚙️ Resetting headers...")
            sheet.delete_row(1) if existing else None
            sheet.insert_row(DASHBOARD_HEADERS, 1)
    except Exception as e:
        print("⚠️ Header setup error:", str(e))

# === Append Tray Data ===
def process_and_push(data):
    try:
        print("🔔 Received payload:", data)
        set_headers_if_missing()

        row = [
            data.get("tray_name", "N/A"),
            data.get("seed_type", "N/A"),
            data.get("growth_percent", "N/A"),
            data.get("health", "N/A"),
            data.get("days_since_sowing", "N/A"),
            data.get("est_harvest", "N/A"),
            data.get("lighting_stage", "N/A"),
            data.get("mist_level", "N/A"),
            data.get("notes", "N/A"),
            data.get("recommended_action", "N/A"),
            data.get("environment_flags", "N/A"),
            data.get("timestamp", "N/A")
        ]

        print("📄 Appending row:", row)
        sheet.append_row(row)

        message = f"""✅ *Tray Update*: `{data.get('tray_name')}`\n• *Seed*: {data.get('seed_type')}\n• *Growth*: {data.get('growth_percent')}%\n• *Health*: {data.get('health')}\n• *Action*: {data.get('recommended_action')}\n• *Notes*: {data.get('notes')}\n• *Time*: {data.get('timestamp')}"""
        send_telegram_message(message)

        return jsonify({"status": "success", "row": row})
    except Exception as e:
        print("❌ Append failed:", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 500

# === Upload Image & Analyze ===
@app.route("/analyze_tray", methods=["POST"])
def analyze_tray():
    try:
        image_file = request.files.get("image")
        tray_name = request.form.get("tray_name", "Unnamed_Tray")

        if not image_file:
            return jsonify({"status": "failed", "error": "No image uploaded"}), 400

        temp_path = os.path.join(tempfile.gettempdir(), secure_filename(image_file.filename))
        image_file.save(temp_path)

        # Simulated ML Analysis
        growth_percent = 90 + hash(tray_name) % 10
        health = 8.0 + hash(temp_path) % 20 / 10
        est_harvest = "Tomorrow"
        notes = "Looks healthy"
        lighting_stage = "Stage 2"
        mist_level = "Medium"
        days_since_sowing = 6 + hash(tray_name) % 3

        row_data = {
            "tray_name": tray_name,
            "seed_type": "Chia" if "Chia" in tray_name else "Mix",
            "growth_percent": growth_percent,
            "health": health,
            "days_since_sowing": days_since_sowing,
            "est_harvest": est_harvest,
            "lighting_stage": lighting_stage,
            "mist_level": mist_level,
            "notes": notes,
            "recommended_action": "Harvest soon" if growth_percent > 95 else "Keep monitoring",
            "environment_flags": "OK",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        set_headers_if_missing()
        sheet.append_row(list(row_data.values()))

        summary = (
            f"🧪 *Tray:* {tray_name}\n"
            f"🌱 Growth: {growth_percent}%\n"
            f"💚 Health: {health}/10\n"
            f"🗓 Days Since Sowing: {days_since_sowing}\n"
            f"🔆 Light: {lighting_stage} | 💧 Mist: {mist_level}\n"
            f"📌 Action: {row_data['recommended_action']}"
        )

        send_telegram_message(summary)
        return jsonify({"status": "success", "summary": summary})

    except Exception as e:
        print("❌ Analysis error:", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 500

# === Flask Routes ===
@app.route("/push_tray_data", methods=["POST"])
@app.route("/push_data", methods=["POST"])
def push_data():
    data = request.json
    return process_and_push(data)

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "✅ GreeNest Flask app is running"}), 200

# === Run Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
