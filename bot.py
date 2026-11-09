import os
import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "https://itemshop.gg/api/v1/shop/fortnite"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Sprawdzamy godzinę w Polsce
now = datetime.now(ZoneInfo("Europe/Warsaw"))

if now.hour != 1:
    print("To nie jest jeszcze godzina wysyłki.")
    raise SystemExit(0)

# Pobieramy aktualny sklep Fortnite
request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "FortniteShopDiscordBot/1.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

data = result["data"]
lines = ["🛒 SKLEP FORTNITE", ""]

for section in data.get("sections", []):
    for item in section.get("items", []):
        name = item.get("name", "Nieznany przedmiot")
        price = item.get("price") or {}
        amount = price.get("amount")

        if amount is not None:
            lines.append(f"• {name} — {amount} V-Dolców")

lines.append("")
lines.append(
    f"Data from itemshop.gg: {result['meta']['attribution']['url']}"
)

if len(lines) <= 2:
    raise RuntimeError("Nie znaleziono przedmiotów w sklepie.")

# Discord ogranicza wiadomość do 2000 znaków
messages = []
current = ""

for line in lines:
    if len(current) + len(line) + 1 > 1900:
        messages.append(current)
        current = ""
    current += line + "\n"

if current:
    messages.append(current)

for message in messages:
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        print("Wysłano wiadomość:", response.status)

print("Sklep Fortnite został wysłany!")
