"""Build XLSX + PDF reports with 4OAC branding."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from theme import find_logo, load_theme


def _hex(h: str):
    return colors.HexColor(h)


def _header(title: str, subtitle: str, theme: dict[str, str]) -> list:
    styles = getSampleStyleSheet()
    elements = []
    logo = find_logo()
    title_style = ParagraphStyle(
        "title", parent=styles["Title"],
        textColor=_hex(theme["page_heading"]),
        fontSize=22, leading=26, alignment=0, spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "sub", parent=styles["Normal"], fontSize=10,
        textColor=_hex(theme["section_heading"]), alignment=0,
    )

    if logo:
        try:
            from reportlab.lib.utils import ImageReader
            ir = ImageReader(str(logo))
            iw, ih = ir.getSize()
            target_h = 2.4 * cm
            img = Image(str(logo), width=target_h * iw / ih, height=target_h)
            inner = [[img,
                      Paragraph(f"<b>{title}</b><br/><font size=10 color='{theme['section_heading']}'>{subtitle}</font>",
                                title_style)]]
            t = Table(inner, colWidths=[3 * cm, None])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(t)
        except Exception:
            elements.append(Paragraph(title, title_style))
            elements.append(Paragraph(subtitle, sub_style))
    else:
        elements.append(Paragraph(title, title_style))
        elements.append(Paragraph(subtitle, sub_style))

    elements.append(Spacer(1, 0.3 * cm))
    rule = Table([[" "]], colWidths=[None], rowHeights=[2])
    rule.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), _hex(theme["sidebar_heading"]))]))
    elements.append(rule)
    elements.append(Spacer(1, 0.4 * cm))
    return elements


def _table_style(theme: dict[str, str], highlight_first_row: bool = False) -> TableStyle:
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), _hex(theme["sidebar_bg"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), _hex(theme["sidebar_heading"])),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _hex(theme["main_bg"])]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if highlight_first_row:
        cmds.append(("BACKGROUND", (0, 1), (-1, 1), _hex(theme["leaderboard_highlight"])))
        cmds.append(("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"))
    return TableStyle(cmds)


# ---- Leaderboard ---------------------------------------------------------

def build_leaderboard_xlsx(lb_df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        (lb_df if not lb_df.empty else pd.DataFrame({"info": ["No data"]})
         ).to_excel(xl, sheet_name="Leaderboard", index=False)
    return buf.getvalue()


def build_leaderboard_pdf(lb_df: pd.DataFrame, theme: dict[str, str] | None = None) -> bytes:
    theme = theme or load_theme()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    elements = _header("Leaderboard",
                       f"4OAC Winter League · Generated {datetime.now():%Y-%m-%d %H:%M}",
                       theme)
    if lb_df.empty:
        elements.append(Paragraph("No sessions logged yet.", getSampleStyleSheet()["Normal"]))
    else:
        data = [list(lb_df.columns)] + lb_df.astype(str).values.tolist()
        tbl = Table(data, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(_table_style(theme, highlight_first_row=True))
        elements.append(tbl)
    doc.build(elements)
    return buf.getvalue()


# ---- Fish detail (per venue) --------------------------------------------

def build_fish_detail_xlsx(fish_df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xl:
        if fish_df.empty:
            pd.DataFrame({"info": ["No catches yet"]}).to_excel(xl, sheet_name="Summary", index=False)
        else:
            # Summary
            summary = (fish_df.groupby("venue")
                       .agg(catches=("species", "count"),
                            unique_species=("species", "nunique"),
                            anglers=("angler", "nunique"))
                       .reset_index())
            summary.to_excel(xl, sheet_name="Summary", index=False)
            # All catches
            fish_df.to_excel(xl, sheet_name="All catches", index=False)
            # One sheet per venue
            for venue, sub in fish_df.groupby("venue"):
                safe = (venue or "Unknown")[:31].replace("/", "-").replace("\\", "-")
                sub.to_excel(xl, sheet_name=safe, index=False)
    return buf.getvalue()


def build_fish_detail_pdf(fish_df: pd.DataFrame, theme: dict[str, str] | None = None) -> bytes:
    theme = theme or load_theme()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                            leftMargin=1.2 * cm, rightMargin=1.2 * cm,
                            topMargin=1.0 * cm, bottomMargin=1.0 * cm)
    styles = getSampleStyleSheet()
    elements = _header("Details of Fish Caught — by Venue",
                       f"4OAC Winter League · Generated {datetime.now():%Y-%m-%d %H:%M}",
                       theme)

    if fish_df.empty:
        elements.append(Paragraph("No catches yet.", styles["Normal"]))
        doc.build(elements)
        return buf.getvalue()

    # Summary block
    summary = (fish_df.groupby("venue")
               .agg(catches=("species", "count"),
                    unique_species=("species", "nunique"),
                    anglers=("angler", "nunique"))
               .reset_index()
               .rename(columns={"venue": "Venue", "catches": "Catches",
                                "unique_species": "Species",
                                "anglers": "Anglers"}))
    elements.append(Paragraph("<b>Summary</b>", styles["Heading3"]))
    sum_tbl = Table([list(summary.columns)] + summary.astype(str).values.tolist(),
                    repeatRows=1, hAlign="LEFT")
    sum_tbl.setStyle(_table_style(theme))
    elements.append(sum_tbl)
    elements.append(Spacer(1, 0.4 * cm))

    cols = ["session_id", "date", "angler", "species", "length_cm", "notes"]
    cols_show = [c for c in cols if c in fish_df.columns]
    headers_pretty = {"session_id": "Session", "date": "Date",
                      "angler": "Angler", "species": "Species",
                      "length_cm": "Length (cm)", "notes": "Notes"}

    for venue, sub in fish_df.sort_values(["venue", "date"]).groupby("venue"):
        elements.append(PageBreak())
        elements.append(Paragraph(f"<b>{venue}</b>", styles["Heading2"]))
        elements.append(Paragraph(f"{len(sub)} catch(es)", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * cm))
        sub_view = sub[cols_show].rename(columns=headers_pretty).fillna("")
        data = [list(sub_view.columns)] + sub_view.astype(str).values.tolist()
        tbl = Table(data, repeatRows=1, hAlign="LEFT")
        tbl.setStyle(_table_style(theme))
        elements.append(tbl)

    doc.build(elements)
    return buf.getvalue()


# ---- Helpers -------------------------------------------------------------

def fish_detail_dataframe(catches: pd.DataFrame, sessions: pd.DataFrame,
                          anglers: pd.DataFrame) -> pd.DataFrame:
    """Catches enriched with session date/venue/angler — venue falls back to session venue."""
    if catches.empty:
        return pd.DataFrame(columns=["session_id", "date", "angler", "venue",
                                     "species", "length_cm", "notes"])
    sess_lite = sessions[["session_id", "date", "angler_id", "venue"]].rename(
        columns={"venue": "session_venue"})
    df = catches.merge(sess_lite, on="session_id", how="left")
    df["venue"] = df["venue"].astype(str).str.strip().replace("", pd.NA).fillna(df["session_venue"])
    name_map = {r["angler_id"]: f"{r['first_name']} {r['surname']}".strip()
                for _, r in anglers.iterrows()}
    df["angler"] = df["angler_id"].map(lambda a: name_map.get(a, a))
    df = df[["session_id", "date", "angler", "venue", "species", "length_cm", "notes"]]
    return df.sort_values(["venue", "date"]).reset_index(drop=True)
