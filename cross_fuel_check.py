"""
MADT 7202 Mid-Term - Step 17: robustness of the two headline findings at looser cutoffs.
For k = 1, 2, 3 (min distinct videos per pair): how many links cross fuel (ICE/HEV <-> EV), which ones,
and whether any Geely model can reach any MG model through the graph (and by how many steps).
Reads data/processed/comment_models_v2.csv.  Prints only.   Run:  python3 cross_fuel_check.py
"""
import csv, itertools
from collections import Counter, defaultdict
import networkx as nx

FUEL = {m: "ICE" for m in ["City", "XForce", "HR-V", "Kicks", "Yaris Cross", "Yaris Ativ", "Yaris", "Swift", "Fronx",
                          "Civic", "Camry", "CR-V", "Altis", "iCAUR V27", "ORA 5 HEV"]}
FUEL.update({m: "EV" for m in ["EX2", "UT", "Atto 1", "Atto 2", "Dolphin", "MG Urban", "Jaecoo 5", "MG4", "Nevo Q05",
                              "ORA 5 EV", "Atto 3", "EX5", "Model 3", "MG S5"]})
GEELY, MG = ["EX2", "EX5"], ["MG4", "MG Urban", "MG S5"]

pc, pv = Counter(), defaultdict(set)
for r in csv.DictReader(open("data/processed/comment_models_v2.csv", encoding="utf-8")):
    ms = sorted(set(r["models"].split("|")))
    for a, b in itertools.combinations(ms, 2):
        pc[(a, b)] += 1; pv[(a, b)].add(r["video_id"])

print("=== CROSS-FUEL CHECK (paste this back) ===")
for k in (1, 2, 3):
    G = nx.Graph()
    for p, c in pc.items():
        if len(pv[p]) >= k: G.add_edge(*p, comments=c, videos=len(pv[p]))
    cross = sorted(((a, b, d) for a, b, d in G.edges(data=True) if FUEL[a] != FUEL[b]),
                   key=lambda e: (-e[2]["videos"], -e[2]["comments"]))
    pieces = sum(1 for c in nx.connected_components(G) if len(c) >= 2)
    print(f"\nk>={k}: links {G.number_of_edges()} | pieces {pieces} | fuel-crossing links {len(cross)}")
    for a, b, d in cross[:8]:
        print(f"  {a} + {b}: {d['comments']} comments / {d['videos']} videos")
    best = None
    for g in GEELY:
        for m in MG:
            if g in G and m in G and nx.has_path(G, g, m):
                L = nx.shortest_path_length(G, g, m)
                if best is None or L < best[0]: best = (L, nx.shortest_path(G, g, m))
    print("  Geely->MG path:", "none" if best is None else f"{best[0]} steps: {' - '.join(best[1])}")
