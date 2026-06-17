from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from engine import inputQueue, stopEvent
import storage

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

@app.post("/custom")
async def send_custom_message(data: dict):
    msg = data.get("msg")
    await inputQueue.put(msg)
    return {"status": "ok"}

@app.post("/shutdown")
async def shutdown():
    await inputQueue.put("SHUTDOWN")
    return {"status": "shutting down"}

@app.post("/init")
async def initialise_bot():
    await inputQueue.put("INITIALISE")
    return {"status": "ok"}

@app.post("/start")
async def start_heartbeat():
    await inputQueue.put("START_HEARTBEAT")
    return {"status": "ok"}

@app.get("/")
async def hello():
    return FileResponse("static/index.html")

@app.post("/editCard")
async def edit_card(data: dict):
    if not all([cardNumber, data.get("cardExpiry"), data.get("cardCvc"), data.get("cardPostcode")]):
        return {"status": "error", "message": "Missing required fields"}, 400
    cardNumber = data.get("cardNumber")
    cardExpiry = data.get("cardExpiry")
    cardCvc = data.get("cardCvc")
    cardPostcode = data.get("cardPostcode")
    await storage.editCard(cardNumber, cardExpiry, cardCvc, cardPostcode)
    return {"status": "ok"}