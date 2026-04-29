"""Partner tracker — pairs and 'first time together' bonuses."""
from __future__ import annotations

from itertools import combinations

import pandas as pd
import streamlit as st

from app_lib import (load_anglers, load_sessions, page_header, parse_partners)

page_header("Partner Tracker", icon="🤝")
st.caption("Who has fished with whom. New pairings each grant +5 to both anglers (first time only).")

anglers = load_anglers()
sessions = load_sessions()

if sessions.empty:
    st.info("No sessions yet.")
    st.stop()

lookup = {r["angler_id"]: f"{r['first_name']} {r['surname']}".strip()
          for _, r in anglers.iterrows()}

# Build pair-encounter rows: for each session, every (focal, partner) and (partner, partner)
rows = []
for _, s in sessions.sort_values("date").iterrows():
    partners = parse_partners(s.get("partners", ""))
    everyone = [s["angler_id"]] + partners
    for a, b in combinations(sorted(set(everyone)), 2):
        rows.append({"a": a, "b": b, "date": s["date"], "session_id": s["session_id"],
                     "round": int(s["round"] or 0)})

if not rows:
    st.info("No partner data yet — all sessions so far are solo.")
    st.stop()

pairs = pd.DataFrame(rows)
pairs["a_name"] = pairs["a"].map(lambda x: lookup.get(x, x))
pairs["b_name"] = pairs["b"].map(lambda x: lookup.get(x, x))
pairs["pair"] = pairs["a_name"] + " ↔ " + pairs["b_name"]

st.subheader("All pairings")
summary = (pairs.groupby("pair")
           .agg(times_together=("session_id", "count"),
                first_seen=("date", "min"),
                last_seen=("date", "max"))
           .reset_index()
           .sort_values("times_together", ascending=False))
st.dataframe(summary, use_container_width=True, hide_index=True)

st.divider()

st.subheader("Unique pairs per round")
per_round = pairs.drop_duplicates(["a", "b", "round"]).groupby("round").size()
st.bar_chart(per_round)

st.divider()

st.subheader("Solo sessions (-10 each)")
solo_count = (sessions["solo"].astype(bool)).sum() if "solo" in sessions.columns else 0
solo_view = sessions[sessions["solo"].astype(bool)].copy()
solo_view["angler"] = solo_view["angler_id"].map(lambda a: lookup.get(a, a))
st.metric("Solo sessions", int(solo_count))
if len(solo_view):
    st.dataframe(solo_view[["session_id", "round", "date", "angler", "venue"]],
                 use_container_width=True, hide_index=True)
