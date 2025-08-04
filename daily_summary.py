import gspread
import os
import json
import requests
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = os.getenv("SHEET_ID")
SHEET_TAB_NAME = os.getenv("SHEET_TAB_NAME", "GreeNest Farm Tracker")
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)

# Telegram Setup
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Fetch and format summary
def build_summary():
    rows = sheet.get_all_records()
    if not rows:
        return "⚠️ No tray data available."

    summary = "*🌿 GreeNest Farm Dashboard Summary 🌿*\n\n"
    for tray in rows[-10:]:  # Adjust to limit or full if needed
        summary += (
            f"• `{tray['Tray Name']}` | 🌱 {tray['Growth %']}% | 💪 {tray['Health']} | 📌 {tray['Recommended Action']} | 🕒 {tray['Timestamp']}\n"
        )

    return summary

# Send to Telegram
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })

if __name__ == "__main__":
    summary = build_summary()
    send_to_telegram(summary)
