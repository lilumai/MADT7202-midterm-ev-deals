"""
MADT 7202 Mid-Term - Step 18: split-sample replication (corroboration inside the one source).
Batch 1 and batch 2 used different generic queries and share no video, so each is an independent sample.
Do both batches show the same two headline results?  (fuel-crossing links rare; Geely-MG overlap thin)
Reads data/raw/yt_videos.csv + data/processed/comment_models_v2.csv.  Prints only.  Run: python3 batch_replication.py
"""
import csv, itertools
from collections import Counter, defaultdict
import networkx as nx

B1 = {"เทียบรถยนต์", "รีวิวรถยนต์", "ลังเลระหว่าง รถ", "เลือกรถคันแรก"}
batch = {r["video_id"]: (1 if r["query"] in B1 else 2)
         for r in csv.DictReader(open("data/raw/yt_videos.csv", encoding="utf-8"))}
EV = {"EX2", "UT", "Atto 1", "Atto 2", "Dolphin", "MG Urban", "Jaecoo 5", "MG4", "Nevo Q05", "ORA 5 EV",
      "Atto 3", "EX5", "Model 3", "MG S5"}
GEELY, MG = {"EX2", "EX5"}, {"MG4", "MG Urban", "MG S5"}

data = {1: [], 2: []}
for r in csv.DictReader(open("data/processed/comment_models_v2.csv", encoding="utf-8")):
    data[batch.get(r["video_id"], 2)].append((r["video_id"], sorted(set(r["models"].split("|")))))

print("=== BATCH REPLICATION (paste this back) ===")
for b in (1, 2):
    rows = data[b]
    pc, pv = Counter(), defaultdict(set)
    for v, ms in rows:
        for a, c in itertools.combinations(ms, 2):
            pc[(a, c)] += 1; pv[(a, c)].add(v)
    vids = sum(1 for x in batch.values() if x == b)
    print(f"\nBATCH {b}: videos {vids} | comments naming >=2 models {sum(1 for _, ms in rows if len(ms) >= 2)}")
    for k in (1, 2, 3):
        G = nx.Graph([p for p in pc if len(pv[p]) >= k])
        cf = sum(1 for a, c in G.edges if (a in EV) != (c in EV))
        E = G.number_of_edges()
        share = f"{cf / E:.2f}" if E else "-"
        print(f"  k>={k}: links {E} | fuel-crossing {cf} (share {share}) | pieces {nx.number_connected_components(G) if E else 0}")
    gm = sum(c for (a, d), c in pc.items() if (a in GEELY and d in MG) or (a in MG and d in GEELY))
    exut = pc.get(("EX2", "UT"), 0)
    print(f"  Geely x MG comments: {gm} | EX2-UT comments: {exut}")
    print("  top 5 pairs (comments/videos):",
          "; ".join(f"{a}+{c} {n}/{len(pv[(a, c)])}" for (a, c), n in pc.most_common(5)))
