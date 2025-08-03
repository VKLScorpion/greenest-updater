from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ✅ Health check endpoint for Render
@app.get("/")
def root():
    return {"message": "Relay is running"}

# ✅ Ensure this matches your actual backend
GREENEST_BACKEND_URL = os.getenv("GREENEST_BACKEND_URL", "https://greenest-updater.onrender.com/push_tray_data")

@app.post("/relay")
async def relay_data(req: Request):
    try:
        payload = await req.json()
        print("🚀 Relay received payload:", payload)

        response = requests.post(GREENEST_BACKEND_URL, json=payload)

        print("📤 Forwarded to:", GREENEST_BACKEND_URL)
        print("📥 Response from backend:", response.status_code, response.text)

        return {
            "status": "forwarded",
            "payload": payload,
            "backend_status_code": response.status_code,
            "backend_response": response.text
        }

    except Exception as e:
        print("❌ Relay Error:", str(e))
        return {"status": "error", "detail": str(e)}
