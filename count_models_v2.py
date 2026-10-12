"""
MADT 7202 Mid-Term - Step 3b, v2 (REVISED AFTER THE EDGE AUDIT - disclose this in the report)
Changes vs count_models.py:
  1) "ORA 5" is split into "ORA 5 EV" / "ORA 5 HEV": comment text first (HEV/hybrid/ไฮบริด vs EV/BEV/ไฟฟ้า),
     then the video title. If still unclear (both or neither) the ORA 5 mention is DROPPED and counted.
  2) each kept comment gets cue=1 if it has a choice word: หรือ / ระหว่าง / ลังเล / เลือก / vs.
Reads  data/raw/yt_videos.csv, data/raw/yt_comments.jsonl
Writes data/processed/comment_models_v2.csv  (ids + model names + cue; NO comment text)
v1 files are not touched, so the earlier results stay reproducible.   Run:  python3 count_models_v2.py
"""
import csv, json, re, os, itertools
from collections import Counter, defaultdict

RAW = "data/raw"
vtitle = {r["video_id"]: r["title"].lower()
          for r in csv.DictReader(open(f"{RAW}/yt_videos.csv", encoding="utf-8"))}
comments = [json.loads(l) for l in open(f"{RAW}/yt_comments.jsonl", encoding="utf-8")]

IN_SCOPE = [
 (r"ex\s?2", "EX2"), (r"ex\s?5", "EX5"), (r"ut", "UT"),
 (r"yaris(?!\s?(ativ|cross))", "Yaris"), (r"yaris\s?ativ|ativ", "Yaris Ativ"), (r"yaris\s?cross", "Yaris Cross"),
 (r"city", "City"), (r"ซิตี้", "City"), (r"civic", "Civic"), (r"ซีวิค", "Civic"),
 (r"x-?\s?force", "XForce"), (r"kicks", "Kicks"),
 (r"dolphin", "Dolphin"), (r"mg\s?4", "MG4"), (r"atto\s?1", "Atto 1"), (r"atto\s?2", "Atto 2"), (r"atto\s?3", "Atto 3"),
 (r"ora\s?0?5", "ORA 5"), (r"q05|nevo", "Nevo Q05"), (r"jaecoo\s?5?", "Jaecoo 5"),
 (r"mg\s?s5", "MG S5"), (r"v27", "iCAUR V27"), (r"mg\s?urban|urban", "MG Urban"),
 (r"swift", "Swift"), (r"fronx", "Fronx"), (r"hr-?v", "HR-V"), (r"cr-?v", "CR-V"),
 (r"camry", "Camry"), (r"แคมรี่", "Camry"), (r"altis", "Altis"), (r"อัลติส", "Altis"),
 (r"model\s?3", "Model 3"),
]
OUT_OF_SCOPE = r"hilux|revo|travo|fortuner|ranger|pajero|d-?max|triton|navara"
PENDING = [(r"tank\s?300", "x"), (r"fj", "x"), (r"land\s?cruiser", "x"), (r"serena", "x"), (r"m6", "x")]

def comp(pat):
    guard = pat[0].isascii()
    return re.compile((r"(?<![a-z0-9])" + pat + r"(?![a-z0-9])") if guard else pat)
IN_RX = [(comp(p), m) for p, m in IN_SCOPE]
OUT_RX = comp(OUT_OF_SCOPE)
PEND_RX = [comp(p) for p, _ in PENDING]
XF_RX = comp(r"xf")
HEV_RX = re.compile(r"(?<![a-z0-9])(hev|phev|hybrid)(?![a-z0-9])|ไฮบริด")
EV_RX = re.compile(r"(?<![a-z0-9])(bev|ev)(?![a-z0-9])|ไฟฟ้า")
CUE_RX = re.compile(r"หรือ|ระหว่าง|ลังเล|เลือก|(?<![a-z])vs(?![a-z])")

def ora_variant(text_l, title_l):
    for s in (text_l, title_l):
        h, e = bool(HEV_RX.search(s)), bool(EV_RX.search(s))
        if h and not e: return "ORA 5 HEV"
        if e and not h: return "ORA 5 EV"
    return None

seen, dup, rows = set(), 0, []
for c in comments:
    key = re.sub(r"\s+", " ", c["text"]).strip().lower()
    if key in seen: dup += 1; continue
    seen.add(key); rows.append(c)

res, ora = [], Counter()
for c in rows:
    t = c["text"].lower(); title = vtitle.get(c["video_id"], "")
    models = {m for rx, m in IN_RX if rx.search(t)}
    if XF_RX.search(t) and "xforce" in title:
        models.add("XForce")
    if "ORA 5" in models:
        models.discard("ORA 5")
        v = ora_variant(t, title)
        if v: models.add(v); ora[v] += 1
        else: ora["unresolved(dropped)"] += 1
    res.append((c["video_id"], c["comment_id"], sorted(models), int(bool(CUE_RX.search(t)))))

os.makedirs("data/processed", exist_ok=True)
with open("data/processed/comment_models_v2.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["video_id", "comment_id", "models", "cue"])
    for v, cid, ms, cue in res:
        if ms: w.writerow([v, cid, "|".join(ms), cue])

ge1 = [r for r in res if len(r[2]) >= 1]
ge2 = [r for r in res if len(r[2]) >= 2]
def pair_stats(rs):
    pv = defaultdict(set)
    for v, _, ms, _ in rs:
        for a, b in itertools.combinations(ms, 2): pv[(a, b)].add(v)
    return pv
pv_all, pv_cue = pair_stats(ge2), pair_stats([r for r in ge2 if r[3]])
print("=== MODEL COUNT SUMMARY v2 (paste this back) ===")
print("comments kept (after exact-duplicate removal):", len(rows), "| duplicates removed:", dup)
print("ORA 5 mentions ->", dict(ora))
print("comments with >=1 in-scope model:", len(ge1), "| with cue word:", sum(r[3] for r in ge1))
print("comments with >=2 distinct models:", len(ge2), "| of those with cue word:", sum(r[3] for r in ge2))
for k in (1, 2, 3):
    print(f"pairs under >={k} videos: all comments {sum(1 for p in pv_all if len(pv_all[p])>=k)} | cue-only {sum(1 for p in pv_cue if len(pv_cue[p])>=k)}")
print("models by comments:", dict(Counter(m for _, _, ms, _ in res for m in ms).most_common(12)))
