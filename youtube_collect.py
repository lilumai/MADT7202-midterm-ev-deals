"""
MADT 7202 Mid-Term — YouTube comment collector (corroborating source)
- Official YouTube Data API v3 only (no page scraping)
- Generic queries only: NO car-model names as search terms (avoids seed bias)
- Window: 2026-01-01 to 2026-10-11 (videos AND comments)
- Does NOT store author names or channel names (PDPA)
Run:  export YOUTUBE_API_KEY="..."  then  python youtube_collect.py
"""
import os, sys, json, csv, time
import requests

API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    sys.exit("Set the YOUTUBE_API_KEY environment variable first (never hard-code it).")

QUERIES = ["เทียบรถยนต์", "รีวิวรถยนต์", "ลังเลระหว่าง รถ", "เลือกรถคันแรก"]
AFTER  = "2026-01-01T00:00:00Z"
BEFORE = "2026-10-12T00:00:00Z"      # exclusive -> includes 11 Oct 2026
MAX_SEARCH_PAGES  = 2                 # 50 videos/page, 100 units/call
MAX_COMMENT_PAGES = 5                 # 100 comments/page, 1 unit/call
OUT = "data/raw"
os.makedirs(OUT, exist_ok=True)

units = 0
def get(endpoint, params, cost):
    global units
    params = {**params, "key": KEY}
    for _ in range(3):
        r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
        units += cost
        if r.status_code == 200:
            return r.json()
        if r.status_code == 403 and ("commentsDisabled" in r.text or "forbidden" in r.text):
            return None                      # comments off on this video
        if r.status_code == 403 and "quotaExceeded" in r.text:
            sys.exit("Quota exceeded — rerun tomorrow (resets midnight Pacific).")
        print("HTTP", r.status_code, r.text[:200])
        time.sleep(2)
    return None

# 1) find videos with generic queries
videos = {}
for q in QUERIES:
    token = None
    for _ in range(MAX_SEARCH_PAGES):
        p = dict(part="snippet", q=q, type="video", maxResults=50,
                 publishedAfter=AFTER, publishedBefore=BEFORE,
                 regionCode="TH", relevanceLanguage="th", order="relevance")
        if token:
            p["pageToken"] = token
        d = get("search", p, cost=100)
        if not d:
            break
        for it in d.get("items", []):
            vid = it["id"]["videoId"]
            videos.setdefault(vid, {"video_id": vid,
                                    "title": it["snippet"]["title"],
                                    "published_at": it["snippet"]["publishedAt"],
                                    "query": q})
        token = d.get("nextPageToken")
        if not token:
            break
        time.sleep(0.5)

# 2) pull top-level comments in the window
rows = []
for vid in videos:
    token = None
    for _ in range(MAX_COMMENT_PAGES):
        p = dict(part="snippet", videoId=vid, maxResults=100,
                 textFormat="plainText", order="time")
        if token:
            p["pageToken"] = token
        d = get("commentThreads", p, cost=1)
        if not d:
            break
        for it in d.get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            if AFTER <= s["publishedAt"] < BEFORE:
                rows.append({"video_id": vid,
                             "comment_id": it["id"],
                             "published_at": s["publishedAt"],
                             "text": s["textDisplay"]})   # raw text kept LOCAL only
        token = d.get("nextPageToken")
        if not token:
            break
        time.sleep(0.3)

# 3) save
with open(f"{OUT}/yt_videos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["video_id", "title", "published_at", "query"])
    w.writeheader(); w.writerows(videos.values())
with open(f"{OUT}/yt_comments.jsonl", "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print("=== YOUTUBE SUMMARY (paste this back) ===")
print("videos found:", len(videos))
for q in QUERIES:
    print(f"  query '{q}':", sum(1 for v in videos.values() if v["query"] == q))
print("comments in window:", len(rows))
print("videos with >=1 comment:", len({r['video_id'] for r in rows}))
print("approx quota units used:", units)
print("sample titles:")
for v in list(videos.values())[:10]:
    print("  -", v["title"][:80])
