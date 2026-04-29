"""Manage the angler roster."""
from __future__ import annotations

import streamlit as st

from app_lib import (ANGLER_COLS, load_anglers, page_header, save_anglers,
                     _make_angler_id, _make_initials)

page_header("Anglers", icon="👥")
st.caption("Add the league participants. `angler_id` and `initials` auto-fill on save if blank.")

df = load_anglers()
edited = st.data_editor(
    df, num_rows="dynamic", use_container_width=True,
    column_config={
        "angler_id": st.column_config.TextColumn("Angler ID", help="Auto-filled from name if blank."),
        "first_name": st.column_config.TextColumn("First name", required=True),
        "surname": st.column_config.TextColumn("Surname", required=True),
        "initials": st.column_config.TextColumn("Initials", help="Auto from first/surname if blank."),
        "club": st.column_config.TextColumn("Club"),
    },
    key="anglers_editor",
)

if st.button("💾 Save anglers", type="primary"):
    save_anglers(edited)
    st.success(f"Saved {len(edited)} anglers.")
    st.rerun()
