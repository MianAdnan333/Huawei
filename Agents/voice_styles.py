"""Theme CSS and HTML blocks for the voice agent app."""
from html import escape
from textwrap import dedent

import streamlit as st

THEMES = {
    "dark": {
        "bg": "#090d1a", "glow": "rgba(236, 72, 153, 0.16)", "glow2": "rgba(99, 102, 241, 0.18)",
        "sidebar": "#0d1324", "surface": "rgba(255, 255, 255, 0.04)", "surface_solid": "#121a30",
        "border": "rgba(255, 255, 255, 0.09)", "text": "#e8eaf3", "muted": "#98a1b9",
        "user_bubble": "rgba(99, 102, 241, 0.18)",
    },
    "light": {
        "bg": "#f6f6fb", "glow": "rgba(236, 72, 153, 0.10)", "glow2": "rgba(99, 102, 241, 0.10)",
        "sidebar": "#ffffff", "surface": "#ffffff", "surface_solid": "#ffffff",
        "border": "#e5e7f0", "text": "#111827", "muted": "#667085",
        "user_bubble": "rgba(99, 102, 241, 0.08)",
    },
}
ACCENT = "#6366f1"
GRADIENT = "linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%)"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root {{
    --bg: {bg}; --sidebar: {sidebar}; --surface: {surface}; --surface-solid: {surface_solid};
    --border: {border}; --text: {text}; --muted: {muted}; --user-bubble: {user_bubble};
    --accent: {accent}; --gradient: {gradient};
}}
html, body, .stApp {{ font-family: 'Inter', sans-serif; }}
.stApp {{
    background:
        radial-gradient(900px 420px at 10% -10%, {glow2}, transparent 60%),
        radial-gradient(900px 420px at 95% 0%, {glow}, transparent 60%),
        var(--bg);
    color: var(--text);
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] {{ color: var(--text); }}
.stApp [data-testid="stCaptionContainer"] {{ color: var(--muted) !important; }}
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 1.5rem; max-width: 900px; }}

section[data-testid="stSidebar"] {{ background: var(--sidebar); border-right: 1px solid var(--border); }}
.side-brand {{ font-weight: 800; font-size: 1.05rem; }}
.side-title {{
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted) !important; margin: 1.1rem 0 0.4rem;
}}

.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stSelectbox"] > div > div {{
    background: var(--surface-solid) !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}}
.stApp [data-testid="stTextInputField"], .stApp [data-testid="stSelectbox"] *, .stApp textarea {{
    background-color: transparent !important; color: var(--text) !important;
}}
.stApp [data-testid="stTextInputField"]::placeholder, .stApp textarea::placeholder {{ color: var(--muted) !important; }}

.stApp .stButton > button {{
    border-radius: 999px; border: 1px solid var(--border); background: var(--surface-solid);
    color: var(--text); font-weight: 500; transition: all 0.2s ease;
}}
.stApp .stButton > button:hover {{ border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }}

/* Recorder card */
.st-key-recorder_panel {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 20px !important; padding: 1.2rem 1.4rem !important;
    box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
}}
[data-testid="stAudioInput"] div:has([data-testid="stAudioInputWaveSurfer"]) {{
    background: var(--surface-solid) !important; border-radius: 14px;
}}
[data-testid="stAudioInputWaveformTimeCode"] {{ color: var(--muted) !important; background: transparent !important; }}

/* Big record button (the default one is a tiny icon) */
[data-testid="stAudioInput"] div:has(> [data-testid="stAudioInputActionButton"]) {{ min-height: 76px; align-items: center; }}
[data-testid="stAudioInputActionButton"] {{
    width: 58px !important; height: 58px !important; min-width: 58px; margin: 0 0.6rem 0 0.2rem;
    border-radius: 50% !important; background: var(--gradient) !important; color: #fff !important;
    box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.55); animation: micPulse 2s infinite; transition: transform 0.15s ease;
}}
[data-testid="stAudioInputActionButton"]:hover {{ transform: scale(1.08); }}
[data-testid="stAudioInputActionButton"] svg, [data-testid="stAudioInputActionButton"] span {{
    width: 28px !important; height: 28px !important; font-size: 28px !important; color: #fff !important; fill: #fff !important;
}}
[data-testid="stAudioInputActionButton"][aria-label="Stop recording"] {{
    background: #ef4444 !important; animation: recPulse 1.2s infinite;
}}
@keyframes micPulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(168, 85, 247, 0.55); }} 100% {{ box-shadow: 0 0 0 16px rgba(168, 85, 247, 0); }} }}
@keyframes recPulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }} 100% {{ box-shadow: 0 0 0 16px rgba(239, 68, 68, 0); }} }}

