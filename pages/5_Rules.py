"""Read-only rules + scoring reference."""
from __future__ import annotations

import streamlit as st

from app_lib import load_venues, page_header

page_header("Rules & Scoring", icon="📜")

st.markdown("""
## Format

- **Period:** May–August 2026 — 4 rounds, one per month.
- **Sessions:** Unlimited per round, all points accumulate.
- **Self-nominated:** Angler picks day and venue in advance; admin issues a session code.
- **Solo allowed** but carries a **-50 point** penalty (strong disincentive — pair up where possible).
- **Catch proof:** photo with session card visible, submitted within 24 hours.

## Scoring
""")

st.table(load_venues().rename(columns={
    "venue": "Venue", "base_pts": "Base pts", "bonus_species": "Bonus species (+50)"
}))

st.markdown("""
| Element | Points |
|---|---|
| Any fish caught | **+2 per fish** (no limit) |
| Bonus species | **+50** (once per session if caught) |
| Partner on the day | **+5 per partner** |
| New partner (first time this league) | **+5 per new pair** |
| Blank session (showed up, no fish) | **+5** |
| Solo penalty | **-50** |

## Session code format

`WL-R<round>-<initials>-<NNN>` — e.g. `WL-R2-SA-014`.

## Card

The session card must show: angler name, session code, round, date, venue, partner(s).
The card must be visible in the catch-proof photo.
""")
