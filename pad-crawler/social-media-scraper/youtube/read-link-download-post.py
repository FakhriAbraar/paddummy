# STATUS: SUDAH FUNGSIONAL

import json
import yt_dlp
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Konfigurasi
BASE_DIR = Path(__file__).resolve().parent
# D:\Informatics-Semester-6\Capstone Project\pad2-model\pad-crawler\social-media-scraper\tiktok
LINK_PATH = BASE_DIR / "data" / "hasil_youtube.json"
RESULT_PATH = BASE_DIR / "data" / "final.json"
DOWNLOAD_FLAG = True
MAX_URL = 2

# LOAD LINK-LINK HASIL SCRAPING
raw_data = json.load(open(LINK_PATH, "r", encoding="utf-8"))
target_tags = raw_data["metadata"]["target_tags"]
scraped_at = raw_data["metadata"]["scraped_at"]

ydl_opts = {
    'outtmpl': 'downloads/%(id)s.%(ext)s',  # folder & nama file
    'format': 'bestvideo+bestaudio/best',  # kualitas terbaik
    'quiet': True,
    'no_warnings': True,   # Nonaktifkan warning
    'merge_output_format': 'mp4',  # ⬅️ paksa jadi mp4
    # 'logger': None,

}

data = []

# DOWNLOAD DAN EXTRACT INFO PER URL
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    for tag in target_tags:
        links = raw_data["data"][tag]
        for i, url in enumerate(links):
            if i >= MAX_URL:
                break
            
            info = ydl.extract_info(url, download=DOWNLOAD_FLAG)

            # [DEBUGGING]
            # with open("yt-dlp-info-full.json", "w", encoding="utf-8") as f:
            #     json.dump(info, f, indent=4, ensure_ascii=False)

            upload_date = info.get("upload_date")
            if upload_date:
                upload_date = datetime.strptime(upload_date, "%Y%m%d").strftime("%Y-%m-%d")

            temp_data = {
                "scraped_at": scraped_at,
                "platform": "youtube",
                "filepath": ydl.prepare_filename(info),
                "title": info.get("title"),
                "description": info.get("description"),
                "upload_date": upload_date,
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "comment_count": info.get("comment_count"),
                "duration": info.get("duration"),
                "video_url": info.get("webpage_url"),
            }

            data.append(temp_data)

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