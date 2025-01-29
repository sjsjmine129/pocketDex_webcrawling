import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import json
import re


# Base URL and headers

base_url = "https://www.pokemon-zone.com"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to download images (unchanged)
# def download_image(image_url, card_name):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
#     }
#     response = requests.get(image_url, headers=headers)

#     if response.status_code == 200:
#         content_type = response.headers['Content-Type']
#         if 'image' in content_type:
#             try:
#                 img = Image.open(BytesIO(response.content))

#                 # No need to convert RGBA to RGB, as PNG supports transparency
#                 img.save(f'card_images/{card_name}.webp', 'WEBP')
                
#                 # print(f"Image for {card_name} downloaded successfully as PNG.")
#             except Exception as e:
#                 print(f"Error processing image for {card_name}: {e}")
#         else:
#             print(f"URL does not point to an image: {image_url}")
#     else:
#         print(f"Failed to download image from {image_url}, status code: {response.status_code}")


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

                # Ensure the output directory exists
                output_dir = 'card_images'
                os.makedirs(output_dir, exist_ok=True)

                # Save with higher quality
                output_path = os.path.join(output_dir, f'{card_name}.webp')
                img.save(output_path, 'WEBP', quality=95)  # Use high quality

                # print(f"Image for {card_name} downloaded successfully as WebP.")
            except Exception as e:
                print(f"Error processing image for {card_name}: {e}")
        else:
            print(f"URL does not point to an image: {image_url}")
    else:
        print(f"Failed to download image from {image_url}, status code: {response.status_code}")


# Function to scrape card details
def scrape_card_details(card_url, number, start):
    # print(f"Scraping card: {card_url}")
    res = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    card_details = {}

    card_details['id'] = start + number
    
    ## image    
    image_tag = soup.find("img", class_='game-card-image__img')
    if card_details['id'] <= 20200:
        return
    if image_tag:
        image_url = image_tag['src']
        download_image(image_url, card_details['id'])


    return card_details

# Function to scrape all cards from the main page
def scrape_all_cards(main_url, start):
    res = requests.get(main_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")

    # Find all card links
    card_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if "/cards/" in a["href"]
    ]

    print(f"Found {len(card_links)} cards.")
    card_data = []
    
    del card_links[0]
    del card_links[0]
    del card_links[0]
    del card_links[0]
    del card_links[0]
    print(card_links)
    
    number = 1
    
    for link in card_links:
        full_url = base_url + link if link.startswith("/") else link
        card_details = scrape_card_details(full_url, number, start)
        # card_id = full_url.split("/")[-2]  # Extract unique card ID
        card_data.append(card_details)
        number += 1
        if number == 218:
          number += 1
    
    return card_data


url1 = "https://www.pokemon-zone.com/sets/a1/"
url2 = "https://www.pokemon-zone.com/sets/a1a/"
url3 = "https://www.pokemon-zone.com/sets/promo-a/"
url4 = "https://www.pokemon-zone.com/sets/a2/"

# Main script
# scrape_all_cards(url1, 10000)
# scrape_all_cards(url2, 20000)
# scrape_all_cards(url3, 100000)
scrape_all_cards(url4,20100)

print("Card data saved")
