"""Settings — exports and danger-zone resets."""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from app_lib import (CATCHES_CSV, SESSIONS_CSV, load_anglers, load_catches,
                     load_sessions, load_venues, page_header, save_catches,
                     save_sessions, score_all)

page_header("Settings", icon="⚙")

# ---- Export -------------------------------------------------------------
st.subheader("Export")
st.caption("Download an Excel snapshot of every sheet.")

if st.button("📤 Build snapshot", type="primary"):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        load_anglers().to_excel(xl, sheet_name="Anglers", index=False)
        load_venues().to_excel(xl, sheet_name="Venues", index=False)
        load_sessions().to_excel(xl, sheet_name="Sessions", index=False)
        load_catches().to_excel(xl, sheet_name="Catches", index=False)
        scored = score_all()
        if not scored.empty:
            scored.to_excel(xl, sheet_name="Scored", index=False)
    fn = f"4OAC_WinterLeague_{datetime.now():%Y%m%d_%H%M}.xlsx"
    st.download_button("⬇ Download snapshot", buf.getvalue(), file_name=fn,
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()

# ---- Danger zone --------------------------------------------------------
st.subheader("Danger zone")
st.caption("These actions are irreversible.")

with st.expander("🗑 Clear all sessions and catches (keeps anglers)"):
    confirm = st.text_input("Type CLEAR to confirm")
    if st.button("Clear sessions + catches", disabled=(confirm != "CLEAR")):
        save_sessions(load_sessions().iloc[0:0])
        save_catches(load_catches().iloc[0:0])
        st.success("Cleared.")
        st.rerun()
