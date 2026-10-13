"""
Overlap check: how many comments name a Geely model together with an Aion model, versus a Geely model together with an MG model.
Reads data/processed/comment_models_v4.csv. Prints only.   Run from the repo folder:  python3 overlap_geely_aion_mg.py
"""
import csv, itertools
from collections import Counter, defaultdict
G, A, M = {"EX2", "EX5"}, {"UT", "Aion V", "Aion Y"}, {"MG4", "MG Urban", "MG S5"}
c, v = Counter(), defaultdict(set)
for r in csv.DictReader(open("data/processed/comment_models_v4.csv", encoding="utf-8")):
    ms = sorted(set(r["models"].split("|")))
    for a, b in itertools.combinations(ms, 2):
        c[(a, b)] += 1; v[(a, b)].add(r["video_id"])
def show(name, X, Y):
    rows = [(p, c[p], len(v[p])) for p in c if (p[0] in X and p[1] in Y) or (p[0] in Y and p[1] in X)]
    print(f"{name}: {sum(n for _, n, _ in rows)} comments in total")
    for p, n, k in sorted(rows, key=lambda x: -x[1]):
        print(f"   {p[0]} + {p[1]}: {n} comments / {k} videos")
show("Geely x Aion", G, A)
show("Geely x MG  ", G, M)
show("Aion  x MG  ", A, M)
