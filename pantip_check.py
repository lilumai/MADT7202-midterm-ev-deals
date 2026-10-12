"""
MADT 7202 Mid-Term - Step 19: second source = Pantip thread TITLES collected BY HAND (normal browsing, no bots).
Search phrases (generic): "ลังเลระหว่าง", "เลือกระหว่าง"; room รัชดา; window 1 Jan - 11 Oct 2026.
Reads  data/raw/pantip_manual.csv  (topic_id,date,model_a,model_b,new_or_used,keyword; header optional; lines with # ignored)
Also counts MG5 / MG ZS / MG HS in the YouTube comments (these were missing from the YouTube alias table).
Prints only.   Run:  python3 pantip_check.py
"""
import csv, os, re, json
from collections import Counter

COLS = ["topic_id", "date", "model_a", "model_b", "new_or_used", "keyword"]
lines = [l for l in open("data/raw/pantip_manual.csv", encoding="utf-8") if l.strip() and not l.startswith("#")]
if lines and lines[0].lower().startswith("topic_id"): lines = lines[1:]
rows = [dict(zip(COLS, [x.strip() for x in r])) for r in csv.reader(lines)]

BASE = {"City e:HEV": "City", "Toyota Ativ": "Yaris Ativ"}                     # variant -> model
EV = {"MG Urban", "MG4", "MG S5", "EX2", "EX5", "UT", "Atto 1", "Atto 2", "Atto 3", "Dolphin", "Nevo Q05",
      "Jaecoo 5", "ORA 5 EV", "Model 3"}                                       # BEV; everything else ICE/HEV/PHEV
GEELY, MG = {"EX2", "EX5"}, {"MG Urban", "MG4", "MG S5", "MG5", "MG ZS", "MG HS"}
base = lambda m: BASE.get(m, m)

seen, uniq = set(), []
for r in rows:
    if r["topic_id"] not in seen: seen.add(r["topic_id"]); uniq.append(r)
inwin = [r for r in uniq if "2026-01-01" <= r["date"] <= "2026-10-11"]
pairs = [(base(r["model_a"]), base(r["model_b"]), r["new_or_used"]) for r in inwin]

print("=== PANTIP CHECK (paste this back) ===")
print(f"rows {len(rows)} | unique threads {len(uniq)} | in window {len(inwin)} | dates {min(r['date'] for r in inwin)} .. {max(r['date'] for r in inwin)}")
print("by keyword:", dict(Counter(r["keyword"] for r in inwin)), "| new/used:", dict(Counter(p[2] for p in pairs)))
print("model mentions:", dict(Counter(m for a, b, _ in pairs for m in (a, b)).most_common()))
cf = [(a, b) for a, b, _ in pairs if (a in EV) != (b in EV)]
print(f"fuel-crossing threads: {len(cf)} of {len(pairs)} -> {cf}")
gm = [(a, b) for a, b, _ in pairs if (a in GEELY and b in MG) or (a in MG and b in GEELY)]
print(f"Geely x MG threads: {len(gm)} | threads naming any Geely model: {sum(1 for a,b,_ in pairs if a in GEELY or b in GEELY)}")
print("MG threads and partners:", [(a, b) for a, b, _ in pairs if a in MG or b in MG])
print("Yaris Ativ - City threads:", sum(1 for a, b, _ in pairs if {a, b} == {"Yaris Ativ", "City"}))

if os.path.exists("data/raw/yt_comments.jsonl"):                              # coverage gap check on YouTube
    rx = {m: re.compile(p) for m, p in {"MG5": r"(?<![a-z0-9])mg\s?5(?![a-z0-9])",
                                         "MG ZS": r"(?<![a-z0-9])(mg\s?)?zs(?![a-z0-9])",
                                         "MG HS": r"(?<![a-z0-9])(mg\s?)?hs(?![a-z0-9])"}.items()}
    c = Counter()
    for l in open("data/raw/yt_comments.jsonl", encoding="utf-8"):
        t = json.loads(l)["text"].lower()
        for m, r_ in rx.items():
            if r_.search(t): c[m] += 1
    print("YouTube comments naming models missing from the alias table:", dict(c))
