import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import json
import re

# Base URL and headers

url = "https://www.pokemon-zone.com/sets/a1/"
# url = "https://www.pokemon-zone.com/sets/a1a/"
# url = "https://www.pokemon-zone.com/sets/promo-a/"
# url = "https://www.pokemon-zone.com/sets/a2/"

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
                img.save(f'card_images/{card_name}.webp', 'WEBP')
                # print(f"Image for {card_name} downloaded successfully as PNG.")
            except Exception as e:
                print(f"Error processing image for {card_name}: {e}")
        else:
            print(f"URL does not point to an image: {image_url}")
    else:
        print(f"Failed to download image from {image_url}, status code: {response.status_code}")


# Function to scrape card details
def scrape_card_details(card_url, number):
    # print(f"Scraping card: {card_url}")
    res = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(res.content, "html.parser")
    card_details = {}

    card_details['id'] = 10000+number
    # card_details['id'] = 20000+number
    # card_details['card_set'] = 'mythical'
    # card_details['id'] = 100000+number
    # card_details['card_set'] = 'promoA'

    # card_details['id'] = 20100+number
    
    # ##
    # # temp = soup.find_all("div", class_="card-detail__pack__details")
    # # if len(temp) == 2:
    # #   card_details['card_set'] = 'smack0'
    # # elif temp[0].text.strip() == "Space-Time Smackdown: Dialga":
    # #   card_details['card_set'] = 'smack1'
    # # elif temp[0].text.strip() == "Space-Time Smackdown: Palkia":
    # #   card_details['card_set'] = 'smack2'
    
    # card_details['card_set'] = 'promoA'
    
    # card_details["card_name"] = soup.find("h1", class_="fs-1 text-break").text.strip()
    
    
    # rarity_count = None
    # temp = soup.find("span", class_="rarity-icon")
    # if temp:

    #   rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--diamond"))
    #   if(rarity_count == 0):
    #     rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--star")) + 4
    #     if(rarity_count == 4):
    #       rarity_count = 7+ len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--crown"))
    

    # card_details['rarity_count'] = rarity_count
    
    
    ## image    
    image_tag = soup.find("img", class_='game-card-image__img')
    if image_tag:
        image_url = image_tag['src']
        download_image(image_url, card_details['id'])

    
    # card_type = soup.find("div", class_="fw-bold")
    # if card_type:
    #   card_details['card_type'] = card_type.text.strip().split(' ')[0]
    
    # #pokemonCard
    # if card_details['card_type'] == 'Pokémon':
    #   # Extract pokemon name
    #   pokemon_name = card_details['card_name'].replace(' ex',"")
    #   card_details['pokemon_name'] = pokemon_name
      
    #   ex = card_details['card_name'].find(' ex')
    #   if ex != -1:
    #     card_details['ex'] = True
    #   else:
    #     card_details['ex'] = False
        
       
    #   card_details['evolution_stage'] = card_type.text.strip().split(' | ')[1]
      
      
    #   hp_element = soup.find("span", class_="fs-1 lh-1")
    #   if hp_element:
    #       card_details['hp'] = hp_element.text.strip()
      
      
    #   #pokemon type
    #   card_type = soup.find("div", class_="d-flex align-items-center gap-1")
    #   if card_type:
    #     temp = card_type.find("span", class_="energy-icon")
    #     classes = temp.get("class", [])

    #     for cls in classes:
    #         if cls.startswith("energy-icon--type-"):
    #             energy_type = cls.split("--type-")[-1]
    #             energy_type = energy_type.capitalize()
    #             card_details['type'] = energy_type

    #   # Extract attack information
    #   attack_elements = soup.find("div", class_="card-detail__content-body")
    #   if attack_elements:
    #     attack_elements = attack_elements.find_all("div", class_="attack-summary-row")
    #     card_details['attacks'] = []
        
    #     for attack in attack_elements:
    #       temp = attack.find_all("span")
          
    #       energys = []
    #       for a in temp:
    #         classes = a.get("class", [])
    #         for cls in classes:
    #           if cls.startswith("energy-icon--type-"):
    #               energy_type = cls.split("--type-")[-1]
    #               energy_type = energy_type.capitalize()
    #               energys.append(energy_type)
          
    #       attack_text = attack.find("div", class_="attack-summary-row__footer")
    #       if attack_text:
    #         attack_text = attack_text.text.strip()
          
    #       attack_name = attack.find("div", class_="attack-summary-row__name").text.strip()
          
    #       attack_damage = attack.find("div", class_="attack-summary-row__damage")
    #       if attack_damage:
    #         attack_damage = attack_damage.text.strip()
          
    #       card_details['attacks'].append({'energies': energys, 'name': attack_name, 'damage': attack_damage, 'term_text': attack_text})
          
    #   # Extract Ability
    #   ability_name = soup.find("div", class_="ability-summary-row__name")
    #   if ability_name:
    #     ability_name = ability_name.text.strip()
    #     ability_description = soup.find("div", class_="ability-summary-row__description").text.strip()
    #     card_details['ability'] = {'name': ability_name, 'description': ability_description}

    #   # Extract weakness
    #   weakness_element = soup.find("div", class_="d-inline-flex gap-1 fw-bold align-items-center")
    #   if weakness_element:
    #     weakness_element = weakness_element.find("div", class_="w-24px")

    #     if weakness_element:
    #       classes = weakness_element.find("span").get("class", [])
    #       for cls in classes:
    #         if cls.startswith("energy-icon--type-"):
    #             weakness_element = cls.split("--type-")[-1]
    #             weakness_element = weakness_element.capitalize()
    #             card_details['weakness'] = weakness_element
    #             card_details['weakness_damage'] = '+20'
    
    #   # Extract retreat
    #   retreat = 0
    #   temp = soup.find("div", class_="d-inline-flex gap-2 align-items-center")
    #   if temp:
    #       tempLen = temp.find_all("span", class_="energy-icon energy-icon--type-colorless")
    #       if tempLen:
    #           retreat = len(tempLen)
    #       else:
    #           retreat = 0
    #   card_details['retreat'] = retreat
      
      
    # elif card_details['card_type'] == 'Trainer':
    #   # Extract trainer_type
    #   trainer_type = soup.find("div", class_="heading-container d-flex justify-content-between card-detail__header")
    #   if trainer_type:
    #     temp = trainer_type.find("div", class_="fw-bold").text.strip()
    #     card_details['trainer_type'] = temp.split(' | ')[1]
      
    #   # Extract trainer_text
    #   trainer_text = soup.find("div", class_="card-detail__desc").text.strip()
    #   card_details['trainer_text'] = trainer_text

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
        card_details = scrape_card_details(full_url, number)
        # card_id = full_url.split("/")[-2]  # Extract unique card ID
        card_data.append(card_details)
        number += 1
        if number == 218:
          number += 1
    
    return card_data

# Main script
cards = scrape_all_cards(url)

# Save to JSON
output_file = "cardsData.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=4)

print(f"Card data saved to {output_file}")
