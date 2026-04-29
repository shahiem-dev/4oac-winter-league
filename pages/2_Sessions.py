"""Capture and edit fishing sessions + per-session catches."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app_lib import (ROUNDS, load_anglers, load_catches, load_sessions,
                     load_venues, make_session_code, page_header,
                     save_catches, save_sessions, score_session)

page_header("Sessions", icon="🐟")
st.caption("Log every session. Each session belongs to one angler; partners are listed separately.")

anglers = load_anglers()
venues = load_venues()
sessions = load_sessions()
catches = load_catches()

if anglers.empty:
    st.warning("Add anglers first on the **Anglers** page.")
    st.stop()

lookup = {r["angler_id"]: f"{r['first_name']} {r['surname']} ({r['initials']})".strip()
          for _, r in anglers.iterrows()}
angler_ids = list(lookup.keys())

tab_new, tab_edit = st.tabs(["➕ New session", "📋 All sessions"])

# ---- New session --------------------------------------------------------
with tab_new:
    c1, c2 = st.columns(2)
    angler = c1.selectbox("Angler", angler_ids,
                          format_func=lambda a: lookup.get(a, a))
    rnd = c2.selectbox("Round", ROUNDS)

    c3, c4 = st.columns(2)
    date = c3.date_input("Date").isoformat()
    venue = c4.selectbox("Venue", venues["venue"].tolist())

    venue_row = venues[venues["venue"] == venue].iloc[0]
    st.caption(f"Base **{venue_row['base_pts']} pts** · "
               f"Bonus species: **{venue_row['bonus_species']}** (+50 if caught)")

    partner_ids = [a for a in angler_ids if a != angler]
    partners = st.multiselect("Partner(s) on the day", partner_ids,
                              format_func=lambda a: lookup.get(a, a),
                              help="Leave empty for solo (-10 penalty applies).")
    photo_url = st.text_input("Photo proof URL (Drive/Dropbox link)",
                              help="Photo with session card visible, submitted within 24h.")
    notes = st.text_area("Notes (optional)", height=80)

    st.markdown("**Catches in this session**")
    n_default = int(st.session_state.get("new_n_catches", 1))
    blank_catches = pd.DataFrame({"species": [""] * n_default,
                                  "length_cm": [""] * n_default,
                                  "notes": [""] * n_default})
    new_catches = st.data_editor(
        blank_catches, num_rows="dynamic", use_container_width=True,
        column_config={
            "species": st.column_config.TextColumn("Species"),
            "length_cm": st.column_config.TextColumn("Length (cm)"),
            "notes": st.column_config.TextColumn("Notes"),
        },
        key="new_session_catches",
    )

    if st.button("💾 Save session", type="primary"):
        ang_row = anglers[anglers["angler_id"] == angler].iloc[0]
        code = make_session_code(int(rnd), ang_row["initials"], sessions)
        new_sess = pd.DataFrame([{
            "session_id": code,
            "round": int(rnd),
            "date": date,
            "angler_id": angler,
            "venue": venue,
            "partners": ";".join(partners),
            "solo": len(partners) == 0,
            "photo_url": photo_url.strip(),
            "notes": notes.strip(),
        }])
        save_sessions(pd.concat([sessions, new_sess], ignore_index=True))

        valid_catches = new_catches[new_catches["species"].astype(str).str.strip() != ""].copy()
        if len(valid_catches):
            valid_catches["session_id"] = code
            save_catches(pd.concat([catches, valid_catches], ignore_index=True))

        all_sess = pd.concat([sessions, new_sess], ignore_index=True)
        all_catches = (pd.concat([catches, valid_catches], ignore_index=True)
                       if len(valid_catches) else catches)
        score = score_session(new_sess.iloc[0], all_catches, all_sess, venues)
        st.success(f"✓ {code} saved — **{score['total_pts']} pts** "
                   f"({score['fish']} fish, {score['partners']} partner(s), "
                   f"{score['new_pairs']} new pair(s))")
        st.rerun()

# ---- All sessions -------------------------------------------------------
with tab_edit:
    if sessions.empty:
        st.info("No sessions yet.")
    else:
        st.caption("Edit existing sessions. To delete, clear the row.")
        view = sessions.copy()
        view["angler"] = view["angler_id"].map(lambda a: lookup.get(a, a))
        cols_show = ["session_id", "round", "date", "angler", "venue",
                     "partners", "solo", "photo_url", "notes"]
        st.dataframe(view[cols_show], use_container_width=True, hide_index=True)

        st.divider()
        st.markdown("**Edit / delete catches**")
        edited = st.data_editor(
            catches, num_rows="dynamic", use_container_width=True,
            key="catches_editor")
        if st.button("💾 Save catch edits"):
            save_catches(edited)
            st.success(f"Saved {len(edited)} catch rows.")
            st.rerun()
