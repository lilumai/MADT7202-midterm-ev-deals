"""
MADT 7202 Mid-Term - Step 3c, v2 (REVISED AFTER THE EDGE AUDIT - disclose in the report): build the model co-mention graph, run Week 6-8 tests, robustness grid.
Reads  data/processed/comment_models_v2.csv   (made by count_models_v2.py: video_id, comment_id, models, cue)
Revision after audit: ORA 5 is two nodes (EV / HEV); a "cue" construction (comments with a choice word) is added.
The v1 grid (build_graph.py) is kept so the BEFORE result stays reproducible.
Writes data/processed/graph_edges_baseline_v2.csv
Run:   python3 build_graph.py

PRE-REGISTERED (fixed before any result was seen - do not change after looking):
  Node  = one car model (28 labelled models).   Edge = two models named in the SAME comment.
  Primary construction: keep an edge only if seen under >= 3 DIFFERENT videos (raw comment count as weight).
  Group = size (S/M) x fuel (ICE incl. HEV/PHEV/REEV, or EV). Baseline labels below are [UNVERIFIED]
  except Nevo Q05 and ORA 5 (checked against Thai sources).
  Week-8 tests (Ch08): inside share = links inside groups / all links; connector = highest betweenness
  (Ch07, unweighted); pieces = components with 2+ nodes. Tests are run on the biggest piece.
  Gate: inside share >= 0.80 AND still one piece without the connector -> COMMUNITIES (silo):
        drop the "bridge" angle and plan promotions by group.  >= 2 pieces -> BRIDGE.  < 0.80 -> MIXED.
"""
import csv, itertools, math, os
from collections import Counter, defaultdict
import networkx as nx

SRC = "data/processed/comment_models_v2.csv"

# (size, fuel)  size: S = B-segment or smaller, M = C-segment or larger.  fuel: ICE (incl. HEV/PHEV/REEV) or EV
LABELS = {
 # small + ICE/Hybrid
 "City": ("S","ICE"), "XForce": ("S","ICE"), "HR-V": ("S","ICE"), "Kicks": ("S","ICE"),
 "Yaris Cross": ("S","ICE"), "Yaris Ativ": ("S","ICE"), "Yaris": ("S","ICE"), "Swift": ("S","ICE"), "Fronx": ("S","ICE"),
 # mid + ICE/Hybrid
 "Civic": ("M","ICE"), "Camry": ("M","ICE"), "CR-V": ("M","ICE"), "Altis": ("M","ICE"), "iCAUR V27": ("M","ICE"),
 # small + EV
 "EX2": ("S","EV"), "UT": ("S","EV"), "Atto 1": ("S","EV"), "Atto 2": ("S","EV"), "Dolphin": ("S","EV"),
 "MG Urban": ("S","EV"), "Jaecoo 5": ("S","EV"), "MG4": ("S","EV"), "Nevo Q05": ("S","EV"), "ORA 5 EV": ("S","EV"), "ORA 5 HEV": ("S","ICE"),
 # mid + EV
 "Atto 3": ("M","EV"), "EX5": ("M","EV"), "Model 3": ("M","EV"), "MG S5": ("M","EV"),
}
SCENARIOS = {
 "S0 baseline":        {},
 "S1 MG4->M":          {"size": {"MG4": "M"}},
 "S2 Q05+ORA5->M":     {"size": {"Nevo Q05": "M", "ORA 5 EV": "M", "ORA 5 HEV": "M"}},
 "S3 drop ORA5":       {"drop": {"ORA 5 EV", "ORA 5 HEV"}},
 "S4 MG4+Q05+ORA5->M": {"size": {"MG4": "M", "Nevo Q05": "M", "ORA 5 EV": "M", "ORA 5 HEV": "M"}},
}
# (name, min distinct videos, npmi min, cue-only, max models per comment)
# "k3 <=3m" added after the 2nd audit: one price-list comment naming 7 models makes 21 pairs at once.
CONSTRUCTIONS = [("k1", 1, None, False, None), ("k2", 2, None, False, None), ("k3*", 3, None, False, None),
                 ("k5", 5, None, False, None), ("k3+npmi.05", 3, 0.05, False, None),
                 ("k2 cue", 2, None, True, None), ("k3 cue", 3, None, True, None), ("k3 <=3m", 3, None, False, 3)]
GATE = 0.80

rows = []
for r in csv.DictReader(open(SRC, encoding="utf-8")):
    rows.append((r["video_id"], r["comment_id"], set(r["models"].split("|")), int(r["cue"])))
unk = {m for _, _, s, _ in rows for m in s} - set(LABELS)
if unk:
    raise SystemExit(f"Models with no label: {sorted(unk)} - add them to LABELS first.")

def groups(scn):
    sz = {m: v[0] for m, v in LABELS.items()}; fu = {m: v[1] for m, v in LABELS.items()}
    sz.update(scn.get("size", {})); fu.update(scn.get("fuel", {}))
    return {m: f"{sz[m]}-{fu[m]}" for m in LABELS}, set(scn.get("drop", set()))

