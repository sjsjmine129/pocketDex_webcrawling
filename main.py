import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

# Base URL and headers
# url = "https://www.pokemon-zone.com/sets/a4/"
url = "https://www.pokemon-zone.com/sets/promo-a/"
base_url = "https://www.pokemon-zone.com"

def get_soup_by_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(3)
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, 'html.parser')
    return soup


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
                output_dir = 'card_images'
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f'{card_name}.webp')
                img.save(output_path, 'WEBP', quality=95)
                print(f"Image for {card_name} downloaded successfully as WebP.")
            except Exception as e:
                print(f"Error processing image for {card_name}: {e}")
        else:
            print(f"URL does not point to an image: {image_url}")
    else:
        print(f"Failed to download image from {image_url}, status code: {response.status_code}")


def scrape_card_details(card_url, number):
    card_details = {}
    # card_details['id'] = 21400 + number
    card_details['id'] = 100000 + number
    
    card_details['card_set'] = 'promoA'


    print(f"Scraping card: {card_url}")
    soup = get_soup_by_selenium(card_url)
    
    # temp = soup.find_all("div", class_="card-detail__pack__details")
    # if len(temp) == 2:
    #     card_details['card_set'] = 'wisdom0'
    # elif temp[0].text.strip() == "Wisdom of Sea and Sky: Ho-Oh":
    #     card_details['card_set'] = 'wisdom1'
    # elif temp[0].text.strip() == "Wisdom of Sea and Sky: Lugia":
    #     card_details['card_set'] = 'wisdom2'

    card_details["card_name"] = soup.find("h1", class_="fs-1 text-break").text.strip()

    if url != "https://www.pokemon-zone.com/sets/promo-a/":
        rarity_count = None
        temp = soup.find("span", class_="rarity-icon")
        if temp:
            rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--diamond"))
            if(rarity_count == 0):
                rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--star")) + 4
                if(rarity_count == 4):
                    rarity_count = 19 + len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--crown"))
                    if(rarity_count == 19):
                        rarity_count = 10
                        card_details['shine'] = True
        card_details['rarity_count'] = rarity_count

    image_tag = soup.find("img", class_='game-card-image__img')
    if image_tag:
        image_url = image_tag['src']
        download_image(image_url, card_details['id'])

    print("##")
    # print(soup.prettify())  

    card_type = soup.find_all("div", class_="fw-bold")

    card_type = card_type[1]
    # print(card_type.text.strip())
    if card_type:
        card_details['card_type'] = card_type.text.strip().split(' ')[0]

    if card_details['card_type'] == 'Pokémon':
        pokemon_name = card_details['card_name'].replace(' ex', "")
        card_details['pokemon_name'] = pokemon_name
        card_details['ex'] = ' ex' in card_details['card_name']
        card_details['evolution_stage'] = card_type.text.strip().split(' | ')[1]

        hp_element = soup.find("span", class_="fs-1 lh-1")
        if hp_element:
            card_details['hp'] = hp_element.text.strip()

        card_type = soup.find("div", class_="d-flex align-items-center gap-1")
        if card_type:
            temp = card_type.find("span", class_="energy-icon")
            classes = temp.get("class", [])
            for cls in classes:
                if cls.startswith("energy-icon--type-"):
                    energy_type = cls.split("--type-")[-1].capitalize()
                    card_details['type'] = energy_type

        attack_elements = soup.find("div", class_="card-detail__content-body")
        if attack_elements:
            attack_elements = attack_elements.find_all("div", class_="attack-summary-row")
            card_details['attacks'] = []
            for attack in attack_elements:
                temp = attack.find_all("span")
                energys = []
                for a in temp:
                    classes = a.get("class", [])
                    for cls in classes:
                        if cls.startswith("energy-icon--type-"):
                            energys.append(cls.split("--type-")[-1].capitalize())

                attack_text = attack.find("div", class_="attack-summary-row__footer")
                attack_text = attack_text.text.strip() if attack_text else ""

                attack_name = attack.find("div", class_="attack-summary-row__name").text.strip()

                attack_damage = attack.find("div", class_="attack-summary-row__damage")
                attack_damage = attack_damage.text.strip() if attack_damage else ""

                card_details['attacks'].append({
                    'energies': energys,
                    'name': attack_name,
                    'damage': attack_damage,
                    'term_text': attack_text
                })

        ability_name = soup.find("div", class_="ability-summary-row__name")
        if ability_name:
            ability_description = soup.find("div", class_="ability-summary-row__description").text.strip()
            card_details['ability'] = {
                'name': ability_name.text.strip(),
                'description': ability_description
            }

        weakness_element = soup.find("div", class_="d-inline-flex gap-1 fw-bold align-items-center")
        if weakness_element:
            weakness_element = weakness_element.find("div", class_="w-24px")
            if weakness_element:
                classes = weakness_element.find("span").get("class", [])
                for cls in classes:
                    if cls.startswith("energy-icon--type-"):
                        card_details['weakness'] = cls.split("--type-")[-1].capitalize()
                        card_details['weakness_damage'] = '+20'

        retreat = 0
        temp = soup.find("div", class_="d-inline-flex gap-2 align-items-center")
        if temp:
            tempLen = temp.find_all("span", class_="energy-icon energy-icon--type-colorless")
            retreat = len(tempLen) if tempLen else 0
        card_details['retreat'] = retreat

    elif card_details['card_type'] == 'Trainer':
        trainer_type = soup.find("div", class_="heading-container d-flex justify-content-between card-detail__header")
        if trainer_type:
            temp = trainer_type.find("div", class_="fw-bold").text.strip()
            card_details['trainer_type'] = temp.split(' | ')[1]

        trainer_text = soup.find("div", class_="card-detail__desc").text.strip()
        card_details['trainer_text'] = trainer_text

    return card_details


def scrape_all_cards(main_url, output_file):
    soup = get_soup_by_selenium(main_url)
    card_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if "/cards/" in a["href"]
    ]

    print(f"Found {len(card_links)} cards.")
    # del card_links[0:5]
    del card_links[0:97]

    number = 1
    number = 93
    for link in card_links:
        try:
            full_url = base_url + link if link.startswith("/") else link
            card_details = scrape_card_details(full_url, number)

            with open(output_file, "a", encoding="utf-8") as f:
                json.dump(card_details, f, ensure_ascii=False)
                f.write("\n")

            print(f"[{number}] Saved: {card_details.get('card_name')}")
            number += 1
            if number == 218:
                number += 1
        except Exception as e:
            print(f"[{number}] Error scraping {link}: {e}")
            continue


# Main execution
output_file = "cardsData.jsonl"
scrape_all_cards(url, output_file)
print(f"Card data saved incrementally to {output_file}")
