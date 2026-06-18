from fastapi import FastAPI
from fastapi import HTTPException
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

@app.get("/configuration")
async def configuration():
    return FileResponse("static/configuration.html")

@app.post("/card")
async def edit_card(data: dict):
    cardNumber = data.get("cardNumber")
    cardExpiry = data.get("cardExpiry")
    cardCvc = data.get("cardCvc")
    cardPostcode = data.get("cardPostcode")
    if not all([cardNumber, cardExpiry, cardCvc, cardPostcode]):
        raise HTTPException(status_code=400, detail="Missing required fields")
    await storage.editCard(cardNumber, cardExpiry, cardCvc, cardPostcode)
    return {"status": "ok"}

@app.get("/accounts")
async def get_accounts():
    try:
        await storage.loadAccounts()
    except FileNotFoundError:
        storage.accounts = []
        with open("accounts.json", "w") as f:
            f.write("[]")
    return {"accounts": storage.accounts}

@app.post("/account")
async def add_account(data: dict):
    email = data.get("email")
    password = data.get("password")
    if not all([email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        result = await storage.addAccount(email, password)
    except FileNotFoundError:
        with open("accounts.json", "w") as f:
            f.write("[]")
        result = await storage.addAccount(email, password)

    if not result:
        raise HTTPException(status_code=400, detail="Account already exists")
    return {"status": "ok"}

@app.get("/event")
async def get_event():
    try:
        await storage.loadEvent()
    except FileNotFoundError:
        storage.event = {}
        with open("event.json", "w") as f:
            f.write("{}")
    return {"event": storage.event}

@app.post("/event")
async def edit_event(data: dict):
    organiserUrl = data.get("organiserUrl")
    ticketKeyword = data.get("ticketKeyword")
    event_time_raw = data.get("time")
    if not all([organiserUrl, ticketKeyword, event_time_raw]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    try:
        event_time = int(event_time_raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="time must be a positive integer")
    if event_time < 1:
        raise HTTPException(status_code=400, detail="time must be a positive integer")

    await storage.editEvent(organiserUrl, ticketKeyword, event_time)
    return {"status": "ok"}