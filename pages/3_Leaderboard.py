"""Overall and per-round leaderboards."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app_lib import (ROUNDS, ROUND_MONTHS, leaderboard, load_anglers,
                     load_sessions, page_header, score_all)

page_header("Leaderboard", icon="🏆")

anglers = load_anglers()
sessions = load_sessions()
scored = score_all(sessions)

if scored.empty:
    st.info("No sessions yet — log one on the **Sessions** page.")
    st.stop()

tabs = st.tabs(["Overall"] + [f"R{r}" for r in ROUNDS])

with tabs[0]:
    lb = leaderboard(scored, anglers)
    st.dataframe(lb, use_container_width=True, hide_index=True)

for i, r in enumerate(ROUNDS, start=1):
    with tabs[i]:
        st.caption(ROUND_MONTHS[r])
        sub = scored[scored["round"] == r]
        if sub.empty:
            st.info(f"No sessions in Round {r} yet.")
        else:
            lb_r = leaderboard(sub, anglers)
            st.dataframe(lb_r, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Session breakdown")
lookup = {r["angler_id"]: f"{r['first_name']} {r['surname']}".strip()
          for _, r in anglers.iterrows()}
view = scored.copy()
view["angler"] = view["angler_id"].map(lambda a: lookup.get(a, a))
cols = ["session_id", "round", "date", "angler", "venue", "fish",
        "bonus_caught", "partners", "new_pairs", "blank", "solo",
        "base_pts", "fish_pts", "bonus_pts", "partner_pts",
        "new_pair_pts", "blank_pts", "solo_pts", "total_pts"]
st.dataframe(view[cols].sort_values(["round", "date"]),
             use_container_width=True, hide_index=True)
