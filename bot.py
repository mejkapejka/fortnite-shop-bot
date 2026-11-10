
import os
import json
import time
import urllib.request
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "https://itemshop.gg/api/v1/shop/fortnite"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Czas polski
now = datetime.now(ZoneInfo("Europe/Warsaw"))

# Automatyczne uruchomienie tylko o 01:00.
# Ręczne uruchomienie działa o każdej godzinie.
event = os.getenv("GITHUB_EVENT_NAME", "")

if event == "schedule" and now.hour != 1:
    print("Not 1 AM in Poland. Skipping scheduled run.")
    raise SystemExit(0)

# Pobieranie sklepu
request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "FortniteShopBot/1.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

data = result["data"]

# Kategorie i kolejność
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

def normalize(value):
    if isinstance(value, dict):
        value = " ".join(str(v) for v in value.values())

    return (
        str(value).lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def is_jam_track(section, item):
    item_fields = [
        "type",
        "displayType",
        "category",
        "subType",
        "backendType",
        "name"
    ]

    for field in item_fields:
        if "jamtrack" in normalize(item.get(field, "")):
            return True

    section_fields = [
        "name",
        "title",
        "type",
        "category",
        "displayName"
    ]

    for field in section_fields:
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

sent_count = 0

# Każda kategoria osobno
for item_type, title in categories.items():

    items = grouped[item_type]

    if not items:
        print("Empty category:", title)
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

    # Dzielenie długich kategorii
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
        sent_count += 1
        time.sleep(0.7)

if sent_count == 0:
    raise RuntimeError(
        "No categories were sent. Check Fortnite API item types."
    )

print("Fortnite Item Shop sent successfully!")
