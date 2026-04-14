# STATUS: SUDAH FUNGSIONAL

import json
import yt_dlp
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Konfigurasi
BASE_DIR = Path(__file__).resolve().parent
# D:\Informatics-Semester-6\Capstone Project\pad2-model\pad-crawler\social-media-scraper\tiktok
LINK_PATH = BASE_DIR / "data" / "hasil_tiktok.json"
RESULT_PATH = BASE_DIR / "data" / "final.json"
MAX_URL = 200

# LOAD LINK-LINK HASIL SCRAPING
raw_data = json.load(open(LINK_PATH, "r", encoding="utf-8"))
target_tags = raw_data["metadata"]["target_tags"]
scraped_at = raw_data["metadata"]["scraped_at"]

ydl_opts = {
    'outtmpl': 'downloads/%(id)s.%(ext)s',  # folder & nama file
    'format': 'best',  # kualitas terbaik
    'quiet': True,         # Nonaktifkan output biasa
    'no_warnings': True,   # Nonaktifkan warning
    # 'logger': None,
}

data = []

# DOWNLOAD DAN EXTRACT INFO PER URL
for tag in target_tags:
    links = raw_data["data"][tag]
    for i, url in enumerate(links):
        if i >= MAX_URL:
            break
        data_temp = {}
        def hook(d):
            if d['status'] == 'finished':
                info = d["info_dict"]
                data_temp.update({
                    "scraped_at": scraped_at,
                    "platform": "tiktok",
                    "file_path": d['filename'],
                    "post_link": info["original_url"],
                    "duration": info["duration"],
                    "title": info["title"],
                    "description": info["description"],
                    "uploaded_at": datetime.fromtimestamp(
                        info["timestamp"],
                        tz=timezone.utc
                    ).astimezone(
                        timezone(timedelta(hours=7))
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                    "view_count": info["view_count"],
                    "like_count": info["like_count"],
                    "repost_count": info["repost_count"],
                    "comment_count": info["comment_count"],
                    "save_count": info["save_count"],
                })

        ydl_opts_with_hook = ydl_opts.copy()
        ydl_opts_with_hook['progress_hooks'] = [hook]

        with yt_dlp.YoutubeDL(ydl_opts_with_hook) as ydl:
            ydl.download([url])

        data.append(data_temp)
        
# Rename final.json to final_N.json (N = last number + 1)
data_dir = RESULT_PATH.parent
base_name = "final"
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

if RESULT_PATH.exists():
    RESULT_PATH.rename(new_path)

with open(RESULT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)