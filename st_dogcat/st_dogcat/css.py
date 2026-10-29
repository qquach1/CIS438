# ─────────────────────────────────────────────
# THEME DEFINITIONS
# ─────────────────────────────────────────────
# Color tokens for consistent styling: use T['primary'], T['amber'], etc. in charts.
# Each theme is a dictionary mapping color names to hex codes used throughout the UI.
THEMES = {
    "dark": dict(
        bg="#0b0f19", card="#111827", card_hover="#1a2235", surface="#161e2e",
        border="rgba(56,189,248,0.08)", border_glow="rgba(56,189,248,0.25)",
        primary="#38bdf8", primary_dim="rgba(56,189,248,0.6)",
        amber="#fbbf24", emerald="#34d399", rose="#fb7185", violet="#a78bfa",
        slate="#94a3b8", text="#f1f5f9", muted="#64748b",
        grid="rgba(148,163,184,0.06)", line="rgba(148,163,184,0.1)",
        sidebar_bg="linear-gradient(180deg, #0d1321 0%, #111827 100%)",
        hero_bg="linear-gradient(135deg, #0d1321 0%, #111827 40%, #0f1b2d 100%)",
        hero_orb1="rgba(56,189,248,0.06)", hero_orb2="rgba(251,191,36,0.04)",
        card_shadow="rgba(56,189,248,0.08)", tab_active_shadow="rgba(56,189,248,0.08)",
        insight_bg_alpha="0.04", insight_bg_alpha2="0.01", insight_border_alpha="0.1",
        pie_line="#0b0f19", bar_text="#f1f5f9", bar_text_alt="#94a3b8",
        heatmap_scale=["#0b0f19", "#1e3a5f", "#38bdf8", "#e0f2fe"],
        matrix_scale=["#0b0f19", "#1e1b4b", "#a78bfa", "#e9d5ff"],
        footer_color="rgba(148,163,184,0.35)",
        stat_border="rgba(148,163,184,0.06)",
    ),
    "light": dict(
        bg="#f8fafc", card="#ffffff", card_hover="#f1f5f9", surface="#eef2f7",
        border="rgba(15,23,42,0.08)", border_glow="rgba(14,116,144,0.2)",
        primary="#0891b2", primary_dim="rgba(8,145,178,0.6)",
        amber="#d97706", emerald="#059669", rose="#e11d48", violet="#7c3aed",
        slate="#475569", text="#0f172a", muted="#64748b",
        grid="rgba(15,23,42,0.05)", line="rgba(15,23,42,0.08)",
        sidebar_bg="linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%)",
        hero_bg="linear-gradient(135deg, #f0fdfa 0%, #ecfeff 40%, #f0f9ff 100%)",
        hero_orb1="rgba(8,145,178,0.06)", hero_orb2="rgba(217,119,6,0.04)",
        card_shadow="rgba(0,0,0,0.06)", tab_active_shadow="rgba(14,116,144,0.1)",
        insight_bg_alpha="0.06", insight_bg_alpha2="0.02", insight_border_alpha="0.15",
        pie_line="#ffffff", bar_text="#0f172a", bar_text_alt="#475569",
        heatmap_scale=["#f0fdfa", "#99f6e4", "#0891b2", "#164e63"],
        matrix_scale=["#faf5ff", "#ddd6fe", "#7c3aed", "#4c1d95"],
        footer_color="rgba(71,85,105,0.4)",
        stat_border="rgba(15,23,42,0.06)",
    ),
}



# ─────────────────────────────────────────────
# COLOR UTILITIES
# ─────────────────────────────────────────────
# Helper functions to convert and manipulate colors for chart styling.

def _rgb(hex_color):
    """Convert #hex to r,g,b string for use in rgba()."""
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


# ─────────────────────────────────────────────
# DYNAMIC CSS
# ─────────────────────────────────────────────
# Generates the visual styling (colors, fonts, spacing, shadows) that makes the dashboard
# look professional. This CSS is injected into the page to customize Streamlit's defaults.

