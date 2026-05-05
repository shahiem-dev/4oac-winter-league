"""Shared helpers, scoring engine, and CSV IO for the 4OAC Winter League app."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UPLOADS_DIR = ROOT / "uploads"

ANGLERS_CSV  = DATA / "anglers.csv"
VENUES_CSV   = DATA / "venues.csv"
SESSIONS_CSV = DATA / "sessions.csv"
CATCHES_CSV  = DATA / "catches.csv"
SPECIES_CSV  = DATA / "species.csv"

ROUNDS = [1, 2, 3, 4]
ROUND_MONTHS = {1: "May 2026", 2: "June 2026", 3: "July 2026", 4: "August 2026"}
SESSIONS_PER_ROUND = 2

# ── Scoring constants ──────────────────────────────────────────────────────────
PTS_PER_FISH      = 2
BONUS_SPECIES_PTS = 50   # first bonus-species catch per venue per session
PARTNER_PTS       = 5
NEW_PAIR_PTS      = 15   # first time this league season
BLANK_SESSION_PTS = 5
SOLO_PENALTY      = -100

ANGLER_COLS = ["angler_id", "wp_no", "first_name", "surname", "initials", "club", "division"]
DIVISIONS   = {"G": "GrandMasters", "J": "Juniors", "K": "Kids",
               "L": "Ladies", "M": "Masters", "S": "Seniors"}
VENUE_COLS  = ["venue", "base_pts", "bonus_species"]
SESSION_COLS = [
    "session_id", "round", "date", "start_time", "angler_id", "venue",
    "partners", "solo", "late_submission", "photo", "notes", "status",
]
STATUS_ISSUED = "issued"
STATUS_LOGGED = "logged"
CATCH_COLS = ["session_id", "species", "length_cm", "venue", "notes"]


# ── Data IO ───────────────────────────────────────────────────────────────────

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
    if SESSIONS_CSV.exists():
        raw = pd.read_csv(SESSIONS_CSV, dtype=str).fillna("")
        # Backward-compat: rename legacy photo_url → photo
        if "photo_url" in raw.columns and "photo" not in raw.columns:
            raw = raw.rename(columns={"photo_url": "photo"})
        for c in SESSION_COLS:
            if c not in raw.columns:
                raw[c] = ""
        df = raw[SESSION_COLS]
    else:
        df = pd.DataFrame(columns=SESSION_COLS)
    df["round"] = pd.to_numeric(df["round"], errors="coerce").fillna(0).astype(int)
    df["solo"] = df["solo"].astype(str).str.lower().isin(["true", "1", "yes", "y"])
    df["late_submission"] = df["late_submission"].astype(str).str.lower().isin(
        ["true", "1", "yes", "y"])
    df["status"] = df["status"].fillna("").replace("", STATUS_LOGGED)
    return df


def save_sessions(df: pd.DataFrame) -> None:
    df = df.copy()
    df["solo"]           = df["solo"].apply(lambda v: "true" if bool(v) else "false")
    df["late_submission"] = df["late_submission"].apply(lambda v: "true" if bool(v) else "false")
    # Ensure all columns exist before writing
    for c in SESSION_COLS:
        if c not in df.columns:
            df[c] = ""
    df[SESSION_COLS].to_csv(SESSIONS_CSV, index=False)


def load_catches() -> pd.DataFrame:
    return _read(CATCHES_CSV, CATCH_COLS)


def save_catches(df: pd.DataFrame) -> None:
    df[CATCH_COLS].to_csv(CATCHES_CSV, index=False)


def load_species() -> list[str]:
    if not SPECIES_CSV.exists():
        return []
    df = pd.read_csv(SPECIES_CSV, dtype=str).fillna("")
    return sorted(df["common_name"].tolist())


# ── Identity helpers ──────────────────────────────────────────────────────────

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


# ── Session code ──────────────────────────────────────────────────────────────

def make_session_code(round_no: int, initials: str, start_time: str,
                      sessions: pd.DataFrame) -> str:
    """Generate WL-R{round}-{INITIALS}-{NNN}-{HHMM}."""
    initials  = (initials or "XX").upper()
    time_part = (start_time or "").replace(":", "").strip()[:4] or "0000"
    prefix    = f"WL-R{round_no}-{initials}-"
    used      = sessions[sessions["session_id"].str.startswith(prefix, na=False)]
    n = len(used) + 1
    while True:
        code = f"{prefix}{n:03d}-{time_part}"
        if code not in sessions["session_id"].values:
            return code
        n += 1


def issue_code(angler_id: str, round_no: int,
               planned_date: str = "", planned_venue: str = "",
               start_time: str = "") -> str:
    """Reserve a session code. Stub row written to sessions.csv."""
    anglers  = load_anglers()
    sessions = load_sessions()
    row = anglers[anglers["angler_id"] == angler_id]
    if row.empty:
        raise ValueError(f"Unknown angler: {angler_id}")
    initials = row.iloc[0]["initials"] or "XX"
    code = make_session_code(int(round_no), initials, start_time, sessions)
    new_row = pd.DataFrame([{
        "session_id":      code,
        "round":           int(round_no),
        "date":            planned_date,
        "start_time":      start_time,
        "angler_id":       angler_id,
        "venue":           planned_venue,
        "partners":        "",
        "solo":            False,
        "late_submission": False,
        "photo":           "",
        "notes":           "",
        "status":          STATUS_ISSUED,
    }])
    save_sessions(pd.concat([sessions, new_row], ignore_index=True))
    return code


# ── Scoring engine ────────────────────────────────────────────────────────────

def score_session(session: pd.Series,
                  catches: pd.DataFrame,
                  sessions: pd.DataFrame,
                  venues: pd.DataFrame) -> dict:
    """Return a scoring breakdown dict for a single session row.

    Venue rules:
      - Base pts = sum of base_pts for every unique venue fished this session.
      - Bonus species: FIRST qualifying catch per venue = +50.
        Additional qualifying catches at the same venue = +2 (same as any fish).
      - All fish (including bonus-species catches) earn +2 via fish_pts.
        The first bonus-species catch per venue earns an *extra* +48 on top of that
        (net +50 total), tracked separately as bonus_pts.

    Late submission: all earned points × 0.50.
    """
    sess_catches = catches[catches["session_id"] == session["session_id"]].copy()
    n_fish  = len(sess_catches)
    fish_pts = PTS_PER_FISH * n_fish   # +2 for every fish including bonus species

    # Resolve effective venue per catch
    sess_catches["venue_eff"] = (
        sess_catches.get("venue", "").astype(str).str.strip()
        .replace("", session.get("venue", ""))
    )
    venues_fished = (
        sess_catches["venue_eff"].dropna().replace("", pd.NA).dropna().unique().tolist()
        if n_fish
        else ([session["venue"]] if session.get("venue") else [])
    )

    venue_lookup = {r["venue"]: (int(r["base_pts"]), r["bonus_species"])
                    for _, r in venues.iterrows()}
    base = sum(venue_lookup.get(v, (0, ""))[0] for v in venues_fished)

    # Bonus species: +48 extra per first qualifying catch per venue
    # (the base +2 is already in fish_pts)
    bonus_venues_hit: set[str] = set()
    bonus_extra = 0
    bonus_count = 0
    if n_fish:
        for _, catch_row in sess_catches.iterrows():
            v  = catch_row["venue_eff"]
            sp = str(catch_row["species"]).strip().lower()
            bs = venue_lookup.get(v, (0, ""))[1]
            if bs and sp == bs.strip().lower():
                if v not in bonus_venues_hit:
                    bonus_venues_hit.add(v)
                    bonus_extra += (BONUS_SPECIES_PTS - PTS_PER_FISH)  # +48 on top of +2
                    bonus_count += 1
    bonus_pts = bonus_extra  # total extra on top of fish_pts for first bonus per venue

    partners    = parse_partners(session.get("partners", ""))
    n_partners  = len(partners)
    partner_pts = PARTNER_PTS * n_partners

    n_new        = _count_new_pairs(session, partners, sessions)
    new_pair_pts = NEW_PAIR_PTS * n_new

    blank_pts = BLANK_SESSION_PTS if n_fish == 0 else 0
    solo      = n_partners == 0
    solo_pts  = SOLO_PENALTY if solo else 0

    subtotal = base + fish_pts + bonus_pts + partner_pts + new_pair_pts + blank_pts + solo_pts

    # Late submission: 50 % of all points
    late = bool(session.get("late_submission", False))
    total = round(subtotal * 0.5) if late else subtotal

    return {
        "session_id":    session["session_id"],
        "angler_id":     session["angler_id"],
        "round":         int(session.get("round", 0) or 0),
        "date":          session.get("date", ""),
        "venues":        ", ".join(venues_fished),
        "fish":          n_fish,
        "bonus_venues":  bonus_count,
        "partners":      n_partners,
        "new_pairs":     n_new,
        "blank":         n_fish == 0,
        "solo":          solo,
        "late":          late,
        "base_pts":      base,
        "fish_pts":      fish_pts,
        "bonus_pts":     bonus_pts,
        "partner_pts":   partner_pts,
        "new_pair_pts":  new_pair_pts,
        "blank_pts":     blank_pts,
        "solo_pts":      solo_pts,
        "subtotal_pts":  subtotal,
        "total_pts":     total,
    }


def _count_new_pairs(session: pd.Series, partners: list[str],
                     sessions: pd.DataFrame) -> int:
    """How many partners is the focal angler pairing with for the first time."""
    if not partners:
        return 0
    focal = session["angler_id"]
    sid   = session["session_id"]
    prior = sessions[(sessions["angler_id"] == focal) & (sessions["session_id"] != sid)]
    prior_dates = prior[prior["date"] < session.get("date", "")]
    seen: set[str] = set()
    for _, r in prior_dates.iterrows():
        seen.update(parse_partners(r.get("partners", "")))
    return sum(1 for p in partners if p not in seen)


def score_all(sessions: pd.DataFrame | None = None,
              catches:  pd.DataFrame | None = None,
              venues:   pd.DataFrame | None = None) -> pd.DataFrame:
    sessions = sessions if sessions is not None else load_sessions()
    catches  = catches  if catches  is not None else load_catches()
    venues   = venues   if venues   is not None else load_venues()
    if sessions.empty:
        return pd.DataFrame()
    logged = sessions[sessions["status"] == STATUS_LOGGED]
    if logged.empty:
        return pd.DataFrame()
    rows = [score_session(r, catches, sessions, venues)
            for _, r in logged.sort_values("date").iterrows()]
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


# ── Streamlit helpers ─────────────────────────────────────────────────────────

def page_header(title: str, icon: str = "🎣", show_title: bool = True) -> None:
    from theme import inject_css, render_sidebar_logo
    st.set_page_config(page_title=f"{title} · 4OAC Winter League",
                       page_icon=icon, layout="wide")
    inject_css()
    render_sidebar_logo()
    with st.sidebar:
        st.markdown("### 🎣 4OAC Winter League")
        st.caption("May–Aug 2026 · 4 rounds")
    if show_title:
        st.title(f"{icon} {title}")
