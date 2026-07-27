let event = {}

async function startscan() {
    const response = await fetch("http://127.0.0.1:8000/start-scan", {method: "GET"});
}

async function stopscan() {
    const response = await fetch("http://127.0.0.1:8000/stop-scan", {method: "GET"});
}

async function refresh() {
    displayaccounts()
}

async function editentry(entry) {
    let i = 0;
}

async function displayaccounts() {

    acounts = document.getElementById("accounts").innHTML = ""

    const response = await fetch("http://127.0.0.1:8000/accounts", {method: "GET"})

    const accounts = await response.json()

    let emails = Object.keys(accounts)

    console.log(emails)

    for (let i=0; i<emails.length; i++) {
        entry = document.createElement("div");
        entry.innerHTML = `
        <input type="input" id="account-${i}-email" value="${emails[i]}" disabled></input>
        <input type="input" id="account-${i}-password" value="##########" disabled></input>
        <button type="button" onclick="editentry(account${i})">edit</button>
        `
        entry.id=`account-${i}`
        entry.class=`entry`

        acounts = document.getElementById("accounts").appendChild(entry)
    }
}

window.onload = function() {
  refresh()
};