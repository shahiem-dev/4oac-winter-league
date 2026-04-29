"""Admin — theme & branding controls."""
from __future__ import annotations

import streamlit as st

from app_lib import page_header
from theme import (DEFAULT_THEME, LOGO_PATH, PALETTE_LABELS, find_logo,
                   get_logo_bytes, load_theme, reset_theme, save_logo,
                   save_theme)

page_header("Admin", icon="🛠")

tab_theme, tab_logo = st.tabs(["🎨 Theme & Branding", "🖼 Logo"])

# ---- Theme tab ----------------------------------------------------------
with tab_theme:
    st.caption("Pick colours for each part of the app. Changes save to `data/theme.json` "
               "and apply on next page render.")
    theme = load_theme()

    st.markdown("### Colour palette")
    grid = list(PALETTE_LABELS.items())
    new_theme: dict[str, str] = {}
    cols_per_row = 2
    for i in range(0, len(grid), cols_per_row):
        row = st.columns(cols_per_row)
        for j, (key, label) in enumerate(grid[i:i + cols_per_row]):
            with row[j]:
                new_theme[key] = st.color_picker(
                    label, value=theme.get(key, DEFAULT_THEME[key]),
                    key=f"clr_{key}",
                )

    st.divider()

    # ---- Live preview ---------------------------------------------------
    st.markdown("### Live preview")
    t = new_theme
    preview_html = f"""
    <div style="border-radius:10px;overflow:hidden;border:1px solid #ddd;
                background:{t['main_bg']};color:{t['body_text']};
                font-family:-apple-system,Segoe UI,Roboto,sans-serif;">
      <div style="display:flex;">
        <div style="background:{t['sidebar_bg']};color:{t['sidebar_item']};
                    width:160px;padding:16px;">
          <div style="color:{t['sidebar_heading']};font-weight:700;
                      margin-bottom:8px;">Sidebar</div>
          <div style="padding:6px 8px;border-radius:6px;margin-bottom:4px;">Home</div>
          <div style="padding:6px 8px;border-radius:6px;margin-bottom:4px;
                      background:{t['sidebar_active_bg']};color:{t['sidebar_active']};
                      font-weight:600;">Sessions (active)</div>
          <div style="padding:6px 8px;border-radius:6px;">Leaderboard</div>
        </div>
        <div style="flex:1;padding:18px;">
          <h2 style="color:{t['page_heading']};margin:0 0 8px;">Page Heading</h2>
          <h4 style="color:{t['section_heading']};margin:8px 0;">Section Heading</h4>
          <div style="font-size:28px;font-weight:700;color:{t['metric_text']};
                      margin:8px 0;">126 pts</div>
          <button style="background:{t['button_bg']};color:{t['button_text']};
                         border:0;border-radius:6px;padding:8px 14px;
                         font-weight:600;">Primary button</button>
          <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;">
            <div style="background:{t['info_bg']};padding:8px 12px;border-radius:6px;">ℹ Info</div>
            <div style="background:{t['success_bg']};padding:8px 12px;border-radius:6px;">✓ Success</div>
            <div style="background:{t['warning_bg']};padding:8px 12px;border-radius:6px;">⚠ Warning</div>
            <div style="background:{t['error_bg']};padding:8px 12px;border-radius:6px;">✗ Error</div>
          </div>
          <table style="margin-top:14px;border-collapse:collapse;width:100%;
                        background:white;font-size:13px;">
            <thead><tr style="background:#eee;">
              <th style="padding:6px 10px;text-align:left;">Rank</th>
              <th style="padding:6px 10px;text-align:left;">Angler</th>
              <th style="padding:6px 10px;text-align:left;">Points</th>
            </tr></thead>
            <tbody>
              <tr style="background:{t['leaderboard_highlight']};font-weight:600;">
                <td style="padding:6px 10px;">1</td>
                <td style="padding:6px 10px;">Top angler</td>
                <td style="padding:6px 10px;">412</td>
              </tr>
              <tr><td style="padding:6px 10px;">2</td>
                  <td style="padding:6px 10px;">Runner up</td>
                  <td style="padding:6px 10px;">388</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)

    st.divider()

    bcol1, bcol2, _ = st.columns([1, 1, 4])
    if bcol1.button("💾 Save Theme", type="primary"):
        save_theme(new_theme)
        st.success("Theme saved. Reload any page to see it applied.")
        st.rerun()
    if bcol2.button("↺ Reset to Default 4OAC Theme"):
        reset_theme()
        st.success("Theme reset to defaults.")
        st.rerun()

# ---- Logo tab -----------------------------------------------------------
with tab_logo:
    st.caption(f"Logo file lives at `assets/4oac_logo.<ext>` "
               "(png, jpg, jpeg, or webp). Replace by uploading below.")

    img = get_logo_bytes()
    if img:
        st.image(img, width=240, caption=str(find_logo().relative_to(find_logo().parent.parent)))
    else:
        st.info("No logo uploaded yet — upload one below or drop a file at "
                f"`{LOGO_PATH.relative_to(LOGO_PATH.parent.parent)}`.")

    up = st.file_uploader("Upload / replace logo",
                          type=["png", "jpg", "jpeg", "webp"])
    if up is not None and st.button("💾 Save logo", type="primary"):
        out = save_logo(up)
        st.success(f"Saved logo to `{out.relative_to(out.parent.parent)}`.")
        st.rerun()
