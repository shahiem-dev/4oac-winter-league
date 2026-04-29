"""Shared helpers, scoring engine, and CSV IO for the 4OAC Winter League app."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

ANGLERS_CSV = DATA / "anglers.csv"
VENUES_CSV = DATA / "venues.csv"
SESSIONS_CSV = DATA / "sessions.csv"
CATCHES_CSV = DATA / "catches.csv"

ROUNDS = [1, 2, 3, 4]
ROUND_MONTHS = {1: "May 2026", 2: "June 2026", 3: "July 2026", 4: "August 2026"}

# Scoring constants
PTS_PER_FISH = 2
BONUS_SPECIES_PTS = 50
PARTNER_PTS = 5
NEW_PAIR_PTS = 5
BLANK_SESSION_PTS = 5
SOLO_PENALTY = -10

ANGLER_COLS = ["angler_id", "first_name", "surname", "initials", "club"]
VENUE_COLS = ["venue", "base_pts", "bonus_species"]
SESSION_COLS = ["session_id", "round", "date", "angler_id", "venue",
                "partners", "solo", "photo_url", "notes"]
CATCH_COLS = ["session_id", "species", "length_cm", "notes"]


# ---- Data IO -------------------------------------------------------------

def _read(path: Path, cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_csv(path, dtype=str).fillna("")
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols]


def load_anglers() -> pd.DataFrame:
    return _read(ANGLERS_CSV, ANGLER_COLS)


def save_anglers(df: pd.DataFrame) -> None:
    df = df.copy()
    df["angler_id"] = df.apply(
        lambda r: r["angler_id"] or _make_angler_id(r["first_name"], r["surname"]),
        axis=1,
    )
    df["initials"] = df.apply(
        lambda r: r["initials"] or _make_initials(r["first_name"], r["surname"]),
        axis=1,
    )
    df[ANGLER_COLS].to_csv(ANGLERS_CSV, index=False)


def load_venues() -> pd.DataFrame:
    df = _read(VENUES_CSV, VENUE_COLS)
    df["base_pts"] = pd.to_numeric(df["base_pts"], errors="coerce").fillna(0).astype(int)
    return df


def load_sessions() -> pd.DataFrame:
    df = _read(SESSIONS_CSV, SESSION_COLS)
    df["round"] = pd.to_numeric(df["round"], errors="coerce").fillna(0).astype(int)
    df["solo"] = df["solo"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    return df


def save_sessions(df: pd.DataFrame) -> None:
    df = df.copy()
    df["solo"] = df["solo"].apply(lambda v: "true" if bool(v) else "false")
    df[SESSION_COLS].to_csv(SESSIONS_CSV, index=False)


def load_catches() -> pd.DataFrame:
    return _read(CATCHES_CSV, CATCH_COLS)


def save_catches(df: pd.DataFrame) -> None:
    df[CATCH_COLS].to_csv(CATCHES_CSV, index=False)


# ---- Identity helpers ----------------------------------------------------

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").strip().lower()).strip("_")


def _make_angler_id(first: str, surname: str) -> str:
    return _slug(f"{first}_{surname}") or _slug(first) or _slug(surname)


def _make_initials(first: str, surname: str) -> str:
    f = (first or "").strip()
    s = (surname or "").strip()
    return ((f[:1] + s[:1]) or "X").upper()


def angler_label(row: pd.Series) -> str:
    nm = f"{row.get('first_name', '')} {row.get('surname', '')}".strip()
    return f"{nm} ({row['angler_id']})" if nm else row["angler_id"]


def angler_lookup(anglers: pd.DataFrame) -> dict[str, str]:
    return {r["angler_id"]: f"{r['first_name']} {r['surname']}".strip()
            for _, r in anglers.iterrows()}


def parse_partners(s: str) -> list[str]:
    if not s:
        return []
    return [p.strip() for p in str(s).split(";") if p.strip()]


# ---- Session code -------------------------------------------------------

def make_session_code(round_no: int, initials: str, sessions: pd.DataFrame) -> str:
    initials = (initials or "XX").upper()
    used = sessions[sessions["session_id"].str.startswith(
        f"WL-R{round_no}-{initials}-", na=False)]
    n = len(used) + 1
    while True:
        code = f"WL-R{round_no}-{initials}-{n:03d}"
        if code not in sessions["session_id"].values:
            return code
        n += 1


# ---- Scoring engine -----------------------------------------------------

def score_session(session: pd.Series,
                  catches: pd.DataFrame,
                  sessions: pd.DataFrame,
                  venues: pd.DataFrame) -> dict:
    """Return a breakdown dict for a single session row."""
    venue_row = venues[venues["venue"] == session["venue"]]
    base = int(venue_row.iloc[0]["base_pts"]) if len(venue_row) else 0
    bonus_species = venue_row.iloc[0]["bonus_species"] if len(venue_row) else ""

    sess_catches = catches[catches["session_id"] == session["session_id"]]
    n_fish = len(sess_catches)
    fish_pts = PTS_PER_FISH * n_fish

    bonus_caught = (
        bool(bonus_species)
        and (sess_catches["species"].str.strip().str.lower()
             == bonus_species.strip().lower()).any()
    )
    bonus_pts = BONUS_SPECIES_PTS if bonus_caught else 0

    partners = parse_partners(session.get("partners", ""))
    n_partners = len(partners)
    partner_pts = PARTNER_PTS * n_partners

    n_new = _count_new_pairs(session, partners, sessions)
    new_pair_pts = NEW_PAIR_PTS * n_new

    blank_pts = BLANK_SESSION_PTS if n_fish == 0 else 0
    solo = bool(session.get("solo", False)) or n_partners == 0
    solo_pts = SOLO_PENALTY if (solo and n_partners == 0) else 0

    total = base + fish_pts + bonus_pts + partner_pts + new_pair_pts + blank_pts + solo_pts
    return {
        "session_id": session["session_id"],
        "angler_id": session["angler_id"],
        "round": int(session.get("round", 0) or 0),
        "date": session.get("date", ""),
        "venue": session.get("venue", ""),
        "fish": n_fish,
        "bonus_caught": bonus_caught,
        "partners": n_partners,
        "new_pairs": n_new,
        "blank": n_fish == 0,
        "solo": solo and n_partners == 0,
        "base_pts": base,
        "fish_pts": fish_pts,
        "bonus_pts": bonus_pts,
        "partner_pts": partner_pts,
        "new_pair_pts": new_pair_pts,
        "blank_pts": blank_pts,
        "solo_pts": solo_pts,
        "total_pts": total,
    }


def _count_new_pairs(session: pd.Series, partners: list[str],
                     sessions: pd.DataFrame) -> int:
    """How many of `partners` is the focal angler pairing with for the first time."""
    if not partners:
        return 0
    focal = session["angler_id"]
    sid = session["session_id"]
    # All this angler's prior sessions (by date, then by session_id as tiebreaker)
    prior = sessions[(sessions["angler_id"] == focal) & (sessions["session_id"] != sid)]
    prior_dates = prior[prior["date"] < session.get("date", "")]
    seen = set()
    for _, r in prior_dates.iterrows():
        seen.update(parse_partners(r.get("partners", "")))
    return sum(1 for p in partners if p not in seen)


def score_all(sessions: pd.DataFrame | None = None,
              catches: pd.DataFrame | None = None,
              venues: pd.DataFrame | None = None) -> pd.DataFrame:
    sessions = sessions if sessions is not None else load_sessions()
    catches = catches if catches is not None else load_catches()
    venues = venues if venues is not None else load_venues()
    if sessions.empty:
        return pd.DataFrame()
    rows = [score_session(r, catches, sessions, venues)
            for _, r in sessions.sort_values("date").iterrows()]
    return pd.DataFrame(rows)


def leaderboard(scored: pd.DataFrame, anglers: pd.DataFrame) -> pd.DataFrame:
    if scored.empty:
        return pd.DataFrame(columns=["rank", "angler", "sessions", "fish", "points"])
    agg = (scored.groupby("angler_id")
           .agg(sessions=("session_id", "count"),
                fish=("fish", "sum"),
                points=("total_pts", "sum"))
           .reset_index())
    lookup = angler_lookup(anglers)
    agg["angler"] = agg["angler_id"].map(lambda a: lookup.get(a, a))
    agg = agg.sort_values("points", ascending=False).reset_index(drop=True)
    agg.insert(0, "rank", agg.index + 1)
    return agg[["rank", "angler", "sessions", "fish", "points"]]


# ---- Streamlit helpers --------------------------------------------------

def page_header(title: str, icon: str = "🎣") -> None:
    from theme import inject_css, render_sidebar_logo
    st.set_page_config(page_title=f"{title} · 4OAC Winter League",
                       page_icon=icon, layout="wide")
    inject_css()
    render_sidebar_logo()
    with st.sidebar:
        st.markdown("### 🎣 4OAC Winter League")
        st.caption("May–Aug 2026 · 4 rounds")
    st.title(f"{icon} {title}")
