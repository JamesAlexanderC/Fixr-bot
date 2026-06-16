import asyncio
import os

from dotenv import load_dotenv
from camoufox.async_api import AsyncCamoufox
from time import sleep

import loginToAccount
import reserveTickets
import buyTickets

load_dotenv()

EMAIL = os.getenv('EMAIL')
PASS = os.getenv('PASS')
ZYTE_API_KEY = os.getenv('ZYTE_API_KEY')
GEONIX_USERNAME = os.getenv('GEONIX_USERNAME')
GEONIX_PASS = os.getenv('GEONIX_PASS')

'''
proxy={
    "server": "res.geonix.com:10000",
    "username": GEONIX_USERNAME,
    "password": GEONIX_PASS,
},
'''

async def test_login_reserve_buy(page):
    page = await loginToAccount.login(page, 1)
    print('async login complete')
    page = await reserveTickets.reserve(page, 'https://fixr.co/event/sketch-1206-tickets-987734962/tickets?lang=en-US')
    print('async reservation complete')
    page = await buyTickets.buy(page)
    await page.wait_for_timeout(300000)

async def test_parallel_flow():
    async with AsyncCamoufox(
            geoip=True,
            i_know_what_im_doing=True,
            disable_coop=True,
        ) as browser:
        context = await browser.new_context(ignore_https_errors=True)
        
        page1 = await context.new_page()

        page2 = await context.new_page()

        task1 = asyncio.create_task(test_login_reserve_buy(page1))
        
        task2 = asyncio.create_task(test_login_reserve_buy(page2))

        page1, page2 = await asyncio.gather(task1, task2, return_exceptions=True)




if __name__ == '__main__':
    asyncio.run(test_parallel_flow())
