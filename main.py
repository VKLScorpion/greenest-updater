from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = FastAPI()

# Define input schema
class TrayData(BaseModel):
    tray_name: str
    growth_percent: float
    health_status: str
    notes: Optional[str] = ""
    timestamp: Optional[str] = None

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("GreeNest Farm Tracker").worksheet("GreeNest Farm Tracker")

@app.post("/upload")
async def upload_data(data: TrayData):
    try:
        timestamp = data.timestamp or datetime.utcnow().isoformat()
        row = [
            timestamp,
            data.tray_name,
            data.growth_percent,
            data.health_status,
            data.notes
        ]
        sheet.append_row(row)
        return {"status": "success", "message": "Row appended"}
    except Exception as e:
        return {"status": "error", "message": str(e)}