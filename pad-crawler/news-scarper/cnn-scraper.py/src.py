import os
import json
import time
import argparse
from datetime import datetime
from playwright.sync_api import sync_playwright

# === 1. Parsing Argument ===
parser = argparse.ArgumentParser(
    description="""Contoh penggunaan program:
python cnn-scraper.py --keyword "komdigi" "bahlil" --target_news 10
""",
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument(
    "--keyword",
    nargs="+",  
    required=True,
    help="Daftar keyword (pisahkan dengan spasi)"
)

parser.add_argument(
    "--target_news",
    type=int,
    required=True,
    help="Jumlah target berita per keyword"
)

args = parser.parse_args()

TARGET_KEYWORDS = args.keyword
TARGET_NEWS = args.target_news
HEADLESS_FLAG = False # Ubah ke True jika sudah lancar dan ingin jalan di background

def scrape_cnn():
    scraped_at = datetime.now().isoformat()
    all_items = []
    counter = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=HEADLESS_FLAG,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Menyamarkan identitas bot
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = context.new_page()

        for keyword in TARGET_KEYWORDS:
            print(f"\n--- Mencari berita untuk keyword: '{keyword}' ---")
            
            search_url = f"https://www.cnnindonesia.com/search/?query={keyword}"
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            try:
                page.wait_for_selector("article", timeout=15000)
                time.sleep(2) 
            except Exception:
                print(f"Tidak ada hasil pencarian untuk '{keyword}' atau halaman lambat dimuat.")
                continue

            # 1. Kumpulkan link artikel
            articles = page.query_selector_all("article a")
            links_found = set()
            
            for el in articles:
                href = el.get_attribute("href")
                
                if not href:
                    continue
                
                # Menangani URL Relatif
                if href.startswith("/"):
                    href = f"https://www.cnnindonesia.com{href}"
                
                # Filter khusus link berita CNN
                if ("cnnindonesia.com" in href) and ("/tag/" not in href) and ("/search/" not in href):
                    links_found.add(href)
                
                if len(links_found) >= TARGET_NEWS:
                    break
            
            print(f"Ditemukan {len(links_found)} link artikel. Memulai ekstraksi konten...")

            # 2. Masuk ke setiap link untuk ekstrak data
            for link in list(links_found)[:TARGET_NEWS]:
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(1.5) 
                    
                    counter += 1
                    
                    # --- EKSTRAK JUDUL DENGAN FALLBACK URL ---
                    # Coba cari tag h1 secara umum (bukan hanya h1.title)
                    title_el = page.query_selector("h1")
                    if title_el and title_el.inner_text().strip():
                        title = title_el.inner_text().strip()
                    else:
                        # Fallback: Ambil dari URL bagian paling belakang
                        slug = link.rstrip('/').split('/')[-1]
                        title = slug.replace('-', ' ').title()
                    
                    # --- EKSTRAK TANGGAL ---
                    # Coba beberapa kemungkinan class tanggal di CNN
                    date_el = page.query_selector(".detail-date, .date, .text-gray-500")
                    news_date = date_el.inner_text().strip() if date_el else ""
                    
                    # --- EKSTRAK KONTEN UTAMA ---
                    content_locator = page.locator("div.detail-text")
                    
                    if content_locator.count() == 0:
                        print(f"  [-] Struktur halaman berbeda/bukan artikel teks: {title[:30]}...")
                        continue

                    # Bersihkan dari iklan/script
                    content_locator.evaluate("""node => {
                        const selectorsToRemove = ['script', 'style', '.parallax', '.ads', '.video', 'table', '.link-sisip'];
                        selectorsToRemove.forEach(selector => {
                            const elements = node.querySelectorAll(selector);
                            elements.forEach(el => el.remove());
                        });
                    }""")
                    
                    raw_content = content_locator.inner_text().strip()
                    clean_content = " ".join(raw_content.split())
                    
                    # --- FORMAT JSON DISAMAKAN DENGAN DETIK ---
                    article_data = {
                        "scraped_at": scraped_at,
                        "publisher": "CNN Indonesia",
                        "unique_id": f"{scraped_at}_{counter}",
                        "title": title,
                        "news_date": news_date,
                        "content": clean_content,
                        "related_link": link
                    }
                    
                    all_items.append(article_data)
                    print(f"  [+] Berhasil: {title[:50]}...")
                    
                except Exception as e:
                    print(f"  [-] Gagal mengekstrak {link}: {e}")
                    
        browser.close()
        
    return all_items, scraped_at

if __name__ == "__main__":
    
    print("Memulai proses scraping portal berita (CNN)...")
    data_hasil, timestamp = scrape_cnn()
    
    # Path penyimpanan
    base_path = "output"
    os.makedirs(base_path, exist_ok=True)
    
    safe_timestamp = timestamp.replace(":", "-").split(".")[0]
    output_path = f"{base_path}/news-portal-cnn-{safe_timestamp}.json"
    
    with open(output_path, "w", encoding="utf-8") as f:
        # Menyimpan langsung array of objects layaknya detik-scraper
        json.dump(data_hasil, f, ensure_ascii=False, indent=4)
        
    print("\n" + "="*40)
    print("SCRAPING BERITA SELESAI")
    print(f"Total {len(data_hasil)} berita disimpan di: {output_path}")
    print("="*40)