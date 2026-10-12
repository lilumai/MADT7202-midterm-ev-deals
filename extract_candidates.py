"""
MADT 7202 Mid-Term - Step 3a: window check + candidate car-model names
Reads data/raw/yt_videos.csv and data/raw/yt_comments.jsonl (made by youtube_collect.py).
Prints to screen only; writes nothing.   Run:  python3 extract_candidates.py
Limits: finds only English-spelled names (e.g. "Atto 3", "City"). Thai nicknames
(ซิตี้, ยาริส) are NOT captured here and will be added later in an alias table.
"""
import csv, json, re
from collections import Counter

RAW = "data/raw"
vids = list(csv.DictReader(open(f"{RAW}/yt_videos.csv", encoding="utf-8")))
coms = [json.loads(l) for l in open(f"{RAW}/yt_comments.jsonl", encoding="utf-8")]

# ---- 1) window check ----
print("=== WINDOW CHECK ===")
vd = sorted(v["published_at"] for v in vids)
cd = sorted(c["published_at"] for c in coms)
print("videos:", len(vids), "| published_at min/max:", vd[0][:10], vd[-1][:10])
print("comments:", len(coms), "| published_at min/max:", cd[0][:10], cd[-1][:10])
per_vid = Counter(c["video_id"] for c in coms)
print("videos with comments:", len(per_vid))
print("max comments in one video:", max(per_vid.values()))
print("videos with >=500 comments (cap hit, likely truncated):",
      sum(1 for n in per_vid.values() if n >= 500))

# ---- 2) candidate model names (document frequency = comments containing it) ----
STOP = set("""ev hev phev bev suv vs the and for not you ok km kw kwh kg ac dc
lol www http https com youtube facebook line id ps ice ptt cvt dct mpv cbu ckd
v2 v3 thai thailand bangkok mg1 am pm""".split())
pat = re.compile(r"[A-Za-z][A-Za-z0-9\-]+(?:\s\d{1,2}(?!\d))?")
df = Counter()
for c in coms:
    found = set()
    for m in pat.findall(c["text"]):
        name = re.sub(r"\s+", " ", m).strip().lower()
        if name.split()[0] in STOP or len(name) < 2:
            continue
        found.add(name)
    df.update(found)

print("\n=== TOP 120 NAME CANDIDATES (name - number of comments) ===")
for i, (name, n) in enumerate(df.most_common(120), 1):
    print(f"{i:>3}. {name} - {n}")
