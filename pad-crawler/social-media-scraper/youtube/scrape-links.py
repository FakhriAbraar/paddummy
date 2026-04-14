# STATUS: SUDAH FUNGSIONAL, BISA HEADLESS BROWSER

# Example endpoint: https://www.youtube.com/results?search_query=python+tutorial

import re
import json
import time
import random
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# ========================
# KONFIGURASI
# ========================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "data" / "hasil_youtube.json"

TARGET_TAGS = ["prabowo+subianto", "anies+baswedan", "ganjar+pranowo"]
MAX_VIDEO_PER_TAG = 200
MAX_SCROLL = 10
HEADLESS_FLAG = True # False => MUNCUL GUI, True => Only Terminal

# ========================
# HUMAN SCROLL
# ========================
def human_scroll(page):
    scroll_steps = random.randint(6, 12)

    print("  [Scroll seperti manusia...]")
    for _ in range(scroll_steps):
        distance = random.randint(400, 1000)
        page.mouse.wheel(0, distance)
        time.sleep(random.uniform(0.2, 0.5))

    time.sleep(random.uniform(1.5, 3.0))


# ========================
# SCRAPE YOUTUBE
# ========================
def scrape_youtube():
    hasil_final = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS_FLAG,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--lang=id-ID',
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768},
            locale='id-ID',
            timezone_id='Asia/Jakarta',
        )
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['id-ID','id','en-US','en']});
            window.chrome = {runtime: {}};
        """)

        page = context.new_page()

        # Stealth: buka google.com dulu
        page.goto("https://www.google.com")
        time.sleep(2)
        # Lalu ke root YouTube
        page.goto("https://www.youtube.com/")
        print('Berada di root YouTube, menunggu lebih lama...')
        time.sleep(10)  # Delay lebih lama di root

        for tag in TARGET_TAGS:
            print(f"\n--- Menjelajahi #{tag} ---")

            # https://www.youtube.com/results?search_query=python+tutorial
            url = f"https://www.youtube.com/results?search_query={tag}"
            page.goto(url)

            time.sleep(5)

            links_found = set()
            retry_scroll = 0

            while len(links_found) < MAX_VIDEO_PER_TAG and retry_scroll < MAX_SCROLL:
                
                elements = page.query_selector_all("a")

                for el in elements:
                    if len(links_found) >= MAX_VIDEO_PER_TAG:
                        break

                    href = el.get_attribute("href")

                    if not href:
                        continue

                    if "/watch" in href:
                        shortcode = re.search(r'v=([^&]+)', href)
                        if shortcode:
                            full_url = f"https://www.youtube.com/watch?v={shortcode.group(1)}"
                        links_found.add(full_url)

                print(f"  Total sementara: {len(links_found)}")

                if len(links_found) < MAX_VIDEO_PER_TAG:
                    try:
                        page.locator("ytd-search.style-scope.ytd-page-manager").scroll_into_view_if_needed()
                    except Exception:
                        pass
                    human_scroll(page)
                    retry_scroll += 1
                else:
                    break

            print(f"Selesai. Didapat {len(links_found)} video")
            hasil_final[tag] = list(links_found)

        browser.close()

    return hasil_final


# ========================
# MAIN
# ========================
if __name__ == "__main__":

    data = scrape_youtube()

    output = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "target_tags": TARGET_TAGS,
            "max_video_per_tag": MAX_VIDEO_PER_TAG
        },
        "data": data
    }

    if data:
        # Rename hasil_youtube.json to hasil_youtube_N.json (N = last number + 1)
        data_dir = OUTPUT_PATH.parent
        base_name = "hasil_youtube"
        existing = list(data_dir.glob(f"{base_name}_*.json"))
        max_num = 0
        for f in existing:
            try:
                num = int(f.stem.split('_')[-1])
                if num > max_num:
                    max_num = num
            except Exception:
                continue
        new_path = data_dir / f"{base_name}_{max_num+1}.json"

        if OUTPUT_PATH.exists():
            OUTPUT_PATH.rename(new_path)

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print("\n" + "="*30)
        print("SCRAPING YOUTUBE SELESAI")
        print(f"Data disimpan di: {OUTPUT_PATH}")
        print("="*30)