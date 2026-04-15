# STATUS: SUDAH FUNGSIONAL, DARI AWAL HINGGA AKHIR, BELUM BISA HEADLESS, LOGIN PERLU MANUAL

from playwright.sync_api import sync_playwright
from pathlib import Path
import os
import csv
import time
import json
import random
import subprocess

# Konfigurasi
BASE_DIR = Path(__file__).resolve().parent
SESSION_FILE = BASE_DIR / "twitter_session.json"

SOURCE_PATH = BASE_DIR / "tweets-data" / "hasil.csv"
DEST_PATH = BASE_DIR / "tweets-data" / "hasil.json"

TWITTER_USER = ""
TWITTER_PASS = "4lg0f4mb1s41tf"

SEARCH_QUERY = "komdigi"
AUTH_TOKEN = None
SEARCH_LIMIT = 100
OUTPUT_PATH = "hasil.csv"
# Konfigurasi

HEADLESS_FLAG = False # False => MUNCUL GUI, True => Only Terminal

with sync_playwright() as p:
    
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36'
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])

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

data = []

with open(SOURCE_PATH, mode="r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    
    for row in reader:
        data.append(row)

with open(DEST_PATH, mode="w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)