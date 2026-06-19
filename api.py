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

@app.post("/stop")
async def stop_heartbeat():
    await inputQueue.put("STOP_HEARTBEAT") # YET TO BE IMPLEMENTED IN QUEUEHANDLER
    return {"status": "ok"}

@app.get("/status")
async def get_status():
    return {"status": "unimplemented"}

# Specs below: 

'''
         * GET /status — PLACEHOLDER, NOT IMPLEMENTED in api.py.
         * Polled every POLL_INTERVAL_MS. This page assumes the backend will
         * eventually expose this route returning JSON shaped like:
         *
         * {
         *   "heartbeat": {
         *     "running": boolean,
         *     "cycles": number,            // completed ticketSearch() loop iterations
         *     "startedAt": string | null,  // ISO8601, set when START_HEARTBEAT is actioned
         *     "lastCycleAt": string | null // ISO8601, set after each checkForTickets() pass
         *   },
         *   "ticketsFound": {
         *     "found": boolean,
         *     "detail": string | null,     // whatever checkForTickets() returned
         *     "foundAt": string | null     // ISO8601, changes each time a NEW find happens
         *   },
         *   "flows": {
         *     "completed": boolean,        // true once every getTickets() flow has finished
         *     "successful": number,
         *     "failed": number,
         *     "restarted": [               // one entry per stage a flow was retried/restarted from
         *       { "stage": "logging in" | "reserving" | "buying" | string, "count": number }
         *     ]
         *   }
         * }
         *
         * Durations/elapsed times are deliberately NOT expected to be pre-formatted
         * strings - the backend only needs to supply timestamps, and this page
         * computes "time since" / "running time" client-side (see tick() below).
         *
         * Until this route exists every poll 404s. That failure is caught here
         * and the affected panels are left in a clearly-labelled "unavailable"
         * placeholder state instead of crashing the page.
'''