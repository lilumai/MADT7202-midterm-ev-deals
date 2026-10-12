# MADT 7202 Mid-Term: Geely or MG first? (evidence repository)

Evidence for the one-page report, which is submitted separately. Every number in the report is printed by one of the scripts below.

Question: each month a Thai bank's Head of Pricing and Strategy (auto finance) spends a fixed rate-subsidy budget on car-maker deals. Does any car model link separate shopper groups, and do Geely and MG draw on the same shoppers?

## Data
- YouTube Data API v3: 817 videos and 23,291 top-level comments, 1 Jan to 11 Oct 2026. Batch 1 used 4 generic queries (youtube_collect.py), batch 2 used 6 generic queries (youtube_collect2.py); the two batches share no video. No model name was used as a search term. Raw comment text is NOT in this repo; only ids and model names are (data/processed/).
- Pantip car room: 11 thread titles naming two models (data/raw/pantip_manual.csv: thread id, date, the two models; no usernames). Pantip blocks bots, so the titles were found and read by hand through the site's own search for two generic phrases. An earlier AI-assisted browsing attempt produced a candidate list that was discarded and not used. Before Pantip's bot-block notice was seen, a short structure-check script sent 3 page requests to Pantip (a search page, a room page, one thread page); it is not included here and nothing from it is used.
- No author or channel names were stored. The API key is read from the YOUTUBE_API_KEY environment variable and is in no file.

## Run order (from this folder)
| Step | Script | Prints or writes | Used in report |
|---|---|---|---|
| 1 | youtube_collect.py, youtube_collect2.py | raw data (not committed) | 3 Data |
| 2 | extract_candidates.py | window check, name candidates | 3 Data |
| 3 | count_models_v2.py | model mentions, ORA 5 split EV/HEV, comment_models_v2.csv | 3 Data, 4 Filtering |
| 4 | build_graph_v2.py | 23 nodes, 26 links, 3 pieces; inside share; betweenness; 40-run robustness grid; graph_edges_baseline_v2.csv | 4 Result and Alternatives, 6 Findings |
| 5 | cross_fuel_check.py | fuel-crossing links at 1, 2, 3 videos; Geely to MG paths | 6 Findings 1-2 |
| 6 | batch_replication.py | batch 1 vs batch 2 | 3 Corroboration, 6 Finding 1 |
| 7 | pantip_check.py | Pantip counts; models missing from the alias list | 3 Data, 6, 8 |
| 8 | inspect_edges.py | comments behind chosen pairs (hand audit, read locally) | 4 Filtering, 6 Finding 3, 8 |
| 9 | make_figure.py | figure_baseline.png | 5 The picture |
| 10 | count_models_v3.py, build_graph_v3.py, cross_fuel_check_v3.py | sensitivity: Aion V and Aion Y added as nodes | 4 Alternatives |
| 11 | count_models_v4.py, build_graph_v4.py, cross_fuel_check_v4.py | sensitivity: v3 plus Thai spellings of 6 models (Yaris, Yaris Ativ, Yaris Cross, Kicks, Swift, Dolphin): 29 links, 0 fuel-crossing, no Geely to MG path at 3 or more videos; City is the top connector in 30 of 40 runs | 4 Alternatives, 6 Finding 3 |

## Decisions fixed before results
Edge = two models in one comment; keep a pair only if seen under 3 or more different videos; groups = size x fuel (ICE incl. HEV/PHEV/REEV, or BEV); gate: inside share 0.80 or more and one piece without the top-betweenness node means no bridge.
Changed after the hand audit and disclosed in the report: ORA 5 split into EV and HEV; choice-word and max-3-models variants added; Aion V and Y, and Thai spellings of 6 models, added as sensitivity tests (v3, v4).

## Limits
Commenters are not buyers; creators choose which models a video compares; one person may post under several videos; MG5, MG ZS, MG HS and most Thai spellings are not matched by the name list (MG5/ZS/HS: 22 comments or fewer); the Pantip list comes from scrolling two search result lists and may be incomplete.

## Install
pip install -r requirements.txt (Python 3.9 or later)
