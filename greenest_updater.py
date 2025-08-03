from flask import Flask, request, jsonify
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Setup Google Sheets API client
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

def process_and_push(data):
    try:
        print("🔔 Updater received payload:", data)

        row = [
            data.get("tray_name", "N/A"),
            data.get("seed_type", "N/A"),
            data.get("growth_percent", "N/A"),
            data.get("health_score", "N/A"),
            data.get("notes", "N/A"),
            data.get("recommended_action", "N/A"),
            data.get("environment_flags", "N/A"),
            data.get("timestamp", "N/A")
        ]

        print("📄 Appending row:", row)
        sheet.append_row(row)
        return jsonify({"status": "success", "row": row})

    except Exception as e:
        print("❌ Error while appending:", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/push_tray_data", methods=["POST"])
def push_data():
    data = request.json
    return process_and_push(data)

@app.route("/push_data", methods=["POST"])
def push_data_alias():
    data = request.json
    return process_and_push(data)

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "✅ GreeNest Flask app is running"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
