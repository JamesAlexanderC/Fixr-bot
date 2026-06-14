# ----------------------------------------------------
# Main File, starts the whole program including tasks
# ----------------------------------------------------

# External Imports

import asyncio
import uvicorn

# Internal Imports

import output
from engine import queueHandler, stopEvent
from api import app
# import ticketFunctions.createAccount as createAccount

async def startEngine():
    handler = asyncio.create_task(queueHandler("idle"))

    await stopEvent.wait()

    handler.cancel()
    
    await asyncio.gather(handler, return_exceptions=True)

async def startApi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=2)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    await asyncio.gather(
        startEngine(),
        startApi()
    )

if __name__ == "__main__":
    asyncio.run(main())