/* Top bar */
.topbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }}
.brand {{ display: flex; align-items: center; gap: 0.7rem; font-weight: 800; font-size: 1.1rem; color: var(--text); }}
.logo {{
    width: 36px; height: 36px; border-radius: 10px; background: var(--gradient); display: grid;
    place-items: center; color: #fff; box-shadow: 0 6px 18px rgba(168, 85, 247, 0.35);
}}
.pill {{
    display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.35rem 0.85rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; border: 1px solid var(--border); background: var(--surface-solid); color: var(--text);
}}
.dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.dot.on {{ background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.18); }}
.dot.off {{ background: #f59e0b; box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.18); }}

/* Hero with animated orb */
.hero {{ text-align: center; padding: 1.4rem 1rem 1.2rem; }}
.orb-wrap {{ position: relative; width: 130px; height: 130px; margin: 0.4rem auto 1.4rem; }}
.orb {{
    position: absolute; inset: 18px; border-radius: 50%; background: var(--gradient);
    display: grid; place-items: center; font-size: 2.4rem;
    box-shadow: 0 0 40px rgba(168, 85, 247, 0.45); animation: breathe 3.2s ease-in-out infinite;
}}
.ring {{
    position: absolute; inset: 0; border-radius: 50%; border: 2px solid rgba(168, 85, 247, 0.35);
    animation: ripple 3.2s ease-out infinite;
}}
.ring.delay {{ animation-delay: 1.6s; }}
.hero h1 {{ font-size: 2.4rem; font-weight: 800; letter-spacing: -0.03em; margin: 0 0 0.5rem; padding: 0; }}
.gradient-text {{ background: var(--gradient); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.hero p {{ color: var(--muted) !important; font-size: 1.02rem; max-width: 560px; margin: 0 auto; }}

/* Conversation */
.section-label {{
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted); margin: 1.6rem 0 0.6rem;
}}
[data-testid="stChatMessage"] {{
    background: var(--surface-solid); border: 1px solid var(--border); border-radius: 16px;
    padding: 0.85rem 1rem; margin-bottom: 0.6rem; animation: fadeUp 0.3s ease-out;
}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ background: var(--user-bubble); }}

/* Tips */
.tips {{ display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin-top: 1rem; }}
.tip {{
    padding: 0.4rem 0.85rem; border-radius: 999px; font-size: 0.84rem; color: var(--text);
    border: 1px solid var(--border); background: var(--surface-solid);
}}
.empty {{ text-align: center; color: var(--muted); padding: 1.2rem 0 0.4rem; font-size: 0.92rem; }}

@keyframes breathe {{ 0%, 100% {{ transform: scale(1); }} 50% {{ transform: scale(1.06); }} }}
@keyframes ripple {{ from {{ transform: scale(0.75); opacity: 0.9; }} to {{ transform: scale(1.25); opacity: 0; }} }}
@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@media (max-width: 640px) {{ .hero h1 {{ font-size: 1.8rem; }} }}
</style>
"""


def html(markup: str):
    # Indented lines after a blank line become a Markdown code block, so drop both
    lines = (line for line in dedent(markup).splitlines() if line.strip())
    st.markdown("\n".join(lines), unsafe_allow_html=True)


def apply_theme(dark: bool):
    tokens = THEMES["dark" if dark else "light"]
    st.markdown(CSS.format(**tokens, accent=ACCENT, gradient=GRADIENT), unsafe_allow_html=True)


def side_title(text: str):
    html(f'<div class="side-title">{escape(text)}</div>')


def topbar(connected: bool, status: str):
    html(f"""
    <div class="topbar">
        <div class="brand"><div class="logo">🎙️</div>Voice Agent</div>
        <div class="pill"><span class="dot {'on' if connected else 'off'}"></span>{escape(status)}</div>
    </div>
    """)


def hero(subtitle: str):
    html(f"""
    <div class="hero">
        <div class="orb-wrap"><div class="ring"></div><div class="ring delay"></div><div class="orb">✈️</div></div>
        <h1>Talk to your <span class="gradient-text">AI travel advisor</span></h1>
        <p>{escape(subtitle)}</p>
    </div>
    """)


def tips(items: list[str]):
    chips = "".join(f'<span class="tip">💬 {escape(item)}</span>' for item in items)
    html(f'<div class="empty">Try asking something like:</div><div class="tips">{chips}</div>')


def section_label(text: str):
    html(f'<div class="section-label">{escape(text)}</div>')
