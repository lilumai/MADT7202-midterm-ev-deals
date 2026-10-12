"""
MADT 7202 Mid-Term - Step 5: "The picture" for the report (one readable graph, not a hairball).
Reads  data/processed/graph_edges_baseline_v2.csv  (written by build_graph_v2.py: baseline S0, k3*)
       data/processed/comment_models_v2.csv        (node size = number of comments naming the model)
Writes figure_baseline.png (300 dpi, drawn at print size)
Run:   python3 make_figure.py
"""
import csv, itertools, math
from collections import Counter
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

E = list(csv.DictReader(open("data/processed/graph_edges_baseline_v2.csv", encoding="utf-8")))
cnt = Counter(m for r in csv.DictReader(open("data/processed/comment_models_v2.csv", encoding="utf-8"))
              for m in r["models"].split("|"))
G = nx.Graph(); grp = {}
for r in E:
    G.add_edge(r["model_a"], r["model_b"], videos=int(r["videos"]), comments=int(r["comments"]))
    grp[r["model_a"]], grp[r["model_b"]] = r["group_a"], r["group_b"]

SHORT = {"Yaris Ativ": "Ativ", "Yaris Cross": "Y-Cross", "Nevo Q05": "Q05", "Jaecoo 5": "Jaecoo5",
         "MG Urban": "Urban", "ORA 5 HEV": "ORA5 HEV", "ORA 5 EV": "ORA5 EV"}
lab = lambda n: SHORT.get(n, n)
CENTER = {"S-ICE": (0.25, 0.25), "M-ICE": (0.25, 0.75), "S-EV": (0.75, 0.25), "M-EV": (0.75, 0.75)}
HW, HH = 0.215, 0.175
def box_layout(nodes, seed):
    sub = G.subgraph(nodes)
    comps = sorted((sorted(c) for c in nx.connected_components(sub)), key=lambda c: (-len(c), c))
    tot = sum(len(c) + 1 for c in comps); left = -1.0; p = {}
    for c in comps:
        wdt = 2.0 * (len(c) + 1) / tot; ccx = left + wdt / 2; left += wdt
        if len(c) == 1: lp = {c[0]: (0.0, 0.0)}
        elif len(c) == 2: lp = {c[0]: (0.0, 0.6), c[1]: (0.0, -0.6)}
        else:
            lp = nx.spring_layout(sub.subgraph(c), seed=seed, iterations=300)
            m0 = max(max(abs(x), abs(y)) for x, y in lp.values()) or 1.0
            rx = {n: i for i, n in enumerate(sorted(lp, key=lambda n: lp[n][0]))}
            ry = {n: i for i, n in enumerate(sorted(lp, key=lambda n: lp[n][1]))}
            L = len(lp) - 1
            lp = {n: (0.4 * lp[n][0] / m0 + 0.6 * (2 * rx[n] / L - 1),
                      0.4 * lp[n][1] / m0 + 0.6 * (2 * ry[n] / L - 1)) for n in lp}
        m = max(max(abs(x), abs(y)) for x, y in lp.values()) or 1.0
        for n, (x, y) in lp.items():
            p[n] = (ccx + 0.42 * wdt * x / m, 0.85 * y / m)
    return p
def place_box(g, layout, r, f):
    cx, cy = CENTER[g]; c, s_ = math.cos(math.radians(r)), math.sin(math.radians(r))
    out = {}
    for n, (x, y) in layout.items():
        x = -x if f else x
        out[n] = (cx + HW * (c * x - s_ * y), cy + HH * (s_ * x + c * y))
    return out
def seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)
lw = lambda n: 0.022 * len(lab(n)) + 0.025
def badness(pos):
    bad = 0
    for a_, b_ in G.edges:
        for n in G:
            if n not in (a_, b_) and seg_dist(pos[n], pos[a_], pos[b_]) < 0.05: bad += 1
    for n in G:                                        # two links leaving a node at almost the same angle
        nb = list(G[n])
        for a2, b2 in itertools.combinations(nb, 2):
            ang = lambda t: math.atan2(pos[t][1] - pos[n][1], pos[t][0] - pos[n][0])
            d = abs(ang(a2) - ang(b2)) % (2 * math.pi)
            if min(d, 2 * math.pi - d) < math.radians(15): bad += 1
    for u, v in itertools.combinations(G, 2):
        if abs(pos[u][0] - pos[v][0]) < (lw(u) + lw(v)) / 2 and abs(pos[u][1] - pos[v][1]) < 0.055: bad += 1
    return bad
