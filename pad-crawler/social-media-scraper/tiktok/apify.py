# STATUS: SUDAH FUNGSIONAL, TINGGAL MEMPERHATIKAN SALDO APIFY

import os
import json
import yt_dlp
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

# === 1. Parsing Argument ===
parser = argparse.ArgumentParser(
    description="""Contoh penggunaan program:
python apify.py --keyword "komdigi" "bahlil" --target_post 10
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
target_post = args.target_post

# === 2. Setup Constant Variables ===
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
APIFY_API_FREE = os.getenv("APIFY_API_FREE")
APIFY_API_PREMIUM = os.getenv("APIFY_API_PREMIUM")

# === 3. Setup Apify ===
client = ApifyClient(APIFY_API_FREE)

run_input = {
    "searchQueries": keyword, # lebih aman dibanding hashtags (hashtags bisa saja tidak ada)
    "resultsPerPage": target_post,
    "shouldDownloadVideos": False,  # kita download pakai URL langsung ke yt_dlp
}

# === 4. Setup yt_dlp ===
download_dir = Path("downloads")

ydl_opts = {
    "outtmpl": str(download_dir / "%(id)s.%(ext)s"),  # nama file hasil download
    "format": "best",  # kualitas terbaik
}

# === 5. Run Apify actor ===
run = client.actor("GdWCkxBtKWOsKjdch").call(run_input=run_input)

dataset_id = run["defaultDatasetId"]

# === 6. Siapkan folder ===
os.makedirs("output", exist_ok=True)
os.makedirs("downloads", exist_ok=True)

# === 7. Siapkan variabel ===
counter = 0
scraped_at = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

all_data = []
final_data = {
    "metadata": {
        "platform": "tiktok",
        "scraped_at": scraped_at,
        "target_tags": run_input.get("searchQueries"),
        "max_post_per_tag": run_input.get("resultsPerPage")
    },
    "data": []
}

# === 8. Ambil data + download video ===
for index, item in enumerate(client.dataset(dataset_id).iterate_items()):
    counter += 1
    all_data.append(item)
    
    # DEBUG: lihat isi mentah
    # print("\n================ ITEM RAW =================")
    # print(json.dumps(item, indent=2, ensure_ascii=False))
    # print("==========================================\n")

    video_url = item.get("webVideoUrl")

    if "/photo/" in video_url:
        content_type = "image"
    elif "/video/" in video_url:
        content_type = "video"
    else:
        content_type = "text"

    file_path = None  # default: tidak ada file

    if video_url:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(video_url, download=True)

                # ambil path file hasil download
                if info:
                    filename = ydl.prepare_filename(info)
                    file_path = str(Path(filename))

                print(f"Download berhasil {video_url}")

        except Exception as e:
            print(f"Gagal download video {index}: {e}")

    # simpan data SETELAH tahu hasil download
    temporary_clean_data = {
        "unique_id": f"{scraped_at}_{counter}",
        "url": video_url,
        "type": content_type,
        "caption": item.get("text"),
        "duration": item.get('videoMeta', {}).get('duration'),
        "file_path": file_path, 
        "published_at": item.get('createTimeISO'),
        "creator_username": item.get('authorMeta', {}).get('name'),
        "engagement": {
            "like_count": item.get("diggCount"),
            "comment_count": item.get("commentCount"),
            "share_count": item.get("shareCount"),
            "view_count": item.get("playCount"),
            "saved_count": item.get('collectCount'),
            "repost_count": item.get('repostCount')
        }
    }

    final_data["data"].append(temporary_clean_data)

# === 9. Simpan all fields JSON ke lokal ===
with open(f"output/media-sosial-tiktok-all-field-data-{scraped_at}.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

# === 10. Simpan selected fields JSON ke lokal ===
with open(f"output/media-sosial-tiktok-selected-field-data-{scraped_at}.json", "w", encoding="utf-8") as f:
    json.dump(final_data, f, ensure_ascii=False, indent=2)

# === 11. SELESAI ===
print("Selesai! Data JSON & video sudah disimpan.")