def build_css(t, dark):
    glow_shadow = f"0 0 8px {t['border_glow']}" if dark else "none"
    card_hover_shadow = f"0 8px 30px {t['card_shadow']}" if dark else f"0 4px 20px {t['card_shadow']}"

    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,300&family=Playfair+Display:wght@600;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root {{
    --bg: {t['bg']}; --card: {t['card']}; --card-hover: {t['card_hover']};
    --surface: {t['surface']}; --primary: {t['primary']}; --border: {t['border']};
    --border-glow: {t['border_glow']}; --amber: {t['amber']}; --emerald: {t['emerald']};
    --rose: {t['rose']}; --violet: {t['violet']}; --slate: {t['slate']};
    --text: {t['text']}; --muted: {t['muted']};
    --font-body: 'DM Sans', sans-serif;
    --font-display: 'Playfair Display', serif;
    --font-mono: 'JetBrains Mono', monospace;
}}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main, .block-container {{
    background-color: var(--bg) !important;
    color: var(--slate) !important;
    font-family: var(--font-body) !important;
}}

#MainMenu, footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 1400px !important; }}
div[data-testid="stMetric"] {{ display: none; }}

/* SIDEBAR */
section[data-testid="stSidebar"] {{
    background: {t['sidebar_bg']} !important;
    border-right: 1px solid var(--border) !important;
}}
section[data-testid="stSidebar"] * {{
    color: var(--slate) !important;
}}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stDateInput label {{
    color: var(--text) !important; font-weight: 500 !important;
    font-size: 0.85rem !important; letter-spacing: 0.02em;
}}
section[data-testid="stSidebar"] hr {{ border-color: var(--border) !important; }}


/* HERO */
.hero {{
    position: relative; overflow: hidden;
    background: {t['hero_bg']};
    border: 1px solid var(--border); border-radius: 20px;
    padding: 2.5rem 3rem; margin-bottom: 2rem;
}}
.hero::before {{
    content: ''; position: absolute; top: -50%; right: -20%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, {t['hero_orb1']} 0%, transparent 70%);
    pointer-events: none;
}}
.hero::after {{
    content: ''; position: absolute; bottom: -30%; left: 10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, {t['hero_orb2']} 0%, transparent 70%);
    pointer-events: none;
}}
.hero-eyebrow {{
    font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.25em;
    text-transform: uppercase; color: var(--primary); margin-bottom: 0.6rem; opacity: 0.9;
}}
.hero h1 {{
    font-family: var(--font-display); font-size: 2.6rem; font-weight: 800;
    color: var(--text); margin: 0; line-height: 1.15; letter-spacing: -0.01em;
}}
.hero h1 span {{ color: var(--primary); }}
.hero-sub {{ font-size: 1rem; color: var(--slate); margin-top: 0.5rem; max-width: 600px; line-height: 1.6; }}

/* METRIC CARDS */
.metric-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 2rem; }}
@media (max-width: 900px) {{ .metric-grid {{ grid-template-columns: repeat(3, 1fr); }} }}
.m-card {{
    background: var(--card); border: 1px solid var(--border); border-radius: 16px;
    padding: 1.4rem 1rem; text-align: center; position: relative;
    overflow: hidden; transition: all 0.25s ease;
    {"" if dark else "box-shadow: 0 1px 4px rgba(0,0,0,0.04);"}
}}
.m-card:hover {{
    border-color: var(--border-glow); background: var(--card-hover);
    transform: translateY(-3px); box-shadow: {card_hover_shadow};
}}
.m-card::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; border-radius: 16px 16px 0 0;
}}
.m-card:nth-child(1)::before {{ background: var(--primary); }}
.m-card:nth-child(2)::before {{ background: var(--emerald); }}
.m-card:nth-child(3)::before {{ background: var(--violet); }}
.m-card:nth-child(4)::before {{ background: var(--amber); }}
.m-card:nth-child(5)::before {{ background: var(--rose); }}
.m-card:nth-child(6)::before {{ background: var(--slate); }}
.m-icon {{ font-size: 1.4rem; margin-bottom: 0.3rem; }}
.m-val {{
    font-family: var(--font-mono); font-size: 1.7rem; font-weight: 600;
    color: var(--text); letter-spacing: -0.02em;
}}
.m-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--slate); margin-top: 0.35rem; font-weight: 500;
}}

