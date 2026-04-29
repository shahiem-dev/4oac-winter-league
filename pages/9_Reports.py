"""Downloadable reports — Leaderboard + Fish Detail per venue (XLSX or PDF)."""
from __future__ import annotations

from datetime import datetime

import streamlit as st

from app_lib import (leaderboard, load_anglers, load_catches, load_sessions,
                     load_venues, page_header, score_all)
from reports import (build_fish_detail_pdf, build_fish_detail_xlsx,
                     build_leaderboard_pdf, build_leaderboard_xlsx,
                     fish_detail_dataframe)

page_header("Reports", icon="📑")
st.caption("Branded XLSX + PDF exports for the league. The 4OAC logo is included automatically "
           "if it's been uploaded under **Admin → Logo**.")

anglers = load_anglers()
sessions = load_sessions()
catches = load_catches()
venues = load_venues()
scored = score_all(sessions, catches, venues)
lb_df = leaderboard(scored, anglers)
fish_df = fish_detail_dataframe(catches, sessions, anglers)

stamp = datetime.now().strftime("%Y%m%d_%H%M")

# ---- Leaderboard --------------------------------------------------------
st.subheader("🏆 Leaderboard")
st.caption(f"{len(lb_df)} angler(s) ranked by points.")
if not lb_df.empty:
    st.dataframe(lb_df, use_container_width=True, hide_index=True)

c1, c2, _ = st.columns([1, 1, 4])
c1.download_button(
    "⬇ XLSX", data=build_leaderboard_xlsx(lb_df),
    file_name=f"4OAC_Leaderboard_{stamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
c2.download_button(
    "⬇ PDF", data=build_leaderboard_pdf(lb_df),
    file_name=f"4OAC_Leaderboard_{stamp}.pdf",
    mime="application/pdf", use_container_width=True,
)

st.divider()

# ---- Fish Detail by Venue -----------------------------------------------
st.subheader("🐟 Details of Fish Caught — by Venue")
st.caption(f"{len(fish_df)} catch(es) across {fish_df['venue'].nunique() if len(fish_df) else 0} venue(s).")
if not fish_df.empty:
    venue_counts = (fish_df.groupby("venue")
                    .agg(catches=("species", "count"),
                         species=("species", "nunique"),
                         anglers=("angler", "nunique"))
                    .reset_index())
    st.dataframe(venue_counts, use_container_width=True, hide_index=True)

c1, c2, _ = st.columns([1, 1, 4])
c1.download_button(
    "⬇ XLSX (sheet per venue)", data=build_fish_detail_xlsx(fish_df),
    file_name=f"4OAC_FishDetail_{stamp}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
c2.download_button(
    "⬇ PDF (one section per venue)", data=build_fish_detail_pdf(fish_df),
    file_name=f"4OAC_FishDetail_{stamp}.pdf",
    mime="application/pdf", use_container_width=True,
)
