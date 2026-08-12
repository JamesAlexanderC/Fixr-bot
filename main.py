# ----------------------------------------------------
# Main File, starts the whole program including tasks
# ----------------------------------------------------

# External Imports

import asyncio
import uvicorn
import os

# Internal Imports

from engine import queueHandler, stopEvent
from api import app
# import ticketFunctions.createAccount as createAccount

async def startEngine():
    handler = asyncio.create_task(queueHandler())
    await stopEvent.wait()
    handler.cancel()
    await asyncio.gather(handler, return_exceptions=True)

async def startApi():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level=0)
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    try:
        for log in ["logs/engine.log", "logs/buy_ticket.log", "logs/get_ticket.log", "logs/scan_loop.log"]:
            if os.path.exists(log):
                with open(log, "a") as f:
                    f.write("="*100 + "\n" + "SERVER START" + "\n" + "="*100 + "\n")
    except Exception as e:
        raise Exception(f"Cannot start logging: {str(e)}") from e
    await asyncio.gather(
        startEngine(),
        startApi()
    )

if __name__ == "__main__":
    asyncio.run(main())
