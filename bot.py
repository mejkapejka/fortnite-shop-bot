
import os
import json
import urllib.request
import urllib.error
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


# Grupowanie przedmiotów
grouped = {}

for section in data.get("sections", []):
    for item in section.get("items", []):
        item_type = item.get("type") or "Other"

        if not isinstance(item_type, str):
            item_type = "Other"

        grouped.setdefault(item_type, []).append(item)


# Tworzenie embedów
embeds = []

for item_type, items in grouped.items():
    category = categories.get(
        item_type,
        f"🎁 {item_type.upper()}"
    )

    lines = []

    for item in items:
        name = item.get("name") or "Nieznany przedmiot"
        price = item.get("price") or {}
        amount = price.get("amount")
        images = item.get("images") or {}

        image = images.get("card") or images.get("render")

        if amount is not None:
            price_text = f"{amount:,} V-Dolców".replace(",", " ")
        else:
            price_text = "Brak ceny"

        line = f"• **{name}** — {price_text}"

        if image:
            line += f" [🖼️]({image})"

        lines.append(line)

    # Dzielenie kategorii na części
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
        embed = {
            "title": category if index == 0 else f"{category} (część {index + 1})",
            "description": chunk,
            "color": 0x8B5CF6,
            "footer": {
                "text": "FORTNITE ITEM SHOP • Codzienna aktualizacja"
            }
        }

        if index == 0 and items:
            first_images = items[0].get("images") or {}
            first_image = (
                first_images.get("card")
                or first_images.get("render")
            )

            if first_image:
                embed["thumbnail"] = {"url": first_image}

        embeds.append(embed)


if not embeds:
    raise RuntimeError("Nie znaleziono przedmiotów w sklepie.")


# Funkcja wysyłająca wiadomości na Discorda
def send_embeds(batch):
    payload = json.dumps({
        "embeds": batch
    }).encode("utf-8")

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


# Discord pozwala wysłać maksymalnie 10 embedów naraz
for i in range(0, len(embeds), 10):
    batch = embeds[i:i + 10]
    send_embeds(batch)


print("Sklep Fortnite został wysłany!")
