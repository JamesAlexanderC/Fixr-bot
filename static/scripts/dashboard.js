let event = {}

async function startscan() {
    const response = await fetch("/start-scan", {method: "GET"});
}

async function stopscan() {
    const response = await fetch("/stop-scan", {method: "GET"});
}

async function refresh() {
    displayaccounts()
}

async function editentry(entry) {
    let i = 0;
}

async function displayaccounts() {

    const response = await fetch("/accounts", {method: "GET"})

    const accounts = await response.json()

    let emails = Object.keys(accounts)

    document.getElementById("accounts").innerHTML = ""

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

async function editevent() {
    const response = await fetch(
        "/event",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "organiser_url": document.getElementById("organiser-url-in").value,
                "ticket_keyword": document.getElementById("ticket-keyword-in").value,
                "scan_interval": document.getElementById("scan-interval-in").value
            })
        })
}

window.onload = function() {
  refresh()
};