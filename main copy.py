import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import re
import json

# URL of the card set
# url = "https://www.pokemon-zone.com/sets/genetic-apex/"
url = "https://www.pokemon-zone.com/sets/a1a/"
# url = "https://www.pokemon-zone.com/sets/promo-a/"
base_url = "https://www.pokemon-zone.com"

# Add headers to mimic a browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to scrape card details from individual card pages
def scrape_card_details(card_url):
    res = requests.get(card_url, headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')
    
    card_details = {}
    
    # Extract card number
    widget = soup.find("div", class_="elementor-element-22be0f5").find("ul", class_="custom-taxo-terms-list")
    card_set = widget.find("p").text.strip()
    number = widget.find("small", class_="number").text.strip()
    # booster = widget.find("small", class_="booster")
    # if booster:
    #   booster = booster.text.strip()
    # else:
    #   booster = "All"
    # card_set = card_set.replace(" (A1)", "")
    # number = int(number.replace("#",""))
    
    # if card_set == "Genetic Apex":
    #   card_details['id'] = 10000+number
    # elif card_set == "Promo-A":
    card_details['id'] = 20000+number
    card_details['card_set'] = 'mythical'
    card_details['booster'] = 'mythical'
    
    # Extract card name
    card_details["card_name"] = soup.find("h1", class_="elementor-heading-title").text.strip()

    # Extract rarity
    rarity_count = None
    temp = soup.find("ul", class_="custom-taxo-terms-list--rarity")
    if temp:
      tempLen = temp.find_all("i", class_="rarity icon-diamond")
      if tempLen:
        rarity_count = len(temp.find_all("i", class_="rarity icon-diamond"))
        if rarity_count != 0:
          card_details['rarity'] = "diamond"
        else:
          rarity_count = len(temp.find_all("i", class_="rarity icon-star"))
          if rarity_count != 0:
            card_details['rarity'] = "star"
          elif rarity_count != 0:
            rarity_count = len(temp.find_all("i", class_="rarity icon-crown"))
            card_details['rarity'] = "crown"
          else:
            card_details['rarity'] = "None"
    

    card_details['rarity_count'] = rarity_count
    
    # # Extract image URL
    pattern = re.compile(r'attachment-large size-large wp-image-\d+')
    image_tag = soup.find("img", class_=pattern)
    if image_tag:
        image_url = image_tag['src']
        download_image(image_url, card_details['id'])
    
    #card type
    card_type = soup.find("div", class_="elementor-element-1a80102")
    if card_type:
      card_details['card_type'] = card_type.text.strip()
      
    #pokemonCard
    if card_details['card_type'] == 'Pokémon':
      # Extract pokemon name
      pokemon_name = card_details['card_name'].replace(' ex',"")
      card_details['pokemon_name'] = pokemon_name
      
      ex = card_details['card_name'].find(' ex')
      if ex != -1:
        card_details['ex'] = True
      else:
        card_details['ex'] = False
      
      # Extract evolution stage
      evolution_stage = soup.find("ul", class_="custom-taxo-terms-list custom-taxo-terms-list--stage").text.strip().replace('|', '')
      card_details['evolution_stage'] = evolution_stage
      
      # Extract HP
      hp_element = soup.find("div", class_="elementor-element-45378ac")
      if hp_element:
          card_details['hp'] = hp_element.text.strip().replace('HP', '').strip()

      # Extract type (for example: Grass, Fire, etc.)
      type_element = soup.find("ul", class_="custom-taxo-terms-list--pokemon-types")
      if type_element:
          card_details['type'] = type_element.find("span", class_="reltooltip").text.strip()

      # Extract attack information
      attack_elements = soup.find("ul", class_="custom-taxo-terms-list--attacks")
      if attack_elements:
        attack_elements = attack_elements.find_all("li", class_="flex-column align-start")
        card_details['attacks'] = []
        for attack in attack_elements:
          temp = attack.find_all("span", class_="reltooltip")
          energys = [a.text.strip() for a in temp]
          
          attack_text = attack.find("div", class_="flex").text.strip()
          parts = attack_text.split('|')
          # print(parts)
          if len(parts) >= 3:
              attack_name = parts[1].strip()  # The attack name is the second part
              damage = parts[2].strip()        # The damage is the third part
          if len(parts) == 2:
              attack_name = parts[1].strip()  # The attack name is the second part
              damage = None        # The damage is the third part
              
          term_text = attack.find("p", class_="term-text")
          if term_text:
            term_text = term_text.text.strip()
          else:
            term_text = None
            
          card_details['attacks'].append({'energys': energys, 'name': attack_name, 'damage': damage, 'term_text': term_text})
      
      # Extract Ability
      ability = soup.find("ul", class_="custom-taxo-terms-list--ability")
      if ability:
        ability_name = ability.find("p").text.split('|')[-1].strip()
        ability_description = ability.find("p", class_="term-text").text.strip()
        card_details['ability'] = {'name': ability_name, 'description': ability_description}

      
      # Extract weakness
      weakness_element = soup.find("ul", class_="custom-taxo-terms-list--pokemon-weakness")
      if weakness_element:
          card_details['weakness'] = weakness_element.find("span", class_="reltooltip").text.strip()
      
      # Extract weakness damage
      weakness_damage = soup.find("div", class_="elementor-element-251116e")
      if weakness_damage:
          card_details['weakness_damage'] = weakness_damage.text.strip()
          
      # Extract retreat
      retreat = 0
      temp = soup.find("ul", class_="custom-taxo-terms-list custom-taxo-terms-list--retreat")
      if temp:
          tempLen = temp.find_all("i", class_="energy icon-colorless")
          if tempLen:
              retreat = len(tempLen)
          else:
              retreat = 0
            
      card_details['retreat'] = retreat
      
    #trainerCard
    if card_details['card_type'] == 'Trainer':
      # Extract trainer_type
      trainer_type = soup.find("div", class_="elementor-element-027768d").text.strip().replace('|', '').replace('\xa0', '').strip()
      card_details['trainer_type'] = trainer_type
      
      # Extract trainer_text
      trainer_text = soup.find("div", class_="elementor-element-53ba761").text.strip()
      card_details['trainer_text'] = trainer_text
      # print(trainer_text)

    return card_details

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
                img.save(f'card_images/100248.png', 'PNG')
                # print(f"Image for {card_name} downloaded successfully as PNG.")
            except Exception as e:
                print(f"Error processing image for {card_name}: {e}")
        else:
            print(f"URL does not point to an image: {image_url}")
    else:
        print(f"Failed to download image from {image_url}, status code: {response.status_code}")

# Function to scrape all cards from the main page
def scrape_all_cards(main_url):
    res = requests.get(main_url, headers=headers)
    soup = BeautifulSoup(res.content, 'html.parser')

    # Find all card links (update based on actual HTML structure)
    card_links = [a['href'] for a in soup.find_all("a", class_="elementor-element elementor-element-b3470db e-con-full e-transform e-flex e-con e-parent", href=True)]

    print(card_links)
    card_data = {}
    for link in card_links:
        card_details = scrape_card_details(link)
        card_id = card_details['id']  # Use the 'id' as the key
        card_data[card_id] = card_details
    # card_data[100447] = scrape_card_details(card_links[246])
    
    # card_data.append(scrape_card_details(card_links[0])) #다이아 하나 이상해씨
    # card_data.append(scrape_card_details(card_links[3])) 
    # card_data.append(scrape_card_details(card_links[5])) 
    # card_data.append(scrape_card_details(card_links[19])) 
    # card_data.append(scrape_card_details(card_links[223])) #웅이
    # card_data.append(scrape_card_details(card_links[202])) #
    # card_data.append(scrape_card_details(card_links[250])) #이상해꽃 ex 2star
    # card_data.append(scrape_card_details(card_links[285])) #크라운 뮤츠

    # print(card_data)
    return card_data

# Scrape all cards
cards = scrape_all_cards(url)

output_file = "cardsData.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(cards, f, ensure_ascii=False, indent=4)

print(f"Card data saved to {output_file}")
