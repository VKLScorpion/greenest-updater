# relay_to_greenest.py
from fastapi import FastAPI, Request
import requests

app = FastAPI()

# Render health check
@app.get("/")
def root():
    return {"message": "✅ Relay is running"}

GREENEST_BACKEND_URL = "https://greenest-updater.onrender.com/push_tray_data"

@app.post("/relay")
async def relay_data(req: Request):
    try:
        payload = await req.json()
        print("🔁 Relay received payload:", payload)

        response = requests.post(GREENEST_BACKEND_URL, json=payload)
        print("📤 Forwarded to:", GREENEST_BACKEND_URL)
        print("📥 Updater responded:", response.status_code, response.text)

        return {
            "status": "forwarded",
            "payload": payload,
            "backend_status_code": response.status_code,
            "backend_response": response.text
        }

    except Exception as e:
        print("❌ Relay error:", str(e))
        return {"status": "error", "detail": str(e)}
