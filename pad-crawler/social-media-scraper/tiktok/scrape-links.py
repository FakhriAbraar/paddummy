# STATUS: SUDAH FUNGSIONAL

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

TARGET_TAGS = ["prabowosubianto", "aniesbaswedan", "ganjarpranowo"]
MAX_VIDEO_PER_TAG = 200
MAX_EMPTY_SCROLL = 10

# ========================
# HUMAN SCROLL
# ========================
def human_scroll(page):
    scroll_steps = random.randint(3, 6)

    print("  [Scroll seperti manusia...]")
    for _ in range(scroll_steps):
        distance = random.randint(200, 500)
        page.mouse.wheel(0, distance)
        time.sleep(random.uniform(0.2, 0.5))

    time.sleep(random.uniform(1.5, 3.0))


# ========================
# SCRAPE TIKTOK
# ========================
def scrape_tiktok():
    hasil_final = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
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
        # Lalu ke root TikTok
        page.goto("https://www.tiktok.com/")
        print('Berada di root TikTok, menunggu lebih lama...')
        time.sleep(10)  # Delay lebih lama di root

        # Simulasi interaksi user di root TikTok
        print('Simulasi interaksi user di root TikTok...')
        for _ in range(3):
            try:
                page.locator("#main-content-explore_page").click(timeout=2000)
            except Exception:
                pass
            # human_scroll(page)
            page.mouse.wheel(0, random.randint(300, 600))
            time.sleep(random.uniform(1, 2))
        # Coba klik logo/home jika ada
        try:
            home_btn = page.query_selector('a[href="/"]')
            if home_btn and home_btn.is_visible():
                home_btn.click()
                time.sleep(2)
        except Exception:
            pass

        for tag in TARGET_TAGS:
            print(f"\n--- Menjelajahi #{tag} ---")

            url = f"https://www.tiktok.com/tag/{tag}"
            page.goto(url)

            if tag == TARGET_TAGS[0]:
                print("Selesaikan CAPTCHA terlebih dahulu!")
                time.sleep(5)

            time.sleep(5)

            links_found = set()
            retry_scroll = 0

            while len(links_found) < MAX_VIDEO_PER_TAG and retry_scroll < MAX_EMPTY_SCROLL:
                
                elements = page.query_selector_all("a")

                for el in elements:
                    if len(links_found) >= MAX_VIDEO_PER_TAG:
                        break

                    href = el.get_attribute("href")

                    if not href:
                        continue

                    # filter khusus video
                    if "/video/" in href:
                        if href.startswith("http"):
                            full_url = href
                        else:
                            full_url = f"https://www.tiktok.com{href}"

                        links_found.add(full_url)

                print(f"  Total sementara: {len(links_found)}")

                if len(links_found) < MAX_VIDEO_PER_TAG:
                    try:
                        page.locator("#main-content-challenge").click(timeout=2000)
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

    data = scrape_tiktok()

    output = {
        "metadata": {
            "scraped_at": datetime.now().isoformat(),
            "target_tags": TARGET_TAGS,
            "max_video_per_tag": MAX_VIDEO_PER_TAG
        },
        "data": data
    }

    output_path = BASE_DIR / "data" / "hasil_tiktok.json"

    if data:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)

        print("\n" + "="*30)
        print("SCRAPING TIKTOK SELESAI")
        print(f"Data disimpan di: {output_path}")
        print("="*30)