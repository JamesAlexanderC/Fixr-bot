# ----------------------------------------------------
''' 
Async version of loginToAccount
'''
# ----------------------------------------------------


import asyncio

async def run(
    page, 
    email,
    password
):
    with open("test", "w") as f:
        f.write("4")
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
    await asyncio.sleep(5)

    return page

# Dev Test Code
import os; from dotenv import load_dotenv; from camoufox.async_api import AsyncCamoufox
async def test(email, password): 
    async with AsyncCamoufox(disable_coop=True) as browser: page = await browser.new_page(); await run(page,email,password)
if __name__ == "__main__": load_dotenv(); email = os.getenv('TEST_EMAIL'); password = os.getenv('TEST_PASSWORD'); asyncio.run(test(email, password))