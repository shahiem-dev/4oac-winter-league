"""Manage the angler roster."""
from __future__ import annotations

import streamlit as st

from app_lib import (DIVISIONS, load_anglers, page_header, save_anglers)

page_header("Anglers", icon="👥")
st.caption("Add or edit league participants. `angler_id` and `initials` auto-fill on save if blank.")

df = load_anglers()
edited = st.data_editor(
    df, num_rows="dynamic", use_container_width=True,
    column_config={
        "angler_id": st.column_config.TextColumn("Angler ID", help="Auto-filled from name if blank."),
        "wp_no": st.column_config.TextColumn("WP No"),
        "first_name": st.column_config.TextColumn("First name", required=True),
        "surname": st.column_config.TextColumn("Surname", required=True),
        "initials": st.column_config.TextColumn("Initials", help="Auto from first/surname if blank."),
        "club": st.column_config.TextColumn("Club"),
        "division": st.column_config.SelectboxColumn(
            "Division", options=[""] + list(DIVISIONS.keys()),
            help=" / ".join(f"{k}={v}" for k, v in DIVISIONS.items())),
    },
    key="anglers_editor",
)

if st.button("💾 Save anglers", type="primary"):
    save_anglers(edited)
    st.success(f"Saved {len(edited)} anglers.")
    st.rerun()
