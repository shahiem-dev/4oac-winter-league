"""Theme + branding: logo storage, colour palette, CSS injection."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
DATA = ROOT / "data"
THEME_JSON = DATA / "theme.json"
LOGO_PATH = ASSETS / "4oac_logo.png"
LOGO_EXTS = (".png", ".jpg", ".jpeg", ".webp")

# Strong 4OAC default — deep ocean blue, white, gold accents, charcoal, light grey
DEFAULT_THEME: dict[str, str] = {
    "main_bg":            "#F5F7FA",  # light grey background
    "sidebar_bg":         "#0B2545",  # deep ocean blue
    "sidebar_heading":    "#FFD60A",  # gold
    "sidebar_item":       "#E5ECF4",  # near-white
    "sidebar_active":     "#FFD60A",  # gold highlight
    "sidebar_active_bg":  "#13315C",
    "page_heading":       "#0B2545",
    "section_heading":    "#13315C",
    "button_bg":          "#0B2545",
    "button_text":        "#FFFFFF",
    "info_bg":            "#E0ECFA",
    "success_bg":         "#DEF7E5",
    "warning_bg":         "#FFF4D6",
    "error_bg":           "#FCE4E4",
    "metric_text":        "#0B2545",
    "leaderboard_highlight": "#FFF4D6",
    "body_text":          "#1F2937",  # dark charcoal
}

PALETTE_LABELS: dict[str, str] = {
    "main_bg": "Main background",
    "sidebar_bg": "Sidebar background",
    "sidebar_heading": "Sidebar headings",
    "sidebar_item": "Sidebar menu items",
    "sidebar_active": "Sidebar active item (text)",
    "sidebar_active_bg": "Sidebar active item (background)",
    "page_heading": "Page headings",
    "section_heading": "Section headings",
    "button_bg": "Buttons (background)",
    "button_text": "Buttons (text)",
    "info_bg": "Info card",
    "success_bg": "Success card",
    "warning_bg": "Warning card",
    "error_bg": "Error card",
    "metric_text": "Metric value text",
    "leaderboard_highlight": "Leaderboard highlight row",
    "body_text": "Body text",
}


# ---- Theme storage ------------------------------------------------------

def load_theme() -> dict[str, str]:
    if THEME_JSON.exists():
        try:
            saved = json.loads(THEME_JSON.read_text(encoding="utf-8"))
            return {**DEFAULT_THEME, **{k: v for k, v in saved.items() if k in DEFAULT_THEME}}
        except json.JSONDecodeError:
            pass
    return dict(DEFAULT_THEME)


def save_theme(theme: dict[str, str]) -> None:
    THEME_JSON.parent.mkdir(parents=True, exist_ok=True)
    clean = {k: theme.get(k, DEFAULT_THEME[k]) for k in DEFAULT_THEME}
    THEME_JSON.write_text(json.dumps(clean, indent=2), encoding="utf-8")


def reset_theme() -> dict[str, str]:
    save_theme(DEFAULT_THEME)
    return dict(DEFAULT_THEME)


# ---- Logo ---------------------------------------------------------------

def find_logo() -> Path | None:
    for ext in LOGO_EXTS:
        p = ASSETS / f"4oac_logo{ext}"
        if p.exists():
            return p
    return None


def get_logo_bytes() -> bytes | None:
    p = find_logo()
    return p.read_bytes() if p else None


def save_logo(uploaded_file) -> Path:
    ASSETS.mkdir(parents=True, exist_ok=True)
    # remove existing logo of any extension first
    for ext in LOGO_EXTS:
        old = ASSETS / f"4oac_logo{ext}"
        if old.exists():
            old.unlink()
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in LOGO_EXTS:
        suffix = ".png"
    out = ASSETS / f"4oac_logo{suffix}"
    out.write_bytes(uploaded_file.getbuffer())
    return out


# ---- CSS injection ------------------------------------------------------

def _css(theme: dict[str, str]) -> str:
    t = theme
    return f"""
    <style>
    .stApp {{
        background-color: {t['main_bg']};
        color: {t['body_text']};
    }}
    [data-testid="stSidebar"] {{
        background-color: {t['sidebar_bg']};
    }}
    [data-testid="stSidebar"] * {{
        color: {t['sidebar_item']};
    }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {{
        color: {t['sidebar_heading']} !important;
    }}
    [data-testid="stSidebarNav"] a {{
        color: {t['sidebar_item']} !important;
        border-radius: 6px;
        padding: 4px 8px;
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"],
    [data-testid="stSidebarNav"] a:hover {{
        background-color: {t['sidebar_active_bg']} !important;
        color: {t['sidebar_active']} !important;
    }}
    h1 {{ color: {t['page_heading']}; }}
    h2, h3 {{ color: {t['section_heading']}; }}
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
        background-color: {t['button_bg']};
        color: {t['button_text']};
        border: 0;
        border-radius: 6px;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {{
        filter: brightness(1.1);
        color: {t['button_text']};
    }}
    [data-testid="stMetricValue"] {{ color: {t['metric_text']}; }}
    [data-testid="stAlert"][data-baseweb="notification"] {{ border-radius: 6px; }}
    div[data-baseweb="notification"][kind="info"]    {{ background-color: {t['info_bg']}; }}
    div[data-baseweb="notification"][kind="success"] {{ background-color: {t['success_bg']}; }}
    div[data-baseweb="notification"][kind="warning"] {{ background-color: {t['warning_bg']}; }}
    div[data-baseweb="notification"][kind="error"]   {{ background-color: {t['error_bg']}; }}
    .leaderboard-highlight {{
        background-color: {t['leaderboard_highlight']} !important;
        font-weight: 600;
    }}
    </style>
    """


def inject_css(theme: dict[str, str] | None = None) -> None:
    theme = theme or load_theme()
    st.markdown(_css(theme), unsafe_allow_html=True)


# ---- Sidebar branding ---------------------------------------------------

def render_sidebar_logo(width: int = 120) -> None:
    img = get_logo_bytes()
    with st.sidebar:
        if img:
            st.image(img, width=width)
        else:
            st.markdown(
                "<div style='padding:16px;border:1px dashed #888;text-align:center;"
                "border-radius:8px;font-size:13px;'>4OAC<br>logo</div>",
                unsafe_allow_html=True,
            )


def render_home_logo(width: int = 220) -> None:
    img = get_logo_bytes()
    if img:
        st.image(img, width=width)
