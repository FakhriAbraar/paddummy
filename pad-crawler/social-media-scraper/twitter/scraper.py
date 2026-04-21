# STATUS: SUDAH FUNGSIONAL, DARI AWAL HINGGA AKHIR, BELUM BISA HEADLESS, LOGIN PERLU MANUAL

import os
import csv
import time
import json
import random
import requests
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

# === 1. Parsing Argument ===
parser = argparse.ArgumentParser(
    description="""Contoh penggunaan program:
python scraper.py --keyword "komdigi" "bahlil" --target_post 100
""",
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "--keyword",
    nargs="+",  # ini membuatnya jadi list
    required=True,
    help="Daftar keyword (pisahkan dengan spasi)"
)

parser.add_argument(
    "--target_post",
    type=int,
    required=True,
    help="Jumlah target post"
)

args = parser.parse_args()

keyword = args.keyword
search_query = " OR ".join(keyword)
target_post = args.target_post

# === 2. Setup Constant Variables ===
BASE_DIR = Path(__file__).resolve().parent
SESSION_FILE = BASE_DIR / "twitter_session.json"

scraped_at = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

SOURCE_PATH = BASE_DIR / "tweets-data" / f"media-sosial-twitter-selected-field-data-{scraped_at}.csv"
DEST_PATH = BASE_DIR / "tweets-data" / f"media-sosial-twitter-selected-field-data-{scraped_at}.json"

DOWNLOAD_DIR = Path("downloads")
os.makedirs("downloads", exist_ok=True)

TWITTER_USER = ""
TWITTER_PASS = ""

AUTH_TOKEN = None
SEARCH_QUERY = search_query
SEARCH_LIMIT = target_post
OUTPUT_PATH = f"media-sosial-twitter-selected-field-data-{scraped_at}.csv"

HEADLESS_FLAG = True # False => MUNCUL GUI, True => Only Terminal

# === 3. Extract Auth Token with Playwright ===

with sync_playwright() as p:
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    browser = p.chromium.launch(headless=HEADLESS_FLAG, args=['--disable-blink-features=AutomationControlled'])

    if os.path.exists(SESSION_FILE):
        context = browser.new_context(storage_state=SESSION_FILE, user_agent=user_agent)
    else:
        context = browser.new_context(user_agent=user_agent)

    page = context.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # buka twitter
    page.goto(
        "https://x.com",
        wait_until="domcontentloaded",
        # timeout=60000,
    )

    # 👉 CEK apakah sudah login
    if not os.path.exists(SESSION_FILE):
        print("🔐 Silakan login manual...")
        page.goto("https://x.com/login")

        # tunggu sampai login sukses (redirect ke home)
        page.wait_for_url("https://x.com/home", timeout=120000)

        time.sleep(random.uniform(2, 4))

        # simpan session
        context.storage_state(path=SESSION_FILE)
        print("💾 Session disimpan!")

    else:
        print("🚀 Sudah login, langsung lanjut...")

    # delay natural
    time.sleep(random.uniform(2, 4))

    # 👉 AMBIL AUTH TOKEN
    cookies = context.cookies("https://x.com")
    auth_token = next((c for c in cookies if c["name"] == "auth_token"), None)

    if auth_token:
        AUTH_TOKEN = auth_token["value"]
    else:
        print("\n❌ auth_token tidak ditemukan")

    browser.close()

# === 4. Jalankan tweet-harvest dari python file ===

cmd = [
    "npx.cmd",
    "tweet-harvest",
    "-s", SEARCH_QUERY,
    "-t", AUTH_TOKEN,
    "-l", str(SEARCH_LIMIT),
    "-e", "csv",
    "-o", OUTPUT_PATH
]
subprocess.run(cmd)

# === 5. Convert csv ke json ===

final_data = {
    "metadata": {
        "platform": "twitter",
        "scraped_at": scraped_at,
        "target_tags": keyword,
        "max_post_per_tag": target_post
    },
    "data": []
}
counter = 0

with open(SOURCE_PATH, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        counter += 1
        
        url = row.get("image_url")

        unique_id = f"{scraped_at}_{counter}"
        ext = os.path.splitext(urlparse(url).path)[1].lstrip(".")
        output = DOWNLOAD_DIR / f"{unique_id}.{ext}"

        if url == "":
            content_type = "text"
        else:
            content_type = "image"

            response = requests.get(url)
            if response.status_code == 200:
                with open(output, "wb") as f:
                    f.write(response.content)
            else:
                print("Gagal download:", response.status_code)

        if content_type == "text":
            file_path = None
        else:
            file_path = f"downloads/{unique_id}.{ext}"
        
        temporary_clean_data = {
            "unique_id": unique_id,
            "url": row.get("tweet_url"),
            "type": content_type,
            "caption": row.get("full_text"),
            "duration": None,
            "file_path": file_path, 
            "published_at": row.get('created_at'),
            "creator_username": row.get('username'),
            "engagement": {
                "like_count": row.get("favorite_count"),
                "comment_count": row.get("reply_count"),
                "share_count": None,
                "view_count": None,
                "saved_count": None,
                "repost_count": f"{row.get('quote_count')}_{row.get('retweet_count')}"
            }
        }

        final_data["data"].append(temporary_clean_data)

with open(DEST_PATH, mode="w", encoding="utf-8") as file:
    json.dump(final_data, file, indent=4)