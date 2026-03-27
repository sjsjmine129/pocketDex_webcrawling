"""
Unified web crawler for Pokémon cards with automatic image map generation.
Optimized for speed: single WebDriver session, session-based image downloads,
explicit waits, and anti-bot randomized delays.
"""

import json
import os
import random
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
BASE_URL = "https://www.pokemon-zone.com"
OUTPUT_DIR = "card_images"
IMAGEMAP_OUTPUT = "imageMap.js"

# Global session for connection pooling (Keep-Alive)
_http_session = None
_driver = None


def get_http_session():
    """Get or create the global requests Session for image downloads."""
    global _http_session
    if _http_session is None:
        _http_session = requests.Session()
        _http_session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.pokemon-zone.com/",
        })
    return _http_session


def init_driver():
    """Initialize Chrome WebDriver once. Call at script start."""
    global _driver
    if _driver is not None:
        return _driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    _driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options,
    )
    return _driver


def quit_driver():
    """Quit the WebDriver. Call at script end."""
    global _driver
    if _driver is not None:
        _driver.quit()
        _driver = None


def get_soup_by_selenium(driver, url, wait_timeout=15):
    """
    Navigate to URL and return BeautifulSoup. Uses explicit waits instead of
    fixed sleep. Waits for card name or image element to be present.
    """
    driver.get(url)
    try:
        # CSS selector with comma = OR: wait for either card name or image
        WebDriverWait(driver, wait_timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1.fs-1.text-break, img.game-card-image__img")
            )
        )
    except Exception as e:
        print(f"Warning: Timed out waiting for content on {url}: {e}")
    html = driver.page_source
    return BeautifulSoup(html, "html.parser")


def download_image(image_url, card_name):
    """Download image using shared Session for connection pooling."""
    if image_url.startswith("//"):
        full_image_url = "https:" + image_url
    elif image_url.startswith("/"):
        full_image_url = BASE_URL + image_url
    else:
        full_image_url = image_url

    session = get_http_session()
    try:
        response = session.get(full_image_url, timeout=15)
        if response.status_code == 200:
            if len(response.content) < 1000:
                print(f"Warning: Downloaded data for {card_name} is too small.")
                return
            img = Image.open(BytesIO(response.content))
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, f"{card_name}.webp")
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "WEBP", quality=95)
            print(f"Successfully downloaded: {card_name}.webp")
        else:
            print(f"HTTP Error {response.status_code} for URL: {full_image_url}")
    except Exception as e:
        print(f"Error downloading {card_name}: {e}")


def scrape_card_details(driver, card_url, main_url, number, adder_num):
    """Scrape a single card's details. Uses shared driver instance."""
    card_details = {}
    card_details["id"] = adder_num + number

    if adder_num == 200000:
        card_details["card_set"] = "promoB"
    else:
        card_details["card_set"] = "m_shine"

    print(f"Scraping card: {card_url}")
    soup = get_soup_by_selenium(driver, card_url)

    temp = soup.find_all("div", class_="card-detail__pack__details")
    card_details["card_name"] = soup.find("h1", class_="fs-1 text-break").text.strip()

    if main_url != "https://www.pokemon-zone.com/sets/promo-a/" and main_url != "https://www.pokemon-zone.com/sets/promo-b/":
        rarity_count = None
        temp = soup.find("span", class_="rarity-icon")
        if temp:
            rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--diamond"))
            if rarity_count == 0:
                rarity_count = len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--star")) + 4
                if rarity_count == 4:
                    rarity_count = 19 + len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--crown"))
                    if rarity_count == 19:
                        rarity_count = 9 + len(temp.find_all("span", class_="rarity-icon__icon rarity-icon__icon--shiny"))
                        card_details["shine"] = True
            card_details["rarity_count"] = rarity_count

    image_tag = soup.find("img", class_="game-card-image__img")
    if image_tag:
        image_url = image_tag["src"]
        download_image(image_url, card_details["id"])

    card_type_elems = soup.find_all("div", class_="fw-bold")
    card_type = card_type_elems[1] if len(card_type_elems) > 1 else None
    if card_type:
        card_details["card_type"] = card_type.text.strip().split(" ")[0]

    if card_details.get("card_type") == "Pokémon":
        pokemon_name = card_details["card_name"].replace(" ex", "")
        card_details["pokemon_name"] = pokemon_name
        card_details["ex"] = " ex" in card_details["card_name"]
        card_details["evolution_stage"] = card_type.text.strip().split(" | ")[1]

        hp_element = soup.find("span", class_="fs-1 lh-1")
        if hp_element:
            card_details["hp"] = hp_element.text.strip()

        type_container = soup.find("div", class_="d-flex align-items-center gap-1")
        if type_container:
            temp = type_container.find("span", class_="energy-icon")
            if temp:
                classes = temp.get("class", [])
                for cls in classes:
                    if cls.startswith("energy-icon--type-"):
                        card_details["type"] = cls.split("--type-")[-1].capitalize()
                        break

        attack_elements = soup.find("div", class_="card-detail__content-body")
        if attack_elements:
            attack_rows = attack_elements.find_all("div", class_="attack-summary-row")
            card_details["attacks"] = []
            for attack in attack_rows:
                temp_spans = attack.find_all("span")
                energys = []
                for a in temp_spans:
                    for cls in a.get("class", []):
                        if cls.startswith("energy-icon--type-"):
                            energys.append(cls.split("--type-")[-1].capitalize())
                footer = attack.find("div", class_="attack-summary-row__footer")
                attack_text = footer.text.strip() if footer else ""
                attack_name = attack.find("div", class_="attack-summary-row__name").text.strip()
                damage_elem = attack.find("div", class_="attack-summary-row__damage")
                attack_damage = damage_elem.text.strip() if damage_elem else ""
                card_details["attacks"].append({
                    "energies": energys,
                    "name": attack_name,
                    "damage": attack_damage,
                    "term_text": attack_text,
                })

        ability_name = soup.find("div", class_="ability-summary-row__name")
        if ability_name:
            desc_elem = soup.find("div", class_="ability-summary-row__description")
            ability_description = desc_elem.text.strip() if desc_elem else ""
            card_details["ability"] = {
                "name": ability_name.text.strip(),
                "description": ability_description,
            }

        weakness_elem = soup.find("div", class_="d-inline-flex gap-1 fw-bold align-items-center")
        if weakness_elem:
            w24 = weakness_elem.find("div", class_="w-24px")
            if w24:
                span = w24.find("span")
                if span:
                    for cls in span.get("class", []):
                        if cls.startswith("energy-icon--type-"):
                            card_details["weakness"] = cls.split("--type-")[-1].capitalize()
                            card_details["weakness_damage"] = "+20"
                            break

        retreat = 0
        retreat_container = soup.find("div", class_="d-inline-flex gap-2 align-items-center")
        if retreat_container:
            colorless = retreat_container.find_all("span", class_="energy-icon energy-icon--type-colorless")
            retreat = len(colorless) if colorless else 0
        card_details["retreat"] = retreat

    elif card_details.get("card_type") == "Trainer":
        header = soup.find("div", class_="heading-container d-flex justify-content-between card-detail__header")
        if header:
            fw = header.find("div", class_="fw-bold")
            if fw:
                card_details["trainer_type"] = fw.text.strip().split(" | ")[1]
        desc = soup.find("div", class_="card-detail__desc")
        card_details["trainer_text"] = desc.text.strip() if desc else ""

    return card_details