def stats(dropped, cue_only=False, max_models=None):
    sets = []
    for v, _, ms, cue in rows:
        if cue_only and not cue: continue
        if max_models is not None and len(ms) > max_models: continue
        s = sorted(m for m in ms if m not in dropped)
        if s: sets.append((v, s))
    N = len(sets); n = Counter(); pc = Counter(); pv = defaultdict(set)
    for v, s in sets:
        n.update(s)
        for a, b in itertools.combinations(s, 2):
            pc[(a, b)] += 1; pv[(a, b)].add(v)
    return N, n, pc, pv

def build(st, k, npmi_min):
    N, n, pc, pv = st
    G = nx.Graph()
    for (a, b), c in pc.items():
        vc = len(pv[(a, b)])
        if vc < k: continue
        p = c / N
        npmi = math.log2(p / ((n[a] / N) * (n[b] / N))) / (-math.log2(p)) if p < 1 else 1.0
        if npmi_min is not None and npmi < npmi_min: continue
        G.add_edge(a, b, comments=c, videos=vc, npmi=npmi)
    return G

def analyze(G, grp):
    if G.number_of_edges() == 0: return None
    comps = sorted(nx.connected_components(G), key=len, reverse=True)
    pieces = sum(1 for c in comps if len(c) >= 2)
    giant = G.subgraph(comps[0]).copy()
    inside = sum(1 for a, b in giant.edges if grp[a] == grp[b]) / giant.number_of_edges()
    out = dict(nodes=G.number_of_nodes(), edges=G.number_of_edges(), pieces=pieces,
               giant=giant.number_of_nodes(), inside=inside, giantG=giant)
    if giant.number_of_nodes() < 3:
        out.update(conn="-", after=None, verdict="too small"); return out
    btw = nx.betweenness_centrality(giant, normalized=True)
    top = max(btw.values()); tops = sorted(m for m, v in btw.items() if abs(v - top) < 1e-12)
    H = giant.copy(); H.remove_node(tops[0])
    after = sum(1 for c in nx.connected_components(H) if len(c) >= 2)
    v = ("BRIDGE" if after >= 2 else "COMMUNITIES") if inside >= GATE else "MIXED"
    out.update(conn=tops[0] + ("(tie)" if len(tops) > 1 else ""), after=after, verdict=v, btw=btw)
    return out

print("=== GRAPH SUMMARY (paste this back) ===")
print(f"comments with >=1 model: {len(rows)} | labelled models: {len(LABELS)} | gate: inside share >= {GATE}")
print("construction * = primary (pre-registered). k = min distinct videos per edge.\n")
print(f"{'scenario':<20}{'constr':<12}{'nodes':>6}{'edges':>6}{'pcs':>4}{'giant':>6}{'inside':>7}  {'connector':<16}{'after':>6}  verdict")
results = {}
for sname, scn in SCENARIOS.items():
    grp, dropped = groups(scn); sts = {}
    for cname, k, nm, cue, mm in CONSTRUCTIONS:
        if (cue, mm) not in sts: sts[(cue, mm)] = stats(dropped, cue, mm)
        G = build(sts[(cue, mm)], k, nm); a = analyze(G, grp); results[(sname, cname)] = (a, grp, G)
        if a is None:
            print(f"{sname:<20}{cname:<12}  no edges left"); continue
        af = "-" if a["after"] is None else a["after"]
        print(f"{sname:<20}{cname:<12}{a['nodes']:>6}{a['edges']:>6}{a['pieces']:>4}{a['giant']:>6}{a['inside']:>7.2f}  {a['conn']:<16}{af:>6}  {a['verdict']}")

base, grp, G = results[("S0 baseline", "k3*")]
print("\n=== BASELINE (S0, k3*) DETAILS ===")
if base:
    print(f"nodes with >=1 edge: {base['nodes']} of {len(LABELS)} | edges: {base['edges']} | pieces: {base['pieces']} | giant piece: {base['giant']} nodes")
    if "btw" in base:
        print("top betweenness in the giant piece (name / group / links / links to other groups / betweenness):")
        gG = base["giantG"]
        for m, v in sorted(base["btw"].items(), key=lambda x: -x[1])[:8]:
            cross = sum(1 for nb in gG[m] if grp[nb] != grp[m])
            print(f"  {m:<12}{grp[m]:<7}{gG.degree(m):>3}{cross:>4}{v:>8.3f}")
    print("edges that cross groups (models / groups / comments / videos):")
    for a_, b_, d in sorted(G.edges(data=True), key=lambda e: -e[2]["videos"]):
        if grp[a_] != grp[b_]:
            print(f"  {a_} + {b_}  {grp[a_]}|{grp[b_]}  {d['comments']} / {d['videos']}")
    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/graph_edges_baseline_v2.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["model_a", "group_a", "model_b", "group_b", "comments", "videos", "npmi"])
        for a_, b_, d in G.edges(data=True):
            w.writerow([a_, grp[a_], b_, grp[b_], d["comments"], d["videos"], round(d["npmi"], 3)])

valid = [(k, v[0]) for k, v in results.items() if v[0] and v[0].get("after") is not None]
tops = Counter(a["conn"] for _, a in valid); verd = Counter(a["verdict"] for _, a in valid)
print(f"\n=== STABILITY over {len(valid)} runs with a giant piece of 3+ nodes ===")
print("top connector counts:", dict(tops))
print("verdict counts:", dict(verd))