/* SECTION HEADERS */
.sec-head {{ display: flex; align-items: center; gap: 10px; margin: 2.2rem 0 0.8rem 0; }}
.sec-dot {{
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--primary); box-shadow: {glow_shadow}; flex-shrink: 0;
}}
.sec-dot.amber {{ background: var(--amber); {"box-shadow: 0 0 8px rgba(251,191,36,0.35);" if dark else ""} }}
.sec-dot.emerald {{ background: var(--emerald); {"box-shadow: 0 0 8px rgba(52,211,153,0.35);" if dark else ""} }}
.sec-dot.rose {{ background: var(--rose); {"box-shadow: 0 0 8px rgba(251,113,133,0.35);" if dark else ""} }}
.sec-dot.violet {{ background: var(--violet); {"box-shadow: 0 0 8px rgba(167,139,250,0.35);" if dark else ""} }}
.sec-title {{
    font-family: var(--font-display); font-size: 1.35rem; font-weight: 600;
    color: var(--text); letter-spacing: -0.01em;
}}

/* INSIGHT CALLOUT */
.insight {{
    background: linear-gradient(135deg, rgba({_rgb(t['primary'])},{t['insight_bg_alpha']}), rgba({_rgb(t['primary'])},{t['insight_bg_alpha2']}));
    border: 1px solid rgba({_rgb(t['primary'])},{t['insight_border_alpha']});
    border-left: 3px solid var(--primary); border-radius: 0 12px 12px 0;
    padding: 1rem 1.4rem; margin: 0.3rem 0 1.2rem 0;
    font-size: 0.9rem; line-height: 1.65; color: var(--slate);
}}
.insight b {{ color: var(--text); font-weight: 600; }}
.insight.amber {{
    background: linear-gradient(135deg, rgba({_rgb(t['amber'])},{t['insight_bg_alpha']}), rgba({_rgb(t['amber'])},{t['insight_bg_alpha2']}));
    border-color: rgba({_rgb(t['amber'])},{t['insight_border_alpha']}); border-left-color: var(--amber);
}}
.insight.rose {{
    background: linear-gradient(135deg, rgba({_rgb(t['rose'])},{t['insight_bg_alpha']}), rgba({_rgb(t['rose'])},{t['insight_bg_alpha2']}));
    border-color: rgba({_rgb(t['rose'])},{t['insight_border_alpha']}); border-left-color: var(--rose);
}}
.insight.emerald {{
    background: linear-gradient(135deg, rgba({_rgb(t['emerald'])},{t['insight_bg_alpha']}), rgba({_rgb(t['emerald'])},{t['insight_bg_alpha2']}));
    border-color: rgba({_rgb(t['emerald'])},{t['insight_border_alpha']}); border-left-color: var(--emerald);
}}
.insight.violet {{
    background: linear-gradient(135deg, rgba({_rgb(t['violet'])},{t['insight_bg_alpha']}), rgba({_rgb(t['violet'])},{t['insight_bg_alpha2']}));
    border-color: rgba({_rgb(t['violet'])},{t['insight_border_alpha']}); border-left-color: var(--violet);
}}

