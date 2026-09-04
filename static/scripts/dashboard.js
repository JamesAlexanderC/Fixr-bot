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
    document.getElementById(`${entry}-email`).disabled = false
    document.getElementById(`${entry}-password`).disabled = false
    document.getElementById(`${entry}-edit-btn`).style.visibility = "hidden"
    
    save_btn = document.createElement("button");
    delete_btn = document.createElement("button");

    save_svg = document.createElement("img")
    save_svg.src = "static/assets/save.svg"
    save_svg.id = "save-icon"

    save_btn.appendChild(save_svg)
    

    document.getElementById(entry).appendChild(save_btn)
    document.getElementById(entry).appendChild(delete_btn)
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
        <button type="button" id="account-${i}-edit-btn" onclick="editentry('account-${i}')">edit</button>
        `
        entry.id=`account-${i}`
        entry.class=`entry`

        document.getElementById("accounts").appendChild(entry)
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
        }
    )
}

async function cancelnewaccount() {
    document.getElementById("added-account").remove()
    document.getElementById("add-account").style.visibility = "visible"
    refresh()
}

async function savenewaccount() {
    const response = await fetch(
        "/accounts",
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "email": document.getElementById("added-account-email").value,
                "password": document.getElementById("added-account-password").value
            })
        }
    )
    document.getElementById("add-account").style.visibility = "visible"
    refresh()
}

async function addnewaccount() {
    entry = document.createElement("div");
    entry.innerHTML = `
    <input type="input" id="added-account-email" value="example@example.com" enabled></input>
    <input type="input" id="added-account-password" value="##########" enabled></input>
    <button type="button" onclick="savenewaccount()">save</button>
    <button type="button" onclick="cancelnewaccount()">cancel</button>
    `
    entry.id=`added-account`
    entry.class=`entry`
    document.getElementById("accounts").appendChild(entry)
    document.getElementById("add-account").style.visibility = "hidden"
}

window.onload = function() {
  refresh()
};