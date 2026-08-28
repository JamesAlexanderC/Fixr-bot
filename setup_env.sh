python3 -m venv .venv &&
echo "virtual environment created" &&
source .venv/bin/activate &&
echo "virtual environment activated" &&
pip install -r requirements.txt &&
echo "dependencies installed" &&
camoufox fetch &&
echo "camoufox browser driver installed" &&
touch accounts.json &&
echo '{"example@example.com": "example_pass"}' > accounts.json &&
echo "created accounts storage file" &&
touch event.json &&
echo '{"organiser_url": "https://fixr.co/organiser/timepiece", "ticket_keyword": "Saturday", "scan_interval": "5"}' > event.json &&
echo "created event storage file" &&
mkdir "logs" &&
echo "created logs folder" &&
touch scan_proxies.json && touch buy_proxies.json &&
echo "created proxy storage file" &&
echo "=================================" &&
echo "         SETUP COMPLETE!         " &&
echo "================================="


