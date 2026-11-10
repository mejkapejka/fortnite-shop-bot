
import os
import json
import time
import urllib.request
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "https://itemshop.gg/api/v1/shop/fortnite"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Wysyłka o 01:00 czasu polskiego
now = datetime.now(ZoneInfo("Europe/Warsaw"))

if now.hour != 1:
    print("It is not 1 AM yet.")
    raise SystemExit(0)

# Pobieranie sklepu
request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "FortniteShopBot/1.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

data = result["data"]

# Kategorie i ich kolejność
categories = {
    "Outfit": "🧥 SKINS",
    "Pickaxe": "⛏️ PICKAXES",
    "Glider": "🪂 GLIDERS",
    "Back Bling": "🎒 BACK BLINGS",
    "Emote": "💃 EMOTES",
    "Wrap": "🎨 WRAPS",
    "Contrail": "✨ CONTRAILS",
    "Loading Screen": "🖼️ LOADING SCREENS",
    "Bundle": "📦 BUNDLES"
}

# Pomijanie Jam Tracków
def normalize(value):
    if isinstance(value, dict):
        value = " ".join(str(v) for v in value.values())

    return str(value).lower().replace(" ", "").replace("_", "").replace("-", "")


def is_jam_track(section, item):
    fields = [
        "type",
        "displayType",
        "category",
        "subType",
        "backendType",
        "name"
    ]

    for field in fields:
        if "jamtrack" in normalize(item.get(field, "")):
            return True

    for field in ["name", "title", "type", "category", "displayName"]:
        if "jamtrack" in normalize(section.get(field, "")):
            return True

    return False


# Grupowanie przedmiotów
grouped = {category: [] for category in categories}

for section in data.get("sections", []):
    for item in section.get("items", []):

        if is_jam_track(section, item):
            print("Skipped Jam Track:", item.get("name"))
            continue

        item_type = item.get("type", "")

        if isinstance(item_type, dict):
            item_type = item_type.get("value", "")

        # Pomijamy kategorie spoza listy
        if item_type not in categories:
            continue

        grouped[item_type].append(item)


# Wysyłanie wiadomości
def send_embed(embed):
    response = requests.post(
        WEBHOOK_URL,
        json={"embeds": [embed]},
        timeout=30
    )

    print("Discord status:", response.status_code)

    if response.status_code >= 400:
        print("Error details:", response.text)
        response.raise_for_status()

    print("Category sent!")


print("Sending Fortnite Item Shop...")

# Każda kategoria jako osobna wiadomość
for item_type, title in categories.items():

    items = grouped[item_type]

    if not items:
        continue

    lines = []

    for item in items:
        if is_jam_track({}, item):
            continue

        name = item.get("name") or "Unknown item"

        price = item.get("price") or {}
        amount = price.get("amount")

        if amount is not None:
            price_text = f"{amount:,} V-Bucks"
        else:
            price_text = "Price unavailable"

        lines.append(f"• **{name}** — {price_text}")

    if not lines:
        continue

    # Dzielenie długiej kategorii
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > 3500:
            if current:
                chunks.append(current)
            current = ""

        current += line + "\n"

    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks):

        embed_title = title

        if index > 0:
            embed_title += f" (PART {index + 1})"

        embed = {
            "title": embed_title,
            "description": chunk,
            "color": 0x8B5CF6,
            "footer": {
                "text": "FORTNITE ITEM SHOP • DAILY UPDATE"
            }
        }

        send_embed(embed)
        time.sleep(0.7)

print("Fortnite Item Shop sent successfully!")
