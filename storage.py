import json

# --------------------------------------------------------------------
# Bot variables
# --------------------------------------------------------------------
global card
card = {}

global accounts
accounts = {}

global event
event = {}

# --------------------------------------------------------------------
# Card Management
# --------------------------------------------------------------------

async def loadCard():
    global card
    with open('card.json', 'r') as f:
        card = json.load(f)

async def editCard(
        cardNumber, 
        cardExpiry,
        cardCvc,
        cardPostcode,
        ):
    global card
    
    details = {'CARD_NUMBER': cardNumber, 'CARD_EXPIRY': cardExpiry, 'CARD_CVC': cardCvc, 'CARD_POSTCODE': cardPostcode}

    with open('card.json', 'w') as f:
        json.dump(details, f)
    
    await loadCard()

    return True

# --------------------------------------------------------------------
# Account Management
# --------------------------------------------------------------------

async def loadAccounts():
    global accounts
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)

async def addAccount( # An account being added here should be a fully verified fixr account
        email,
        password,
):
    global accounts
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)
        for i in range(len(accounts)):
            if accounts[i]['email'] == email:
                return False # Account already exists
    
    accounts.append({'email': email, 'password': password})

    with open('accounts.json', 'w') as f:
        json.dump(accounts, f)

    return True

# --------------------------------------------------------------------
# Event Management
# --------------------------------------------------------------------

async def loadEvent():
    global event
    with open('event.json', 'r') as f:
        event = json.load(f)

async def editEvent(
        organiserUrl, # This is the URL of the event organiser page, which contains the ticket links
        ticketKeyword, # Defines the keyword used to select correct ticket (must be unique)
        time, # This defines the time the bot will buy, defined by a 1 indexed integer, 1 being the first time slot, 2 the second and so on
):
    global event
    details = {'EVENT_URL': organiserUrl, 'EVENT_NAME': ticketKeyword, 'EVENT_DATE': time, 'EVENT_TIME': time}

    with open('event.json', 'w') as f:
        json.dump(details, f)
    
    await loadEvent()

    return True