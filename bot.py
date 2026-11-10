
import os
import json
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "https://itemshop.gg/api/v1/shop/fortnite"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

# Wysyłanie tylko o 01:00 czasu polskiego
now = datetime.now(ZoneInfo("Europe/Warsaw"))

if now.hour != 1:
    print("Nie jest jeszcze godzina wysyłki.")
    raise SystemExit(0)

# Pobieranie sklepu
request = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "FortniteShopDiscordBot/1.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.loads(response.read().decode("utf-8"))

data = result["data"]

# Kategorie przedmiotów
categories = {
    "Outfit": "🧥 STROJE",
    "Pickaxe": "⛏️ KILOFY",
    "Back Bling": "🎒 PLECAKI",
    "Emote": "💃 EMOTKI",
    "Glider": "🪂 LOTNIE",
    "Wrap": "🎨 MALOWANIA",
    "Music": "🎵 MUZYKA",
    "Loading Screen": "🖼️ EKRANY WCZYTYWANIA",
    "Contrail": "✨ SMUGI",
    "Jam Track": "🎶 UTWORY",
    "Guitar": "🎸 GITARY",
    "Bass": "🎸 BASY",
    "Drum": "🥁 PERKUSJE",
    "Microphone": "🎤 MIKROFONY",
    "Bundle": "📦 ZESTAWY"
}

grouped = {}

for section in data.get("sections", []):
    for item in section.get("items", []):
        item_type = item.get("type", "Other")
        grouped.setdefault(item_type, []).append(item)

# Tworzenie embedów
embeds = []

for item_type, items in grouped.items():
    item_type = item_type or "Other"
    category = categories.get(item_type, f"🎁 {item_type.upper()}")

    lines = []

    for item in items:
        name = item.get("name", "Nieznany przedmiot")
        price = item.get("price") or {}
        amount = price.get("amount")
        images = item.get("images") or {}
        image = images.get("card") or images.get("render")

        price_text = (
            f"{amount:,} V-Dolców".replace(",", " ")
            if amount is not None else "Brak ceny"
        )

        line = f"• **{name}** — {price_text}"

        if image:
            line += f" [🖼️]({image})"

        lines.append(line)

    # Dzielenie długich kategorii na części
    chunks = []
    current = ""

    for line in lines:
        if len(current) + len(line) + 1 > 3500:
            chunks.append(current)
            current = ""

        current += line + "\n"

    if current:
        chunks.append(current)

    for index, chunk in enumerate(chunks):
        embed = {
            "title": category if index == 0 else f"{category} (część {index + 1})",
            "description": chunk,
            "color": 0x8B5CF6,
            "footer": {
                "text": "FORTNITE ITEM SHOP • Codzienna aktualizacja"
            }
        }

        if index == 0:
            first_image = (
                (items[0].get("images") or {}).get("card")
                or (items[0].get("images") or {}).get("render")
            )

            if first_image:
                embed["thumbnail"] = {"url": first_image}

        embeds.append(embed)

if not embeds:
    raise RuntimeError("Nie znaleziono przedmiotów w sklepie.")

# Discord: maksymalnie 10 embedów w jednej wiadomości
batch = []

for embed in embeds:
    batch.append(embed)

    if len(batch) == 10:
        payload = json.dumps({"embeds": batch}).encode("utf-8")

        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
    with urllib.request.urlopen(req, timeout=30) as response:
        print("Wysłano wiadomość:", response.status)

except urllib.error.HTTPError as e:
    print("Błąd Discorda:", e.code)
    print("Szczegóły:", e.read().decode("utf-8", errors="replace"))
    raise

        batch = []

if batch:
    payload = json.dumps({"embeds": batch}).encode("utf-8")

    req = urllib.request.Request(
        WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        print("Wysłano wiadomość:", response.status)

print("Sklep Fortnite został wysłany!")
