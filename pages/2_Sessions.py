"""Issue codes, log sessions against issued codes, manage existing sessions."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app_lib import (ROUNDS, STATUS_ISSUED, STATUS_LOGGED, issue_code,
                     load_anglers, load_catches, load_sessions, load_venues,
                     page_header, save_catches, save_sessions, score_session)

page_header("Sessions", icon="🐟")
st.caption("Step 1 — issue a code to the angler. Step 2 — log the catches when proof comes in.")

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

tab_issue, tab_log, tab_all = st.tabs(
    ["🎟 Issue Code", "📝 Log session", "📋 All sessions"])

# ------------------------------------------------------------------------
# 🎟 Issue Code
# ------------------------------------------------------------------------
with tab_issue:
    st.subheader("Issue a session code")
    st.caption("Generates `WL-R<round>-<initials>-<NNN>` and reserves it for the angler. "
               "Show this code on their session card — it will appear in the photo proof.")

    c1, c2 = st.columns(2)
    angler = c1.selectbox("Angler", angler_ids,
                          format_func=lambda a: lookup.get(a, a),
                          key="issue_angler")
    rnd = c2.selectbox("Round", ROUNDS, key="issue_round")

    c3, c4 = st.columns(2)
    planned_date = c3.date_input("Planned date (optional)",
                                 value=None, key="issue_date")
    planned_venue = c4.selectbox("Planned venue (optional)",
                                 [""] + venues["venue"].tolist(),
                                 key="issue_venue")

    if st.button("🎟 Issue code", type="primary"):
        date_str = planned_date.isoformat() if planned_date else ""
        code = issue_code(angler, int(rnd), date_str, planned_venue)
        st.success("Code issued.")
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;letter-spacing:2px;"
            f"background:#FFF4D6;padding:18px 24px;border-radius:10px;"
            f"text-align:center;margin:8px 0;'>{code}</div>",
            unsafe_allow_html=True,
        )
        st.code(code, language=None)
        st.caption("Click the copy icon on the right of the code box to copy. "
                   "Hand this to the angler — it must be visible in the catch-proof photo.")

    st.divider()

    st.markdown("**Issued — awaiting catches**")
    pending = sessions[sessions["status"] == STATUS_ISSUED].copy()
    if pending.empty:
        st.info("No outstanding codes.")
    else:
        pending["angler"] = pending["angler_id"].map(lambda a: lookup.get(a, a))
        st.dataframe(
            pending[["session_id", "round", "date", "angler", "venue"]]
                .rename(columns={"date": "planned_date", "venue": "planned_venue"}),
            use_container_width=True, hide_index=True,
        )

# ------------------------------------------------------------------------
# 📝 Log session
# ------------------------------------------------------------------------
with tab_log:
    st.subheader("Log catches against an issued code")

    pending = sessions[sessions["status"] == STATUS_ISSUED].copy()
    if pending.empty:
        st.info("No issued codes to log against. Issue one in the **Issue Code** tab first.")
    else:
        pending["label"] = pending.apply(
            lambda r: f"{r['session_id']} — {lookup.get(r['angler_id'], r['angler_id'])} "
                      f"(R{r['round']}{', ' + r['date'] if r['date'] else ''})",
            axis=1,
        )
        pick = st.selectbox("Issued code", pending["label"].tolist(), key="log_pick")
        chosen = pending[pending["label"] == pick].iloc[0]
        sid = chosen["session_id"]

        c1, c2 = st.columns(2)
        date = c1.date_input(
            "Actual date",
            value=pd.to_datetime(chosen["date"]).date()
            if chosen["date"] else None,
            key=f"log_date_{sid}",
        )
        venue_opts = venues["venue"].tolist()
        v_idx = venue_opts.index(chosen["venue"]) if chosen["venue"] in venue_opts else 0
        venue = c2.selectbox("Venue", venue_opts, index=v_idx, key=f"log_venue_{sid}")

        v_row = venues[venues["venue"] == venue].iloc[0]
        st.caption(f"Primary venue base **{v_row['base_pts']} pts** · "
                   f"Bonus species: **{v_row['bonus_species']}** (+50 each).")

        partner_ids = [a for a in angler_ids if a != chosen["angler_id"]]
        partners = st.multiselect("Partner(s) on the day", partner_ids,
                                  format_func=lambda a: lookup.get(a, a),
                                  help="Leave empty for solo (-10).",
                                  key=f"log_partners_{sid}")
        photo_url = st.text_input("Photo proof URL", key=f"log_photo_{sid}")
        notes = st.text_area("Notes", height=80, key=f"log_notes_{sid}")

        st.markdown("**Catches**")
        st.caption("Set per-catch **venue** if the angler fished more than one spot in this session. "
                   "Each unique venue fished adds its base points; each fish matching that venue's "
                   "bonus species earns +50.")
        blank = pd.DataFrame({"species": [""], "length_cm": [""],
                              "venue": [venue], "notes": [""]})
        new_catches = st.data_editor(
            blank, num_rows="dynamic", use_container_width=True,
            column_config={
                "species": st.column_config.TextColumn("Species"),
                "length_cm": st.column_config.TextColumn("Length (cm)"),
                "venue": st.column_config.SelectboxColumn(
                    "Venue", options=venues["venue"].tolist(),
                    help="Defaults to the session's primary venue."),
                "notes": st.column_config.TextColumn("Notes"),
            },
            key=f"log_catches_{sid}",
        )

        if st.button("💾 Save logged session", type="primary", key=f"log_save_{sid}"):
            sessions.loc[sessions["session_id"] == sid, "date"] = (
                date.isoformat() if date else "")
            sessions.loc[sessions["session_id"] == sid, "venue"] = venue
            sessions.loc[sessions["session_id"] == sid, "partners"] = ";".join(partners)
            sessions.loc[sessions["session_id"] == sid, "solo"] = (len(partners) == 0)
            sessions.loc[sessions["session_id"] == sid, "photo_url"] = photo_url.strip()
            sessions.loc[sessions["session_id"] == sid, "notes"] = notes.strip()
            sessions.loc[sessions["session_id"] == sid, "status"] = STATUS_LOGGED
            save_sessions(sessions)

            valid = new_catches[new_catches["species"].astype(str).str.strip() != ""].copy()
            if len(valid):
                valid["session_id"] = sid
                save_catches(pd.concat([catches, valid], ignore_index=True))

            score = score_session(
                sessions[sessions["session_id"] == sid].iloc[0],
                pd.concat([catches, valid], ignore_index=True) if len(valid) else catches,
                sessions, venues,
            )
            st.success(f"✓ {sid} logged — **{score['total_pts']} pts** "
                       f"({score['fish']} fish, {score['partners']} partner(s), "
                       f"{score['new_pairs']} new pair(s))")
            st.rerun()

# ------------------------------------------------------------------------
# 📋 All sessions
# ------------------------------------------------------------------------
with tab_all:
    if sessions.empty:
        st.info("No sessions yet.")
    else:
        view = sessions.copy()
        view["angler"] = view["angler_id"].map(lambda a: lookup.get(a, a))
        st.dataframe(
            view[["session_id", "status", "round", "date", "angler", "venue",
                  "partners", "photo_url", "notes"]],
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.markdown("**Edit / delete catches**")
        edited = st.data_editor(
            catches, num_rows="dynamic", use_container_width=True,
            key="catches_editor")
        if st.button("💾 Save catch edits"):
            save_catches(edited)
            st.success(f"Saved {len(edited)} catch rows.")
            st.rerun()
