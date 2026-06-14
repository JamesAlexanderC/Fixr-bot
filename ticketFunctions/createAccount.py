# ----------------------------------------------------
''' 
Async version of createAccount
'''
# ----------------------------------------------------

async def createAccount(page, email, fname, lname, dob, phone):
    # STEP 1
    await page.goto('https://fixr.co/login')

    # STEP 2
    await page.locator('#login-email').fill(email)

    # STEP 3
    await page.locator("button[type='submit']", has_text='Continue').click()

    # STEP 4
    await page.wait_for_load_state('networkidle')
    await page.goto('https://fixr.co/my-profile')

    # STEP 5
    await page.locator('#user-profile-first-name').fill(fname)

    # STEP 6
    await page.locator('#user-profile-last-name').fill(lname)

    # STEP 7
    await page.locator('#user-profile-dob').fill(dob)

    # STEP 8
    await page.locator('#user-profile-gender-m').check()

    # STEP 9
    await page.locator('#user-profile-phone-number').fill(phone)

    # STEP 10
    await page.locator("button[type='submit']").click()

    # WAIT FOR IDLE NETWORK
    await page.wait_for_load_state('networkidle')
