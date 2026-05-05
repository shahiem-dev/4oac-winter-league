"""4OAC Winter League — Dashboard."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app_lib import (ROUND_MONTHS, ROUNDS, leaderboard, load_anglers,
                     load_sessions, page_header, score_all)

page_header("4OAC Winter League", show_title=False)

from theme import find_logo, render_home_logo, save_logo
hcol_logo, hcol_text = st.columns([1, 5], vertical_alignment="center")
with hcol_logo:
    render_home_logo(width=180)
with hcol_text:
    st.markdown(
        "<h1 style='font-size:2.6rem; margin:0; color:#0B2545;'>4OAC Winter League</h1>"
        "<p style='font-size:1rem; margin:6px 0 0; color:#555;'>"
        "Off-season program · May–August 2026 · 4 rounds, unlimited sessions per round.</p>",
        unsafe_allow_html=True,
    )

with st.expander("🖼 Upload / replace 4OAC logo", expanded=(find_logo() is None)):
    up = st.file_uploader("Choose a logo (png, jpg, jpeg, webp)",
                          type=["png", "jpg", "jpeg", "webp"],
                          key="home_logo_uploader")
    if up is not None and st.button("💾 Save logo", type="primary", key="home_logo_save"):
        out = save_logo(up)
        st.success(f"Saved to `{out.relative_to(out.parent.parent)}`. Reload to see it.")
        st.rerun()
    if find_logo() is None:
        st.caption("Or drop a file directly at `assets/4oac_logo.png` and refresh.")

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