/* TABS */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px; background: var(--surface); border-radius: 14px;
    padding: 5px; border: 1px solid var(--border);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 10px !important; padding: 10px 24px !important;
    font-family: var(--font-body) !important; font-weight: 500 !important;
    font-size: 0.88rem !important; color: var(--slate) !important;
    background: transparent !important; border: none !important;
}}
.stTabs [data-baseweb="tab"][aria-selected="true"] {{
    background: var(--card) !important; color: var(--primary) !important;
    box-shadow: 0 2px 12px {t['tab_active_shadow']}; font-weight: 700 !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}

/* INPUTS */
.stSelectbox label, .stMultiSelect label, .stDateInput label, .stRadio label {{
    color: var(--text) !important; font-weight: 500 !important;
}}
.stSelectbox > div > div, .stMultiSelect > div > div {{
    background: var(--surface) !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}}

/* FOOTER */
.footer-bar {{
    text-align: center; padding: 2rem 0 1rem 0;
    font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.1em;
    color: {t['footer_color']}; text-transform: uppercase;
}}
.footer-bar span {{ color: var(--primary); opacity: 0.5; }}

/* USER STAT CARD */
.user-stat-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 14px; padding: 1.5rem;
    {"box-shadow: 0 1px 4px rgba(0,0,0,0.04);" if not dark else ""}
}}
.user-stat-card .stat-row {{
    display: flex; justify-content: space-between; padding: 0.45rem 0;
    border-bottom: 1px solid {t['stat_border']}; font-size: 0.88rem;
}}
.user-stat-card .stat-row:last-child {{ border-bottom: none; }}
.user-stat-card .stat-label {{ color: var(--slate); }}
.user-stat-card .stat-val {{ color: var(--text); font-family: var(--font-mono); font-weight: 600; }}

/* THEME TOGGLE BUTTON */
.theme-toggle {{
    display: flex; align-items: center; gap: 10px;
    padding: 0.6rem 0; margin-bottom: 0.8rem;
}}
.theme-toggle-label {{
    font-family: var(--font-mono); font-size: 0.72rem;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--primary);
}}

/* ─── NATIVE STREAMLIT WIDGET OVERRIDES ─── */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stText"], div[data-testid="stCaptionContainer"] {{
    color: var(--slate) !important;
}}
.stMarkdown b, .stMarkdown strong {{ color: var(--text) !important; }}

[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div {{
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}}
[data-baseweb="select"] svg {{ fill: var(--slate) !important; }}
[data-baseweb="popover"] > div,
[data-baseweb="menu"] {{
    background-color: var(--card) !important;
    border: 1px solid var(--border) !important;
}}
[data-baseweb="menu"] li {{
    color: var(--text) !important;
}}
[data-baseweb="menu"] li:hover {{
    background-color: var(--surface) !important;
}}
[data-baseweb="tag"] {{
    background-color: {"rgba(8,145,178,0.12)" if not dark else "rgba(56,189,248,0.12)"} !important;
    color: var(--primary) !important;
}}
[data-baseweb="tag"] span {{ color: var(--primary) !important; }}

[data-baseweb="input"] {{
    background-color: var(--surface) !important;
    border-color: var(--border) !important;
}}
[data-baseweb="input"] input {{
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}}
[data-baseweb="calendar"] {{
    background-color: var(--card) !important;
}}

.stRadio > div > label > div:first-child {{
    color: var(--slate) !important;
}}
.stRadio > div > label span {{ color: var(--text) !important; }}

[data-testid="stToggle"] label span {{ color: var(--text) !important; }}

[data-testid="stExpander"] {{
    background-color: var(--card) !important;
    border-color: var(--border) !important;
    border-radius: 12px !important;
}}
[data-testid="stExpander"] summary span {{ color: var(--text) !important; }}

.stTabs [data-baseweb="tab-panel"] {{
    background-color: transparent !important;
}}

.stException {{ border-radius: 12px !important; }}

.stMarkdown code {{
    background-color: var(--surface) !important;
    color: var(--primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}}

::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--muted); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--slate); }}
</style>
"""