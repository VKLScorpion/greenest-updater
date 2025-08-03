from flask import Flask, request, jsonify
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# ✅ Setup Google Sheets Client
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON", "{}"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = os.getenv("SHEET_ID")
SHEET_TAB_NAME = os.getenv("SHEET_TAB_NAME")

print("✅ Connecting to Sheet ID:", SHEET_ID)
print("📋 Target tab:", SHEET_TAB_NAME)

try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)
except Exception as e:
    print("❌ Could not access sheet:", str(e))
    sheet = None

# 📌 Column headers for microgreens dashboard
DASHBOARD_HEADERS = [
    "Tray Name",
    "Seed Type",
    "Growth %",
    "Health",
    "Days Since Sowing",
    "Est. Harvest",
    "Lighting Stage",
    "Mist Level",
    "Notes",
    "Recommended Action",
    "Environment Flags",
    "Timestamp"
]

def set_headers_if_missing():
    try:
        existing = sheet.row_values(1)
        if existing != DASHBOARD_HEADERS:
            print("⚙️ Updating headers...")
            if existing:
                sheet.delete_row(1)
            sheet.insert_row(DASHBOARD_HEADERS, 1)
    except Exception as e:
        print("⚠️ Header setup failed:", str(e))

def process_and_push(data):
    try:
        print("🔔 Incoming data:", data)
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

        print("📄 Writing row:", row)
        sheet.append_row(row)
        return jsonify({"status": "success", "row": row})
    except Exception as e:
        print("❌ Append failed:", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 500

# 📥 API POST endpoints
@app.route("/push_tray_data", methods=["POST"])
@app.route("/push_data", methods=["POST"])
def push_data():
    data = request.get_json(force=True)
    return process_and_push(data)

# 🟢 Health check
@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "✅ GreeNest Updater is running"}), 200

# 🏁 Launch for local debug
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
