# This file will be the main engine for starting multiple login_get_ticket instances in parallel
import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from itertools import repeat
from camoufox.sync_api import Camoufox
import sync_login as login
import sync_get_ticket as get_ticket
import sync_buy_ticket as buy_ticket

# Will have the option for proxy (enabled for prod, disabled for dev)
PROXY = False

def login_get_ticket(
        account,
        code,
        url,
):
    email = account["email"]
    password = account["fixr_password"]
    try:
        if PROXY:
            try:
                if os.path.exists("buy_proxies.json"):
                    # Here we use the format server:port:username:password
                    with open("buy_proxies.json") as f:
                        proxies = json.load(f)
                    num_proxies = len(proxies)
                    proxy = proxies[random.randint(0, num_proxies-1)].split(":")
                else:
                    raise Exception("No proxies file")
                camoufox = AsyncCamoufox(
                    proxy={
                        "server": f"{proxy[0]}:{proxy[1]}",
                        "username": proxy[2],
                        "password": proxy[3]
                    },
                    geoip=True,
                )
                logger.debug("Proxies loaded successfully")
            except Exception as e:
                logger.error("Error loading proxies: %s", str(e), exc_info=True)
                raise Exception(f"Error loading proxies: {str(e)}") from e
        else:
            camoufox = Camoufox(
                window=(1920, 1070)
            )
            browser = camoufox.__enter__()
            page = browser.new_page()
            page.set_default_timeout(100_000)
    except Exception as e:
        raise Exception(f"Error starting Camoufox (this will be a pain to debug): {str(e)}, ABORTING")

    try:
        page = login.run(
            page=page,
            email=email,
            password=password,
        )
    except Exception as e:
        raise e
    try:
        page = get_ticket.run(
            page=page,
            url=url,
            number=code
        )
    except Exception as e:
        raise e
    try:
        buy_ticket.buy(
            page=page,
            cnumber="1234567812345678",
            expiry="01/2027",
            cvc="123",
            postal="TAU43F"
        )
        time.sleep(5)
        page.screenshot(path=f"{email}.png")
    except Exception as e:
        raise e

    camoufox.__exit__(None, None, None)

# DEV CODE
if False:
    with open ("accounts.json") as f:
        accounts = json.load(f)
    login_get_ticket(
        email=accounts[0][0],
        password=accounts[0][1],
        code=0,
        url="https://fixr.co/event/fever-foam-party-tickets-903163/tickets"
    )

def main():
    with open ("prod_accounts.json") as f:
        accounts = json.load(f)[0:5]

    # "spawn" avoids inheriting an already-initialized Playwright process.
    with ProcessPoolExecutor(
        max_workers=5,
        mp_context=get_context("spawn"),
    ) as executor:
        results = list(executor.map(
            login_get_ticket, 
            accounts, 
            repeat(0),
            repeat("https://fixr.co/event/fever-foam-party-tickets-903163/tickets")
        ))

    print(results)

if __name__ == "__main__":
    main()