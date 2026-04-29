"""4OAC Winter League — Dashboard."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app_lib import (ROUND_MONTHS, ROUNDS, leaderboard, load_anglers,
                     load_sessions, page_header, score_all)

page_header("4OAC Winter League Tracker")
st.caption("Off-season program · May–August 2026 · 4 rounds, unlimited sessions per round.")

anglers = load_anglers()
sessions = load_sessions()
scored = score_all(sessions)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Anglers", len(anglers))
c2.metric("Sessions logged", len(sessions))
c3.metric("Total fish", int(scored["fish"].sum()) if not scored.empty else 0)
c4.metric("Points awarded", int(scored["total_pts"].sum()) if not scored.empty else 0)

st.divider()

# ---- Round status -------------------------------------------------------
st.subheader("Round status")
cols = st.columns(len(ROUNDS))
for i, r in enumerate(ROUNDS):
    n = int((scored["round"] == r).sum()) if not scored.empty else 0
    cols[i].metric(f"R{r} — {ROUND_MONTHS[r]}", f"{n} sessions")

st.divider()

# ---- Leaderboard preview ------------------------------------------------
st.subheader("🏆 Top 10")
lb = leaderboard(scored, anglers)
if lb.empty:
    st.info("No sessions logged yet. Add anglers on the **Anglers** page, then capture sessions.")
else:
    st.dataframe(lb.head(10), use_container_width=True, hide_index=True)

st.divider()

# ---- Recent sessions ----------------------------------------------------
st.subheader("Recent sessions")
if sessions.empty:
    st.info("No sessions yet.")
else:
    lookup = {r["angler_id"]: f"{r['first_name']} {r['surname']}".strip()
              for _, r in anglers.iterrows()}
    recent = sessions.copy().sort_values("date", ascending=False).head(15)
    recent["angler"] = recent["angler_id"].map(lambda a: lookup.get(a, a))
    if not scored.empty:
        recent = recent.merge(scored[["session_id", "total_pts"]], on="session_id", how="left")
    cols = ["session_id", "round", "date", "angler", "venue", "partners"]
    if "total_pts" in recent.columns:
        cols.append("total_pts")
    st.dataframe(recent[cols], use_container_width=True, hide_index=True)
