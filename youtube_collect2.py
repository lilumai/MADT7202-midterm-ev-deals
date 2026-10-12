"""
MADT 7202 Mid-Term - YouTube batch 2 (adds data; does NOT overwrite batch 1)
- Official YouTube Data API v3 only. Generic category queries, NO car-model names as search terms.
- Same window as batch 1: 2026-01-01 .. 2026-10-11. Skips videos/comments already collected.
- Appends video-by-video, so if it stops midway you can simply run it again.
- Does NOT store author or channel names (PDPA). Raw text stays local in data/raw/.
Run:  export YOUTUBE_API_KEY="..."   then   python3 youtube_collect2.py
"""
import os, sys, json, csv, time, shutil
import requests

API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    sys.exit("Set YOUTUBE_API_KEY first (never hard-code it).")

QUERIES = ["เทียบรถไฟฟ้า 2026", "เทียบรถไฮบริด", "เลือกรถเก๋งหรือ SUV",
           "ลังเลซื้อรถใหม่", "รถเล็กคันแรก ไฟฟ้าหรือน้ำมัน", "เปรียบเทียบรถ B-SUV"]
AFTER, BEFORE = "2026-01-01T00:00:00Z", "2026-10-12T00:00:00Z"
MAX_SEARCH_PAGES, MAX_COMMENT_PAGES = 2, 5
RAW = "data/raw"
VID_F, COM_F = f"{RAW}/yt_videos.csv", f"{RAW}/yt_comments.jsonl"
if not (os.path.exists(VID_F) and os.path.exists(COM_F)):
    sys.exit("Batch 1 files not found. Run this inside the madt7202 folder after youtube_collect.py.")

# safety copy of batch 1 (once)
bk = f"{RAW}/backup_batch1"
if not os.path.exists(bk):
    os.makedirs(bk); shutil.copy(VID_F, bk); shutil.copy(COM_F, bk)

known_vids = {r["video_id"] for r in csv.DictReader(open(VID_F, encoding="utf-8"))}
known_coms = {json.loads(l)["comment_id"] for l in open(COM_F, encoding="utf-8")}
n_vid_before, n_com_before = len(known_vids), len(known_coms)

units = 0
def get(endpoint, params, cost):
    global units
    params = {**params, "key": KEY}
    for _ in range(3):
        r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
        units += cost
        if r.status_code == 200:
            return r.json()
        if r.status_code == 403 and "quotaExceeded" in r.text:
            sys.exit("Quota exceeded - rerun tomorrow (resets midnight Pacific).")
        if r.status_code == 403 and ("commentsDisabled" in r.text or "forbidden" in r.text):
            return None
        if r.status_code == 400 and "API key" in r.text:
            sys.exit("API key problem: " + r.text[:200])
        print("HTTP", r.status_code, r.text[:150]); time.sleep(2)
    return None

# 1) find NEW videos
new_vids = {}
for q in QUERIES:
    token = None
    for _ in range(MAX_SEARCH_PAGES):
        p = dict(part="snippet", q=q, type="video", maxResults=50,
                 publishedAfter=AFTER, publishedBefore=BEFORE,
                 regionCode="TH", relevanceLanguage="th", order="relevance")
        if token: p["pageToken"] = token
        d = get("search", p, 100)
        if not d: break
        for it in d.get("items", []):
            vid = it["id"]["videoId"]
            if vid in known_vids or vid in new_vids: continue
            new_vids[vid] = {"video_id": vid, "title": it["snippet"]["title"],
                             "published_at": it["snippet"]["publishedAt"], "query": q}
        token = d.get("nextPageToken")
        if not token: break
        time.sleep(0.5)

# 2) comments, appended video by video
new_com = 0
vf = open(VID_F, "a", newline="", encoding="utf-8")
cf = open(COM_F, "a", encoding="utf-8")
vw = csv.DictWriter(vf, fieldnames=["video_id", "title", "published_at", "query"])
for vid, v in new_vids.items():
    rows, token = [], None
    for _ in range(MAX_COMMENT_PAGES):
        p = dict(part="snippet", videoId=vid, maxResults=100, textFormat="plainText", order="time")
        if token: p["pageToken"] = token
        d = get("commentThreads", p, 1)
        if not d: break
        for it in d.get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            if AFTER <= s["publishedAt"] < BEFORE and it["id"] not in known_coms:
                known_coms.add(it["id"])
                rows.append({"video_id": vid, "comment_id": it["id"],
                             "published_at": s["publishedAt"], "text": s["textDisplay"]})
        token = d.get("nextPageToken")
        if not token: break
        time.sleep(0.3)
    for r in rows: cf.write(json.dumps(r, ensure_ascii=False) + "\n")
    cf.flush(); vw.writerow(v); vf.flush()
    new_com += len(rows)
vf.close(); cf.close()

print("=== YOUTUBE BATCH 2 SUMMARY (paste this back) ===")
print("new videos:", len(new_vids), "| total videos now:", n_vid_before + len(new_vids))
for q in QUERIES:
    print(f"  query '{q}': {sum(1 for v in new_vids.values() if v['query'] == q)} new")
print("new comments:", new_com, "| total comments now:", n_com_before + new_com)
print("approx quota units used (script counter):", units)
print("sample new titles:")
for v in list(new_vids.values())[:8]:
    print("  -", v["title"][:80])
