from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from engine import inputQueue, stopEvent

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

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