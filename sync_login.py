# ----------------------------------------------------
''' 
Sync version of loginToAccount
'''
# ----------------------------------------------------


import time

def run(
    page, 
    email,
    password
):
    with open("test", "w") as f:
        f.write("4")
    # STEP 1
    page.goto('https://fixr.co/login')

    # STEP 2
    page.locator('#login-email').fill(email)

    # STEP 3
    page.locator("button[type='submit']", has_text='Continue').click()

    # STEP 4
    page.locator('#login-password').fill(password)

    # STEP 5
    page.locator("button[type='submit']", has_text='Sign In').click()

    # WAIT FOR IDLE NETWORK
    page.wait_for_load_state('load')
    time.sleep(5)

    return page

# Dev Test Code
import os; from dotenv import load_dotenv; from camoufox.sync_api import Camoufox
def test(email, password): 
    with Camoufox(disable_coop=True) as browser: page = browser.new_page(); run(page,email,password)
if __name__ == "__main__": load_dotenv(); email = os.getenv('TEST_EMAIL'); password = os.getenv('TEST_PASSWORD'); test(email, password)
