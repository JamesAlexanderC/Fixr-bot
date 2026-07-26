# ----------------------------------------------------
''' 
Async version of loginToAccount
'''
# ----------------------------------------------------

import os
from asyncio import sleep
from dotenv import load_dotenv


async def login(page, code):
    load_dotenv()

    account_code = str(code)
    email = os.getenv(f'ACCE{account_code}')
    password = os.getenv(f'ACCP{account_code}')

    if email is None or password is None:
        raise ValueError(f'ACCE{account_code} and ACCP{account_code} must be set in the environment')

    # STEP 1
    await page.goto('https://fixr.co/login')

    # STEP 2
    await page.locator('#login-email').fill(email)

    # STEP 3
    await page.locator("button[type='submit']", has_text='Continue').click()

    # STEP 4
    await page.locator('#login-password').fill(password)

    # STEP 5
    await page.locator("button[type='submit']", has_text='Sign In').click()

    # WAIT FOR IDLE NETWORK
    await page.wait_for_load_state('load')
    await sleep(5)

    return page
