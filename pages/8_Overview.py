"""Live dashboard — selectable charts (bar / pie / line)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app_lib import (ROUNDS, ROUND_MONTHS, leaderboard, load_anglers,
                     load_catches, load_sessions, load_venues, page_header,
                     score_all)
from reports import fish_detail_dataframe
from theme import load_theme

page_header("Overview", icon="📊")

theme = load_theme()
PRIMARY = theme["sidebar_bg"]
ACCENT = theme["sidebar_heading"]
PALETTE = [PRIMARY, ACCENT, "#13315C", "#3F88C5", "#FFD60A",
           "#1F7A8C", "#94A3B8", "#0EA5E9", "#F59E0B", "#EF4444"]

anglers = load_anglers()
sessions = load_sessions()
catches = load_catches()
venues = load_venues()
scored = score_all(sessions, catches, venues)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Anglers", len(anglers))
c2.metric("Sessions logged", int((sessions["status"] == "logged").sum())
          if "status" in sessions.columns else len(sessions))
c3.metric("Total fish", int(scored["fish"].sum()) if not scored.empty else 0)
c4.metric("Points awarded", int(scored["total_pts"].sum()) if not scored.empty else 0)

if scored.empty:
    st.info("No logged sessions yet — capture some first to populate charts.")
    st.stop()

st.divider()

chart_type = st.radio("Chart style", ["Bar", "Pie", "Line"],
                      horizontal=True, key="ov_chart_type")

# ---- Top anglers --------------------------------------------------------
st.subheader("🏆 Top anglers by points")
lb = leaderboard(scored, anglers).head(10)
if chart_type == "Bar":
    fig = px.bar(lb, x="angler", y="points",
                 color="points", color_continuous_scale=[[0, PRIMARY], [1, ACCENT]],
                 text="points")
    fig.update_traces(textposition="outside")
elif chart_type == "Pie":
    fig = px.pie(lb, names="angler", values="points",
                 color_discrete_sequence=PALETTE, hole=0.35)
else:
    fig = px.line(lb, x="angler", y="points", markers=True,
                  color_discrete_sequence=[PRIMARY])
fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=420)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---- Catches per venue --------------------------------------------------
st.subheader("📍 Catches per venue")
fish_df = fish_detail_dataframe(catches, sessions, anglers)
if fish_df.empty:
    st.info("No catches recorded yet.")
else:
    by_venue = (fish_df.groupby("venue")
                .agg(catches=("species", "count"),
                     anglers=("angler", "nunique"))
                .reset_index()
                .sort_values("catches", ascending=False))
    if chart_type == "Bar":
        fig = px.bar(by_venue, x="venue", y="catches",
                     color="catches",
                     color_continuous_scale=[[0, PRIMARY], [1, ACCENT]],
                     text="catches")
        fig.update_traces(textposition="outside")
    elif chart_type == "Pie":
        fig = px.pie(by_venue, names="venue", values="catches",
                     color_discrete_sequence=PALETTE, hole=0.35)
    else:
        fig = px.line(by_venue, x="venue", y="catches", markers=True,
                      color_discrete_sequence=[PRIMARY])
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=420)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---- Species mix --------------------------------------------------------
st.subheader("🐟 Species mix")
if not fish_df.empty:
    by_species = (fish_df.groupby("species")
                  .size().reset_index(name="catches")
                  .sort_values("catches", ascending=False).head(15))
    if chart_type == "Bar":
        fig = px.bar(by_species, x="species", y="catches",
                     color="catches",
                     color_continuous_scale=[[0, PRIMARY], [1, ACCENT]],
                     text="catches")
        fig.update_traces(textposition="outside")
    elif chart_type == "Pie":
        fig = px.pie(by_species, names="species", values="catches",
                     color_discrete_sequence=PALETTE, hole=0.35)
    else:
        fig = px.line(by_species, x="species", y="catches", markers=True,
                      color_discrete_sequence=[PRIMARY])
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=420)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No catches recorded yet.")

st.divider()

# ---- Round progress -----------------------------------------------------
st.subheader("📅 Sessions per round")
per_round = (scored.groupby("round").size().reindex(ROUNDS, fill_value=0)
             .reset_index(name="sessions"))
per_round["round_label"] = per_round["round"].map(lambda r: f"R{r} — {ROUND_MONTHS.get(r, '')}")
if chart_type == "Bar":
    fig = px.bar(per_round, x="round_label", y="sessions",
                 color="sessions",
                 color_continuous_scale=[[0, PRIMARY], [1, ACCENT]],
                 text="sessions")
    fig.update_traces(textposition="outside")
elif chart_type == "Pie":
    fig = px.pie(per_round, names="round_label", values="sessions",
                 color_discrete_sequence=PALETTE, hole=0.35)
else:
    fig = px.line(per_round, x="round_label", y="sessions", markers=True,
                  color_discrete_sequence=[PRIMARY])
fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=380)
st.plotly_chart(fig, use_container_width=True)
