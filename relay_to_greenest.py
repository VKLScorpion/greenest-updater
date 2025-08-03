# relay_to_greenest.py
from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# Set this to your actual Render backend URL
GREENEST_BACKEND_URL = os.getenv("GREENEST_BACKEND_URL", "https://greenest-updater.onrender.com/push_data")

@app.post("/relay")
async def relay_data(req: Request):
    try:
        payload = await req.json()
        response = requests.post(GREENEST_BACKEND_URL, json=payload)

        return {
            "status": "forwarded",
            "payload": payload,
            "backend_status_code": response.status_code,
            "backend_response": response.text
        }

    except Exception as e:
        return {"status": "error", "detail": str(e)}
