
import os
import json
import time
import urllib.request
import requests

from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "https://itemshop.gg/api/v1/shop/fortnite"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

now = datetime.now(ZoneInfo("Europe/Warsaw"))

if now.hour != 1:
    print("It is not 1 AM yet.")
    raise SystemExit(0)

request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "FortniteShopBot/1.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

data = result["data"]

categories = {
    "Outfit": "🧥 SKINS",
    "Pickaxe": "⛏️ PICKAXES",
    "Back Bling": "🎒 BACK BLINGS",
    "Emote": "💃 EMOTES",
    "Glider": "🪂 GLIDERS",
    "Wrap": "🎨 WRAPS",
    "Music": "🎵 MUSIC",
    "Loading Screen": "🖼️ LOADING SCREENS",
    "Contrail": "✨ CONTRAILS",
    "Guitar": "🎸 GUITARS",
    "Bass": "🎸 BASSES",
    "Drum": "🥁 DRUMS",
    "Microphone": "🎤 MICROPHONES",
    "Bundle": "📦 BUNDLES"
}

grouped = {}

for section in data.get("sections", []):
    for item in section.get("items", []):

        # Skip Jam Tracks
        if item.get("type") == "Jam Track":
            continue

        item_type = item.get("type") or "Other"

        if not isinstance(item_type, str):
            item_type = "Other"

        grouped.setdefault(item_type, []).append(item)


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

    print("Message sent!")


print("Sending Fortnite Item Shop...")

for item_type, items in grouped.items():

    category = categories.get(
        item_type,
        f"🎁 {item_type.upper()}"
    )

    lines = []

    for item in items:
        name = item.get("name") or "Unknown item"
        price = item.get("price") or {}
        amount = price.get("amount")

        if amount is not None:
            price_text = f"{amount:,} V-Bucks"
        else:
            price_text = "Price unavailable"

        lines.append(f"• **{name}** — {price_text}")

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

        title = (
            category
            if index == 0
            else f"{category} (PART {index + 1})"
        )

        embed = {
            "title": title,
            "description": chunk,
            "color": 0x8B5CF6,
            "footer": {
                "text": "FORTNITE ITEM SHOP • DAILY UPDATE"
            }
        }

        send_embed(embed)
        time.sleep(0.5)

print("Fortnite Item Shop sent successfully!")