def scrape_all_cards(driver, main_url, output_file, adder_num):
    """
    Scrape all cards from a set. Returns a list of successfully collected
    card IDs for image map generation.
    """
    collected_ids = []

    soup = get_soup_by_selenium(driver, main_url)
    card_links = [
        a["href"]
        for a in soup.find_all("a", href=True)
        if "/cards/" in a["href"]
    ]

    print(f"Found {len(card_links)} cards.")
    del card_links[0:5]
    number = 1

    for link in card_links:
        try:
            full_url = BASE_URL + link if link.startswith("/") else link
            card_details = scrape_card_details(driver, full_url, main_url, number, adder_num)

            with open(output_file, "a", encoding="utf-8") as f:
                json.dump(card_details, f, ensure_ascii=False)
                f.write(",\n")

            cid = card_details.get("id")
            if cid is not None:
                collected_ids.append(cid)

            print(f"[{number}] Saved: {card_details.get('card_name')}")
            number += 1

            # Anti-bot: randomized delay between page navigations
            time.sleep(random.uniform(1.0, 2.5))

        except Exception as e:
            print(f"[{number}] Error scraping {link}: {e}")
            continue

    return collected_ids


def generate_js_file(card_ids, output_file=IMAGEMAP_OUTPUT):
    """
    Generate JavaScript image map for React Native project.
    Accepts a list of card IDs so only actually downloaded images are included
    (handles non-sequential IDs across b2 and promo-b sets).
    """
    if not card_ids:
        print("No card IDs provided; skipping image map generation.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("const imageMap = {\n")
        for cid in sorted(card_ids):
            f.write(f"  {cid}: require('assets/CardImages/{cid}.webp'),\n")
        f.write("};\n\nexport default imageMap;\n")
    print(f"JavaScript file '{output_file}' has been generated with {len(card_ids)} entries.")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Both sets scraped sequentially with a single WebDriver session
    SCRAPE_TARGETS = [
        ("http://pokemon-zone.com/sets/b2b/", "cardsData.json", 101300),
        ("https://www.pokemon-zone.com/sets/promo-b/", "cardsData_promo.json", 200000),
    ]

    all_collected_ids = []

    try:
        driver = init_driver()

        for main_url, output_file, adder_num in SCRAPE_TARGETS:
            print(f"\n--- Scraping {main_url} ---")
            ids = scrape_all_cards(driver, main_url, output_file, adder_num)
            all_collected_ids.extend(ids)
            print(f"Card data saved incrementally to {output_file}")

        if all_collected_ids:
            generate_js_file(all_collected_ids)
            print(f"Image map generated for {len(all_collected_ids)} cards.")
        else:
            print("No card IDs collected; skipping image map generation.")
    finally:
        quit_driver()

