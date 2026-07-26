let accounts = {}
let event = {}

async function startscan() {
    const response = await fetch("http://127.0.0.1:8000/start-scan", {method: "GET"});
}

async function stopscan() {
    const response = await fetch("http://127.0.0.1:8000/stop-scan", {method: "GET"});
}

function refresh() {

}

function displayaccounts(accounts) {

    const emails = Object.keys(accounts)

    for (let i=0; i<emails.length; i++) {
        entry = document.createElement("div");
        entry.innerHTML = `
        <input type="input" disabled>${email}</input>
        <input type="input" disabled>*******</input>
        <button type="button">edit</button>
        `
        entry.id=`account=${i}`
    }
}