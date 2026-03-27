"""
Unified web crawler for Pokémon cards with automatic image map generation.
Optimized to bypass Cloudflare using undetected-chromedriver.
"""

import json
import os
import random
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from PIL import Image

# 일반 셀레니움 대신 undetected_chromedriver 사용
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchWindowException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
BASE_URL = "https://www.pokemon-zone.com"
OUTPUT_DIR = "card_images"
IMAGEMAP_OUTPUT = "imageMap.js"

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
    """undetected-chromedriver를 사용하여 클라우드플레어를 우회합니다."""
    global _driver
    if _driver is not None:
        return _driver
        
    options = uc.ChromeOptions()
    
    # [중요] 클라우드플레어를 뚫으려면 브라우저 창이 무조건 눈에 보여야 합니다.
    # options.add_argument("--headless=new") # 절대 주석 해제 금지!
    
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    
    # 이전 에러 해결을 위해 사용자의 크롬 버전(146)을 고정
    _driver = uc.Chrome(options=options, version_main=146)
    _driver.set_page_load_timeout(40)
    return _driver


def quit_driver():
    global _driver
    if _driver is not None:
        try:
            _driver.quit()
        except:
            pass
        _driver = None


def restart_driver():
    quit_driver()
    return init_driver()


def get_soup_by_selenium(driver, url, wait_timeout=20, max_attempts=3):
    global _driver
    active_driver = _driver if _driver is not None else driver

    for attempt in range(1, max_attempts + 1):
        try:
            active_driver.get(url)
            
            # [클라우드플레어 우회 핵심 로직]
            time.sleep(3) # 페이지 로딩을 잠시 기다림
            if "Just a moment" in active_driver.title or "Cloudflare" in active_driver.title:
                print("🚨 클라우드플레어 감지됨! 브라우저 창에서 [사람인지 확인합니다]를 직접 클릭해주세요! (30초 대기)")
                time.sleep(30) # 사람이 클릭할 수 있도록 넉넉히 대기
            
            WebDriverWait(active_driver, wait_timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.fs-1.text-break, img.game-card-image__img")
                )
            )

            html = active_driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            if soup.find("h1", class_="fs-1 text-break") or soup.find("img", class_="game-card-image__img"):
                return soup

            print(f"Warning: Page loaded but expected content missing on {url} (attempt {attempt}/{max_attempts}).")
        except TimeoutException as e:
            print(f"Warning: Timed out waiting for content on {url} (attempt {attempt}/{max_attempts})")
        except (NoSuchWindowException, WebDriverException) as e:
            print(f"Warning: Browser session error on {url}. 브라우저 재시작 중...")
            active_driver = restart_driver()
        except Exception as e:
            print(f"Warning: Unexpected error while loading {url} (attempt {attempt}/{max_attempts}): {e}")

        time.sleep(random.uniform(1.5, 3.0))

    return None


def download_image(image_url, card_name):
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
                return
            img = Image.open(BytesIO(response.content))
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            output_path = os.path.join(OUTPUT_DIR, f"{card_name}.webp")
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "WEBP", quality=95)
            print(f"Successfully downloaded: {card_name}.webp")
    except Exception as e:
        print(f"Error downloading {card_name}: {e}")


