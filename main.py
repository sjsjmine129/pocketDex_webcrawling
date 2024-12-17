import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import json

# Base URL and headers
url = "https://www.pokemon-zone.com/sets/a1a/"
base_url = "https://www.pokemon-zone.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Create directory for images
os.makedirs("card_images", exist_ok=True)

# Function to download an image
def download_image(image_url, card_id):
    try:
        response = requests.get(image_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img.save(f"card_images/{card_id}.png", "PNG")
        print(f"Downloaded image for card {card_id}")
    except Exception as e:
        print(f"Failed to download image for card {card_id}: {e}")

# Function to scrape card details
def scrape_card_details(card_url):
    print(f"Scraping card: {card_url}")
    res = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    card_details = {}

    try:
        # Card name
        card_name = soup.find("h1", class_="elementor-heading-title")
        card_details["card_name"] = card_name.text.strip() if card_name else "Unknown"

        # Card image
        image_tag = soup.find("img", {"class": "attachment-large"})
        if image_tag:
            image_url = image_tag["src"]
            card_id = card_url.split("/")[-2]  # Generate card ID from URL
            card_details["image_url"] = image_url
            download_image(image_url, card_id)

        # Card rarity
        rarity = soup.find("ul", class_="custom-taxo-terms-list--rarity")
        if rarity:
            diamond_count = len(rarity.find_all("i", class_="rarity icon-diamond"))
            star_count = len(rarity.find_all("i", class_="rarity icon-star"))
            crown_count = len(rarity.find_all("i", class_="rarity icon-crown"))
            card_details["rarity"] = (
                "diamond" if diamond_count else "star" if star_count else "crown" if crown_count else "None"
            )
        else:
            card_details["rarity"] = "Unknown"
    except Exception as e:
        print(f"Error scraping card details: {e}")

    return card_details

# Function to scrape all cards from the main page
def scrape_all_cards(main_url):
    res = requests.get(main_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # Find all card links
    card_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if "/cards/" in a["href"]
    ]

    print(f"Found {len(card_links)} cards.")
    card_data = {}

    for link in card_links:
        full_url = base_url + link if link.startswith("/") else link
        card_details = scrape_card_details(full_url)
        card_id = full_url.split("/")[-2]  # Extract unique card ID
        card_data[card_id] = card_details

    return card_data

# Main script
cards = scrape_all_cards(url)

# Save to JSON
output_file = "cardsData.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=4)

print(f"Card data saved to {output_file}")
