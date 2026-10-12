"""
MADT 7202 Mid-Term - Step 4a: edge audit. Reads the comments behind chosen model pairs so we can check
that an edge is a real "choosing between these two" and not an artifact of how the data was collected.
Prints to screen only.  Run:   python3 inspect_edges.py                                   (default pairs)
   or: python3 inspect_edges.py "Atto 2+Atto 3" "City+Yaris Ativ"   (any pairs, written A+B)
Raw comment text stays on your computer: do NOT quote comments in the report or put them in the repo.
"""
import csv, json, sys, os
from collections import defaultdict

PAIRS = [("Atto 2", "Atto 3"), ("Atto 3", "Dolphin"), ("City", "Yaris Ativ")]
if len(sys.argv) >= 2:
    PAIRS = [tuple(a.split("+", 1)) for a in sys.argv[1:] if "+" in a]
SRC = "data/processed/comment_models_v2.csv" if os.path.exists("data/processed/comment_models_v2.csv") \
      else "data/processed/comment_models.csv"

titles = {r["video_id"]: r["title"] for r in csv.DictReader(open("data/raw/yt_videos.csv", encoding="utf-8"))}
hits = defaultdict(list)                       # pair -> [(video_id, comment_id)]
for r in csv.DictReader(open(SRC, encoding="utf-8")):
    ms = set(r["models"].split("|"))
    for p in PAIRS:
        if p[0] in ms and p[1] in ms:
            hits[p].append((r["video_id"], r["comment_id"]))
need = {cid for v in hits.values() for _, cid in v}
text = {}
for line in open("data/raw/yt_comments.jsonl", encoding="utf-8"):
    c = json.loads(line)
    if c["comment_id"] in need:
        text[c["comment_id"]] = c["text"]

for p in PAIRS:
    h = hits[p]
    vids = defaultdict(list)
    for v, cid in h:
        vids[v].append(cid)
    print(f"\n=== {p[0]} + {p[1]}: {len(h)} comments / {len(vids)} videos ===")
    shown = 0
    for v, cids in sorted(vids.items(), key=lambda x: -len(x[1])):
        print(f"- video: {titles.get(v, '?')[:80]}  ({len(cids)} comments)")
        for cid in cids[:2]:
            if shown >= 8: break
            print("    >", " ".join(text[cid].split())[:200]); shown += 1
