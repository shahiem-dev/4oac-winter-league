"""Issue codes, log sessions against issued codes, manage existing sessions."""
from __future__ import annotations

from datetime import datetime, time as dtime
from pathlib import Path

import pandas as pd
import streamlit as st

from app_lib import (ROUNDS, SESSIONS_PER_ROUND, STATUS_ISSUED, STATUS_LOGGED,
                     UPLOADS_DIR, issue_code, load_anglers, load_catches,
                     load_sessions, load_species, load_venues, page_header,
                     save_catches, save_sessions, score_session)

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def _save_upload(uploaded_file) -> str:
    """Save uploaded file to /uploads with timestamp prefix. Returns path string."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = Path(uploaded_file.name).name
    dest      = UPLOADS_DIR / f"{ts}_{safe_name}"
    with open(dest, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return str(dest)


page_header("Sessions", icon="🐟")
st.caption("Step 1 — issue a code to the angler. Step 2 — log the catches when proof comes in.")

anglers  = load_anglers()
venues   = load_venues()
sessions = load_sessions()
catches  = load_catches()
species_list = load_species()

if anglers.empty:
    st.warning("Add anglers first on the **Anglers** page.")
    st.stop()

lookup = {r["angler_id"]: f"{r['first_name']} {r['surname']} ({r['initials']})".strip()
          for _, r in anglers.iterrows()}
angler_ids = list(lookup.keys())

tab_issue, tab_log, tab_all = st.tabs(
    ["🎟 Issue Code", "📝 Log session", "📋 All sessions"])

# ─────────────────────────────────────────────────────────────────────────────
# 🎟  ISSUE CODE
# ─────────────────────────────────────────────────────────────────────────────
with tab_issue:
    st.subheader("Issue a session code")
    st.caption(
        "Generates `WL-R<round>-<initials>-<NNN>-<HHMM>` and reserves it for the angler. "
        "The code must be visible on the session card and in the catch-proof photo."
    )

    c1, c2 = st.columns(2)
    angler = c1.selectbox("Angler", angler_ids,
                          format_func=lambda a: lookup.get(a, a),
                          key="issue_angler")
    rnd = c2.selectbox("Round", ROUNDS, key="issue_round")

    # Warn if angler already has max sessions in this round
    existing = sessions[
        (sessions["angler_id"] == angler) &
        (sessions["round"] == int(rnd))
    ]
    if len(existing) >= SESSIONS_PER_ROUND:
        st.warning(
            f"⚠️ **{lookup.get(angler, angler)}** already has "
            f"{len(existing)} session(s) in Round {rnd} "
            f"(max {SESSIONS_PER_ROUND}). Issuing another will exceed the limit."
        )

    c3, c4, c5 = st.columns(3)
    planned_date  = c3.date_input("Planned date (optional)", value=None, key="issue_date")
    planned_venue = c4.selectbox("Planned venue (optional)",
                                 [""] + venues["venue"].tolist(), key="issue_venue")
    start_time_val = c5.time_input("Start time", value=dtime(6, 0), key="issue_time")

    if st.button("🎟 Issue code", type="primary"):
        date_str = planned_date.isoformat() if planned_date else ""
        time_str = start_time_val.strftime("%H:%M")
        code = issue_code(angler, int(rnd), date_str, planned_venue, time_str)
        st.success("Code issued.")
        st.markdown(
            f"<div style='font-size:32px;font-weight:700;letter-spacing:2px;"
            f"background:#FFF4D6;padding:18px 24px;border-radius:10px;"
            f"text-align:center;margin:8px 0;'>{code}</div>",
            unsafe_allow_html=True,
        )
        st.code(code, language=None)
        st.caption("Click the copy icon to copy. Hand this to the angler — "
                   "it must be visible in the catch-proof photo.")

    st.divider()
    st.markdown("**Issued — awaiting catches**")
    pending = sessions[sessions["status"] == STATUS_ISSUED].copy()
    if pending.empty:
        st.info("No outstanding codes.")
    else:
        pending["angler"] = pending["angler_id"].map(lambda a: lookup.get(a, a))
        st.dataframe(
            pending[["session_id", "round", "date", "start_time", "angler", "venue"]]
                .rename(columns={"date": "planned_date", "venue": "planned_venue",
                                 "start_time": "start"}),
            use_container_width=True, hide_index=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# 📝  LOG SESSION
# ─────────────────────────────────────────────────────────────────────────────
with tab_log:
    st.subheader("Log catches against an issued code")

    pending = sessions[sessions["status"] == STATUS_ISSUED].copy()
    if pending.empty:
        st.info("No issued codes to log against. Issue one in the **Issue Code** tab first.")
    else:
        pending["label"] = pending.apply(
            lambda r: (
                f"{r['session_id']} — {lookup.get(r['angler_id'], r['angler_id'])} "
                f"(R{r['round']}{', ' + r['date'] if r['date'] else ''})"
            ),
            axis=1,
        )
        pick   = st.selectbox("Issued code", pending["label"].tolist(), key="log_pick")
        chosen = pending[pending["label"] == pick].iloc[0]
        sid    = chosen["session_id"]

        c1, c2, c3 = st.columns(3)
        date = c1.date_input(
            "Actual date",
            value=pd.to_datetime(chosen["date"]).date() if chosen["date"] else None,
            key=f"log_date_{sid}",
        )
        venue_opts = venues["venue"].tolist()
        v_idx  = venue_opts.index(chosen["venue"]) if chosen["venue"] in venue_opts else 0
        venue  = c2.selectbox("Primary venue", venue_opts, index=v_idx,
                              key=f"log_venue_{sid}")
        # Parse stored time for the time_input default
        stored_time = chosen.get("start_time", "06:00") or "06:00"
        try:
            th, tm = [int(x) for x in stored_time.split(":")]
        except Exception:
            th, tm = 6, 0
        log_start = c3.time_input("Start time", value=dtime(th, tm),
                                  key=f"log_time_{sid}")

        v_row = venues[venues["venue"] == venue].iloc[0]
        st.caption(
            f"Primary venue base **{v_row['base_pts']} pts** · "
            f"Bonus species: **{v_row['bonus_species']}** (+50 first catch, +2 thereafter)."
        )

        partner_ids = [a for a in angler_ids if a != chosen["angler_id"]]
        partners = st.multiselect(
            "Partner(s) on the day", partner_ids,
            format_func=lambda a: lookup.get(a, a),
            help="Leave empty if fishing solo.",
            key=f"log_partners_{sid}",
        )
        if not partners:
            st.warning("⚠ **Solo session** — a **-100 point** penalty will apply.")
        else:
            st.success(
                f"👥 Fishing with {len(partners)} partner(s) — +5 each, "
                "+15 bonus per first-time pairing this league."
            )

        # ── 📸 Catch Card Submission ───────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 📸 Catch Card Submission")
        st.caption("Upload the catch card photo **or** paste a URL — at least one is required.")

        uploaded_file = st.file_uploader(
            "Upload catch card photo (jpg / jpeg / png, max 5 MB)",
            type=["jpg", "jpeg", "png"],
            key=f"log_upload_{sid}",
        )
        photo_url_input = st.text_input(
            "Photo URL (optional fallback)",
            placeholder="https://...",
            key=f"log_photo_url_{sid}",
        )

        # Live preview
        if uploaded_file is not None:
            st.image(uploaded_file, caption="Catch Card", width=420)
        elif photo_url_input.strip():
            st.image(photo_url_input.strip(), caption="Catch Card", width=420)

        # Late submission checkbox
        st.markdown("---")
        late_sub = st.checkbox(
            "⏰ Late card submission (photo metadata proof accepted — **50% of points only**)",
            key=f"log_late_{sid}",
        )
        if late_sub:
            st.warning("Late submission confirmed — **50%** of earned points will be allocated.")

        notes = st.text_area("Notes", height=80, key=f"log_notes_{sid}")

        # ── Catches table ──────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("**Catches**")
        st.caption(
            "Set per-catch **venue** if the angler fished more than one spot. "
            "Each unique venue fished adds its base pts. First bonus species per venue = +50; "
            "further bonus species catches at the same venue = +2."
        )

        species_opts = species_list if species_list else [""]
        blank = pd.DataFrame({
            "species":   [""],
            "length_cm": [""],
            "venue":     [venue],
            "notes":     [""],
        })
        new_catches = st.data_editor(
            blank, num_rows="dynamic", use_container_width=True,
            column_config={
                "species": st.column_config.SelectboxColumn(
                    "Species", options=species_opts,
                    help="Select from the species list.",
                ),
                "length_cm": st.column_config.TextColumn("Length (cm)"),
                "venue": st.column_config.SelectboxColumn(
                    "Venue", options=venues["venue"].tolist(),
                    help="Defaults to the session's primary venue.",
                ),
                "notes": st.column_config.TextColumn("Notes"),
            },
            key=f"log_catches_{sid}",
        )

        if st.button("💾 Save logged session", type="primary", key=f"log_save_{sid}"):
            # ── Validation ─────────────────────────────────────────────────────
            has_upload = uploaded_file is not None
            has_url    = bool(photo_url_input.strip())

            if not has_upload and not has_url:
                st.error("📸 A catch card photo or URL is required before saving.")
                st.stop()

            if has_upload and uploaded_file.size > MAX_UPLOAD_BYTES:
                st.error(
                    f"⚠️ File is {uploaded_file.size / 1_048_576:.1f} MB — "
                    "maximum allowed is 5 MB. Please compress or resize the image."
                )
                st.stop()

            # ── Resolve photo reference ────────────────────────────────────────
            if has_upload:
                photo_ref = _save_upload(uploaded_file)
                st.success(f"✅ Photo saved: `{Path(photo_ref).name}`")
            else:
                photo_ref = photo_url_input.strip()

            # ── Persist session ────────────────────────────────────────────────
            idx = sessions["session_id"] == sid
            sessions.loc[idx, "date"]            = date.isoformat() if date else ""
            sessions.loc[idx, "start_time"]      = log_start.strftime("%H:%M")
            sessions.loc[idx, "venue"]           = venue
            sessions.loc[idx, "partners"]        = ";".join(partners)
            sessions.loc[idx, "solo"]            = (len(partners) == 0)
            sessions.loc[idx, "late_submission"] = late_sub
            sessions.loc[idx, "photo"]           = photo_ref
            sessions.loc[idx, "notes"]           = notes.strip()
            sessions.loc[idx, "status"]          = STATUS_LOGGED
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
            late_note = " *(50% late penalty applied)*" if score["late"] else ""
            st.success(
                f"✓ **{sid}** logged — **{score['total_pts']} pts**{late_note} "
                f"({score['fish']} fish, {score['partners']} partner(s), "
                f"{score['new_pairs']} new pair(s), {score['bonus_venues']} bonus venue(s))"
            )
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 📋  ALL SESSIONS
# ─────────────────────────────────────────────────────────────────────────────
with tab_all:
    if sessions.empty:
        st.info("No sessions yet.")
    else:
        view = sessions.copy()
        view["angler"]         = view["angler_id"].map(lambda a: lookup.get(a, a))
        view["late"]           = view["late_submission"].map(
            lambda v: "⏰ Yes" if str(v).lower() in ["true", "1"] else "")
        st.dataframe(
            view[["session_id", "status", "round", "date", "start_time",
                  "angler", "venue", "partners", "late", "photo", "notes"]],
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.markdown("**Edit / delete catches**")
        edited = st.data_editor(
            catches, num_rows="dynamic", use_container_width=True,
            key="catches_editor",
        )
        if st.button("💾 Save catch edits"):
            save_catches(edited)
            st.success(f"Saved {len(edited)} catch rows.")
            st.rerun()
