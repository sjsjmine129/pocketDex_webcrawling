import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import json
import re

# Base URL and headers
url = "https://www.pokemon-zone.com/sets/a1a/"
base_url = "https://www.pokemon-zone.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to download images (unchanged)
def download_image(image_url, card_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(image_url, headers=headers)

    if response.status_code == 200:
        content_type = response.headers['Content-Type']
        if 'image' in content_type:
            try:
                img = Image.open(BytesIO(response.content))

                # No need to convert RGBA to RGB, as PNG supports transparency
                img.save(f'card_images/{card_name}.png', 'PNG')
                # print(f"Image for {card_name} downloaded successfully as PNG.")
            except Exception as e:
                print(f"Error processing image for {card_name}: {e}")
        else:
            print(f"URL does not point to an image: {image_url}")
    else:
        print(f"Failed to download image from {image_url}, status code: {response.status_code}")


# Function to scrape card details
def scrape_card_details(card_url, number):
    print(f"Scraping card: {card_url}")
    res = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    card_details = {}

    
    card_details['id'] = 20000+number
    card_details['card_set'] = 'mythical'
    card_details['booster'] = 'mythical'
    card_details["card_name"] = soup.find("h1", class_="fs-1 text-break").text.strip()
    
    
    rarity_count = None
    temp = soup.find("span", class_="rarity-icon")
    if temp:

      rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--diamond"))
      if(rarity_count == 0):
        rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--star")) + 4
        if(rarity_count == 4):
          rarity_count = 7+ len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--crown"))
    

    card_details['rarity_count'] = rarity_count
    
    
    ## image    
    image_tag = soup.find("img", class_='game-card-image__img')
    if image_tag:
        image_url = image_tag['src']
        download_image(image_url, card_details['id'])

    
    #card type
    card_type = soup.find("div", class_="d-flex align-items-center gap-1")
    if card_type:
      temp = card_type.find("span", class_="energy-icon")
      classes = temp.get("class", [])

      for cls in classes:
          if cls.startswith("energy-icon--type-"):
              energy_type = cls.split("--type-")[-1]
              energy_type = energy_type.capitalize()
              card_details['card_type'] = energy_type
    
    
    
    print("@@",card_details)
        
    return
    

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
    
    del card_links[0]
    del card_links[0]
    del card_links[0]
    del card_links[0]
    # print(card_links)
    
    number = 1
    
    # link = card_links[85]
    # full_url = base_url + link if link.startswith("/") else link
    # card_details = scrape_card_details(full_url, number)
    # card_id = full_url.split("/")[-2]  # Extract unique card ID
    # card_data[card_id] = card_details
    
    for link in card_links:
        full_url = base_url + link if link.startswith("/") else link
        card_details = scrape_card_details(full_url, number)
        card_id = full_url.split("/")[-2]  # Extract unique card ID
        card_data[card_id] = card_details
        number += 1
        # break
        # if number == 4:
        #   break
        

    
    return card_data

# Main script
cards = scrape_all_cards(url)

# Save to JSON
output_file = "cardsData.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=4)

print(f"Card data saved to {output_file}")
