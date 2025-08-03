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

sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)

def process_and_push(data):
    try:
        row = [
            data.get("tray_name"),
            data.get("growth_percent"),
            data.get("health_score"),
            data.get("recommended_action"),
            data.get("timestamp")
        ]
        print("Appending row:", row)
        sheet.append_row(row)
        return jsonify({"status": "success", "row": row})
    except Exception as e:
        print("Error while appending:", str(e))
        return jsonify({"status": "failed", "error": str(e)}), 500

@app.route("/push_tray_data", methods=["POST"])
def push_data():
    data = request.json
    return process_and_push(data)

# Optional alias for relay compatibility
@app.route("/push_data", methods=["POST"])
def push_data_alias():
    data = request.json
    return process_and_push(data)