groups_present = [g for g in CENTER if any(grp[n] == g for n in G)]
cands = {g: [(box_layout(sorted(n for n in G if grp[n] == g), sd), r, f)
             for sd in (1, 2, 3, 5, 7, 11) for r in (0, 90, 180, 270) for f in (False, True)]
         for g in groups_present}
choice = {g: cands[g][0] for g in groups_present}
def assemble(ch):
    pos = {}
    for g, (lay, r, f) in ch.items(): pos.update(place_box(g, lay, r, f))
    return pos
for _ in range(4):
    for g in groups_present:
        choice[g] = min(cands[g], key=lambda c: badness(assemble({**choice, g: c})))
pos = assemble(choice)

cross = [(a, b) for a, b in G.edges if grp[a] != grp[b]]
cross_fuel = [(a, b) for a, b in cross if grp[a].split("-")[1] != grp[b].split("-")[1]]
inside = [(a, b) for a, b in G.edges if grp[a] == grp[b]]

fig, ax = plt.subplots(figsize=(2.65, 2.5), dpi=300)
ax.axvline(0.5, color="#999", lw=0.6, ls="--"); ax.axhline(0.5, color="#999", lw=0.6, ls="--")
BOX = {"Small · ICE/HEV": (0.01, 0.005), "Mid · ICE/HEV": (0.01, 0.955),
       "Small · EV": (0.51, 0.005), "Mid · EV": (0.51, 0.955)}
for txt, (x, y) in BOX.items():
    ax.text(x, y, txt, fontsize=5.5, color="#555", va="bottom")
w = lambda e: 0.3 + 0.22 * G.edges[e]["videos"]
nx.draw_networkx_edges(G, pos, edgelist=inside, width=[w(e) for e in inside], edge_color="#9aa0a6", ax=ax)
nx.draw_networkx_edges(G, pos, edgelist=cross, width=[w(e) for e in cross], edge_color="#e8710a", ax=ax)
col = ["#4C72B0" if grp[n].endswith("ICE") else "#2E8B57" for n in G]
nx.draw_networkx_nodes(G, pos, node_size=[8 + 0.3 * cnt[n] for n in G], node_color=col, alpha=0.9, ax=ax)
placed = {q: (x + lw(q) / 2, y) for q, (x, y) in BOX.items()}
def clash(n, xy):
    c = 0
    for m, (x2, y2) in placed.items():
        if abs(xy[0] - x2) < (lw(n) + lw(m)) / 2 and abs(xy[1] - y2) < 0.05: c += 1
    return c
for n in sorted(G, key=lambda n: (-G.degree(n), n)):
    x, y = pos[n]
    opts = [(x, y + 0.025), (x, y - 0.075), (x + lw(n) / 2 + 0.025, y - 0.025), (x - lw(n) / 2 - 0.025, y - 0.025)]
    placed[n] = min(opts, key=lambda xy: (clash(n, xy), opts.index(xy)))
for n, (x, y) in placed.items():
    if n not in G: continue
    ax.text(x, y, lab(n), fontsize=6, ha="center", va="bottom", clip_on=False)
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
note = (f"{G.number_of_nodes()} models, {G.number_of_edges()} links (pair in >=3 videos). "
        f"Across groups: {len(cross)}; across fuel: {len(cross_fuel)}.")
fig.tight_layout(); fig.savefig("figure_baseline.png", dpi=300, bbox_inches="tight")
print("=== FIGURE SUMMARY (paste this back) ===")
print(note)
print("layout overlap score (0 = no line through a node, no label clash):", badness(pos))
print("cross-group links:", [f"{a}+{b}" for a, b in cross])
print("saved: figure_baseline.png")
