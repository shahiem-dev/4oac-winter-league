"""Read-only rules + scoring reference."""
from __future__ import annotations

import streamlit as st

from app_lib import load_venues, page_header

page_header("Rules & Scoring", icon="📜")

# ── Format ────────────────────────────────────────────────────────────────────
st.markdown("""
## Format

| | |
|---|---|
| **Period** | May – August 2026 — 4 rounds, one per month |
| **Sessions per round** | 2 per angler (all points accumulate) |
| **Self-nominated** | Angler picks day, start time and venue in advance; admin issues a session code |
| **Solo** | Allowed, but carries a **−100 point** penalty — pair up where possible |
| **Catch proof** | Photo with session card visible, submitted within **24 hours** |
| **Late submission** | Cards submitted late with metadata proof accepted — **50% of points only** |
""")

# ── Venue scoring ─────────────────────────────────────────────────────────────
st.markdown("## Venue Scoring")
st.table(load_venues().rename(columns={
    "venue":         "Venue",
    "base_pts":      "Base pts",
    "bonus_species": "Bonus species",
}))

# ── Points at a glance ────────────────────────────────────────────────────────
st.markdown("""
## Points at a Glance

| Element | Points |
|---|---|
| Any fish caught | **+2 per fish** (no limit) |
| Bonus species — first catch per venue per session | **+50** |
| Bonus species — further catches at same venue | **+2** (same as any fish) |
| Partner on the day | **+5 per partner** |
| New partner (first time this league) | **+15 per new pair** |
| Blank session (showed up, caught nothing) | **+5** |
| Solo penalty | **−100** |
| Late card submission | **50% of total points** |

## Session Code Format

`WL-R<round>-<initials>-<NNN>-<HHMM>` — e.g. `WL-R2-SA-014-0630`

The code encodes: **round · angler initials · session number · start time**.

## Session Card

The session card must show: angler name · session code · round · date · start time · venue · partner(s).
The card **must be visible** in the catch-proof photo.
""")

# ── The Venues ────────────────────────────────────────────────────────────────
st.markdown("## The Venues")

venues_info = [
    ("🌊 False Bay",      "50 pts", "Kob",                   "Glencairn to Mac's Mouth"),
    ("⛰ Mountains",       "40 pts", "Cow Shark",              "Strand Fence to Jock's se Baai"),
    ("🌿 Overberg",        "30 pts", "White Steenbras",        "Botrivier to Rietfontein"),
    ("🏖 Struisbaai",      "20 pts", "Ragged Tooth Shark",     "Varswater to De Mond"),
    ("🪨 Brandfontein",    "20 pts", "Galjoen",                "Car Park to Varswater"),
    ("⚓ Arniston",        "20 pts", "White Musselcracker",    "Left of De Mond to Derde Baai fence"),
    ("🏝 Witsands",        "10 pts", "Grunter",                "Entire area"),
]

for name, pts, bonus, boundary in venues_info:
    with st.container():
        col_name, col_pts, col_bonus, col_area = st.columns([2, 1, 2, 3])
        col_name.markdown(f"**{name}**")
        col_pts.markdown(f"`{pts}`")
        col_bonus.markdown(f"🎯 {bonus}")
        col_area.markdown(f"📍 _{boundary}_")
    st.divider()
