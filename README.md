# 4OAC Winter League Tracker

Streamlit app for the **4 Oceans Angling Club Winter League** (May–August 2026).

## Quick start (local)

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy to Streamlit Community Cloud

1. Push this repo to GitHub.
2. Connect at [share.streamlit.io](https://share.streamlit.io) → pick the repo → main file `Home.py`.
3. Done. Subsequent `git push` triggers an auto-redeploy.

> **Storage caveat:** Streamlit Cloud disk is ephemeral. Capture sessions **locally**, then `git push` so CSVs land in the repo. Captures made on the live site are lost on redeploy.

## Scoring summary

| Element | Points |
|---|---|
| Venue base — False Bay | 50 |
| Venue base — Mountains | 40 |
| Venue base — Overberg | 30 |
| Venue base — Struisbaai | 20 |
| Venue base — Brandfontein/Arniston | 20 |
| Venue base — Witsands | 10 |
| Any fish caught | +2 per fish |
| Bonus species (venue-specific) | +50 (once per session) |
| Partner on the day | +5 per partner |
| New partner (first time this league) | +5 per new pair |
| Blank session (showed up, no fish) | +5 |
| Solo penalty | -50 |

Bonus species per venue:
- False Bay → Kob
- Mountains → Cow Shark
- Overberg → Steenbras
- Struisbaai → Ragged Tooth Shark
- Brandfontein/Arniston → Galjoen
- Witsands → Grunter

## Session code format
`WL-R<round>-<initials>-<NNN>` — e.g. `WL-R2-SA-014`.

## Data layout

```
data/
├── anglers.csv       angler_id, first_name, surname, initials, club
├── venues.csv        venue, base_pts, bonus_species
├── sessions.csv      session_id, round, date, angler_id, venue, partners, solo, photo_url, notes
└── catches.csv       session_id, species, length_cm, notes
```

`partners` is a semicolon-joined list of `angler_id` values.