def scrape_card_details(driver, card_url, main_url, number, adder_num):
    card_details = {"id": adder_num + number}
    card_details["card_set"] = "promoB" if adder_num == 200000 else "m_shine"


    print(f"Scraping card: {card_url}")
    soup = get_soup_by_selenium(driver, card_url)
    if soup is None:
        print(f"  Failed to load card page after retries: {card_url}")
        return None

    card_name_elem = soup.find("h1", class_="fs-1 break-words")
    if not card_name_elem:
        return None
    card_details["card_name"] = card_name_elem.text.strip()

    if "promo-a" not in main_url and "promo-b" not in main_url:
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
        download_image(image_tag["src"], card_details["id"])

    card_type_elems = soup.find_all("div", class_="font-bold")
    card_type = card_type_elems[1] if len(card_type_elems) > 1 else None
    if card_type:
        card_details["card_type"] = card_type.text.strip().split(" ")[0]

    if card_details.get("card_type") == "Pokémon":
        card_details["pokemon_name"] = card_details["card_name"].replace(" ex", "")
        card_details["ex"] = " ex" in card_details["card_name"]
        
        parts = card_type.text.strip().split(" | ")
        if len(parts) > 1:
            card_details["evolution_stage"] = parts[1]

        hp_element = soup.find("span", class_="fs-1 lh-1")
        if hp_element:
            card_details["hp"] = hp_element.text.strip()

        type_container = soup.find("div", class_="flex items-center gap-1")
        if type_container:
            temp = type_container.find("span", class_="energy-icon")
            if temp:
                for cls in temp.get("class", []):
                    if cls.startswith("energy-icon--type-"):
                        card_details["type"] = cls.split("--type-")[-1].capitalize()
                        break

        attack_elements = soup.find("div", class_="card-detail__content-body")
        if attack_elements:
            card_details["attacks"] = []
            for attack in attack_elements.find_all("div", class_="attack-summary-row"):
                energys = []
                for a in attack.find_all("span"):
                    for cls in a.get("class", []):
                        if cls.startswith("energy-icon--type-"):
                            energys.append(cls.split("--type-")[-1].capitalize())
                
                footer = attack.find("div", class_="attack-summary-row__footer")
                attack_name_elem = attack.find("div", class_="attack-summary-row__name")
                damage_elem = attack.find("div", class_="attack-summary-row__damage")
                
                if attack_name_elem:
                    card_details["attacks"].append({
                        "energies": energys,
                        "name": attack_name_elem.text.strip(),
                        "damage": damage_elem.text.strip() if damage_elem else "",
                        "term_text": footer.text.strip() if footer else "",
                    })

        ability_name = soup.find("div", class_="ability-summary-row__name")
        if ability_name:
            desc_elem = soup.find("div", class_="ability-summary-row__description")
            card_details["ability"] = {
                "name": ability_name.text.strip(),
                "description": desc_elem.text.strip() if desc_elem else "",
            }

        weakness_elem = soup.find("div", class_="inline-flex gap-1 font-bold items-center")
        if weakness_elem:
            w24 = weakness_elem.find("div", class_="w-24px")
            if w24 and w24.find("span"):
                for cls in w24.find("span").get("class", []):
                    if cls.startswith("energy-icon--type-"):
                        card_details["weakness"] = cls.split("--type-")[-1].capitalize()
                        card_details["weakness_damage"] = "+20"
                        break

        retreat = 0
        retreat_container = soup.find("div", class_="inline-flex gap-2 items-center")
        if retreat_container:
            colorless = retreat_container.find_all("span", class_="energy-icon energy-icon--type-colorless")
            retreat = len(colorless) if colorless else 0
        card_details["retreat"] = retreat

    elif card_details.get("card_type") == "Trainer":
        header = soup.find("div", class_="heading-container d-flex justify-content-between card-detail__header")
        if header and header.find("div", class_="font-bold"):
            parts = header.find("div", class_="font-bold").text.strip().split(" | ")
            if len(parts) > 1:
                card_details["trainer_type"] = parts[1]
        desc = soup.find("div", class_="card-detail__desc")
        card_details["trainer_text"] = desc.text.strip() if desc else ""

    return card_details


def scrape_all_cards(driver, main_url, output_file, adder_num):
    collected_ids = []
    soup = get_soup_by_selenium(driver, main_url)
    if soup is None:
        print(f"Could not load set listing (blocked or timeout): {main_url}")
        return collected_ids

    card_links = [a["href"] for a in soup.find_all("a", href=True) if "/cards/" in a["href"]]
    print(f"Found {len(card_links)} cards.")
    del card_links[0:5]
    number = 1

    for link in card_links:
        try:
            if number < 41:
                number += 1
                continue
            
            full_url = BASE_URL + link if link.startswith("/") else link
            card_details = scrape_card_details(driver, full_url, main_url, number, adder_num)
            if card_details is None:
                print(f"[{number}] Skipped: {link}")
                number += 1
                continue

            with open(output_file, "a", encoding="utf-8") as f:
                json.dump(card_details, f, ensure_ascii=False)
                f.write(",\n")

            cid = card_details.get("id")
            if cid is not None:
                collected_ids.append(cid)

            print(f"[{number}] Saved: {card_details.get('card_name')}")
            number += 1
            time.sleep(random.uniform(2.0, 4.0)) # 차단 방지를 위해 대기 시간 약간 증가

        except Exception as e:
            print(f"[{number}] Error scraping {link}: {e}")
            continue

    return collected_ids


def generate_js_file(card_ids, output_file=IMAGEMAP_OUTPUT):
    if not card_ids:
        return
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("const imageMap = {\n")
        for cid in sorted(card_ids):
            f.write(f"  {cid}: require('assets/CardImages/{cid}.webp'),\n")
        f.write("};\n\nexport default imageMap;\n")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    SCRAPE_TARGETS = [
        # ("http://pokemon-zone.com/sets/b2b/", "cardsData.json", 101300),
        ("https://www.pokemon-zone.com/sets/promo-b/", "cardsData_promo.json", 200000),
    ]

    all_collected_ids = []

    try:
        driver = init_driver()

        for main_url, output_file, adder_num in SCRAPE_TARGETS:
            print(f"\n--- Scraping {main_url} ---")
            ids = scrape_all_cards(driver, main_url, output_file, adder_num)
            all_collected_ids.extend(ids)

        if all_collected_ids:
            generate_js_file(all_collected_ids)
            print(f"Image map generated for {len(all_collected_ids)} cards.")
    finally:
        quit_driver()