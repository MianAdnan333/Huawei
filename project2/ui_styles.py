"""Theme CSS and small HTML blocks for the RAG workspace."""
from html import escape
from textwrap import dedent

import streamlit as st

THEMES = {
    "dark": {
        "bg": "#0b1020",
        "bg_glow": "rgba(124, 92, 255, 0.18)",
        "sidebar": "#0f1529",
        "surface": "rgba(255, 255, 255, 0.04)",
        "surface_solid": "#141b31",
        "border": "rgba(255, 255, 255, 0.09)",
        "text": "#e7eaf3",
        "muted": "#97a0b8",
        "user_bubble": "rgba(124, 92, 255, 0.16)",
    },
    "light": {
        "bg": "#f5f6fb",
        "bg_glow": "rgba(124, 92, 255, 0.10)",
        "sidebar": "#ffffff",
        "surface": "#ffffff",
        "surface_solid": "#ffffff",
        "border": "#e4e7f0",
        "text": "#111827",
        "muted": "#667085",
        "user_bubble": "rgba(124, 92, 255, 0.08)",
    },
}

ACCENT = "#7c5cff"
GRADIENT = "linear-gradient(135deg, #7c5cff 0%, #4f8bff 50%, #22d3ee 100%)"

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
    background: radial-gradient(1200px 500px at 85% -10%, {bg_glow}, transparent 60%), var(--bg);
    color: var(--text);
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stWidgetLabel"] {{ color: var(--text); }}
.stApp [data-testid="stCaptionContainer"], .stApp small {{ color: var(--muted) !important; }}

header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 1.5rem; max-width: 1280px; }}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: var(--sidebar); border-right: 1px solid var(--border); }}
.side-title {{
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted) !important; margin: 1.1rem 0 0.4rem;
}}
.side-brand {{ display: flex; align-items: center; gap: 0.6rem; font-weight: 800; font-size: 1.05rem; }}

/* Inputs */
.stApp [data-testid="stTextInputRootElement"], .stApp [data-testid="stTextAreaRootElement"],
.stApp [data-testid="stSelectbox"] > div > div, .stApp [data-testid="stChatInput"] > div {{
    background: var(--surface-solid) !important; border-color: var(--border) !important;
    color: var(--text) !important; border-radius: 10px !important;
}}
.stApp [data-testid="stTextInputField"], .stApp [data-testid="stSelectbox"] *, .stApp textarea {{
    background-color: transparent !important; color: var(--text) !important;
}}
.stApp [data-testid="stTextInputField"]::placeholder, .stApp textarea::placeholder {{ color: var(--muted) !important; }}

/* Buttons */
.stApp .stButton > button {{
    border-radius: 999px; border: 1px solid var(--border); background: var(--surface-solid);
    color: var(--text); font-weight: 500; transition: all 0.2s ease;
}}
.stApp .stButton > button:hover {{ border-color: var(--accent); color: var(--accent); transform: translateY(-1px); }}

/* Panels (keyed bordered containers) */
.st-key-doc_panel, .st-key-chat_panel {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 18px !important; padding: 1.25rem 1.25rem 1rem !important;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}}
.panel-title {{ display: flex; align-items: center; gap: 0.5rem; font-weight: 700; font-size: 1.05rem; margin-bottom: 0.35rem; }}
.panel-sub {{ color: var(--muted); font-size: 0.88rem; margin-bottom: 0.9rem; }}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {{
    background: var(--surface-solid); border: 1.5px dashed var(--border); border-radius: 14px;
    transition: border-color 0.2s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{ border-color: var(--accent); }}

/* Chat */
[data-testid="stChatMessage"] {{
    background: var(--surface-solid); border: 1px solid var(--border); border-radius: 14px;
    padding: 0.85rem 1rem; margin-bottom: 0.6rem; animation: fadeUp 0.3s ease-out;
}}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ background: var(--user-bubble); }}
[data-testid="stChatInput"] {{ border-radius: 14px; }}
[data-testid="stExpander"] details {{ border-color: var(--border); border-radius: 12px; background: transparent; }}

/* Top bar */
.topbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.4rem; }}
.brand {{ display: flex; align-items: center; gap: 0.7rem; font-weight: 800; font-size: 1.15rem; color: var(--text); }}
.logo {{
    width: 36px; height: 36px; border-radius: 10px; background: var(--gradient);
    display: grid; place-items: center; color: #fff; font-size: 1.1rem; box-shadow: 0 6px 18px rgba(124, 92, 255, 0.35);
}}
.pill {{
    display: inline-flex; align-items: center; gap: 0.45rem; padding: 0.35rem 0.85rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600; border: 1px solid var(--border); background: var(--surface-solid); color: var(--text);
}}
.dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.dot.on {{ background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.18); }}
.dot.off {{ background: #f59e0b; box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.18); }}

/* Hero */
.hero {{ text-align: center; padding: 2.2rem 1rem 1.6rem; animation: fadeUp 0.5s ease-out; }}
.hero.compact {{ text-align: left; padding: 0 0 1.2rem; }}
.eyebrow {{
    display: inline-block; font-size: 0.78rem; font-weight: 600; color: var(--accent);
    background: rgba(124, 92, 255, 0.10); padding: 0.3rem 0.8rem; border-radius: 999px; margin-bottom: 0.9rem;
}}
.hero h1 {{ font-size: 2.7rem; font-weight: 800; letter-spacing: -0.03em; line-height: 1.15; margin: 0 0 0.6rem; padding: 0; }}
.hero.compact h1 {{ font-size: 1.9rem; }}
.gradient-text {{ background: var(--gradient); -webkit-background-clip: text; background-clip: text; color: transparent; }}
.hero p {{ color: var(--muted) !important; font-size: 1.05rem; max-width: 640px; margin: 0 auto; }}
.hero.compact p {{ margin: 0; font-size: 0.95rem; }}

/* Onboarding steps */
.steps {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem; }}
.step {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 1.3rem;
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
.step:hover {{ transform: translateY(-3px); border-color: var(--accent); }}
.step-num {{
    width: 30px; height: 30px; border-radius: 9px; background: var(--gradient); color: #fff;
    display: grid; place-items: center; font-weight: 700; font-size: 0.85rem; margin-bottom: 0.8rem;
}}
.step h4 {{ margin: 0 0 0.3rem; font-size: 1rem; font-weight: 700; padding: 0; }}
.step p {{ margin: 0; color: var(--muted) !important; font-size: 0.88rem; }}
@media (max-width: 760px) {{ .steps {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 2rem; }} }}

/* Document card */
.doc-card {{
    display: flex; gap: 0.85rem; align-items: center; padding: 0.9rem; border-radius: 14px;
    background: var(--surface-solid); border: 1px solid var(--border); margin-top: 0.9rem;
}}
.doc-icon {{
    width: 42px; height: 42px; border-radius: 11px; background: rgba(124, 92, 255, 0.12);
    display: grid; place-items: center; font-size: 1.3rem; flex-shrink: 0;
}}
.doc-name {{ font-weight: 600; word-break: break-all; }}
.doc-meta {{ color: var(--muted); font-size: 0.8rem; }}
.stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.6rem; margin-top: 0.75rem; }}
.stat {{ background: var(--surface-solid); border: 1px solid var(--border); border-radius: 12px; padding: 0.65rem; text-align: center; }}
.stat b {{ display: block; font-size: 1.15rem; }}
.stat span {{ color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }}

/* Empty state */
.empty {{ text-align: center; padding: 3rem 1rem; color: var(--muted); }}
.empty .icon {{ font-size: 2.4rem; margin-bottom: 0.6rem; }}
.empty h4 {{ color: var(--text); margin: 0 0 0.3rem; padding: 0; }}

@keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
</style>
"""


def apply_theme(dark: bool):
    tokens = THEMES["dark" if dark else "light"]
    st.markdown(CSS.format(**tokens, accent=ACCENT, gradient=GRADIENT), unsafe_allow_html=True)


def html(markup: str):
    # Indented lines after a blank line become a Markdown code block, so drop both
    lines = (line for line in dedent(markup).splitlines() if line.strip())
    st.markdown("\n".join(lines), unsafe_allow_html=True)


def topbar(connected: bool, status: str):
    dot = "on" if connected else "off"
    html(f"""
    <div class="topbar">
        <div class="brand"><div class="logo">✨</div>Multi-Doc RAG Workspace</div>
        <div class="pill"><span class="dot {dot}"></span>{escape(status)}</div>
    </div>
    """)


def hero(compact: bool = False):
    html(f"""
    <div class="hero {'compact' if compact else ''}">
        {'' if compact else '<div class="eyebrow">⚡ Powered by Google Gemini</div>'}
        <h1>Chat with your <span class="gradient-text">documents</span></h1>
        <p>Upload a PDF, Word, CSV or Excel file and get accurate answers grounded in its content, with sources.</p>
    </div>
    """)


def onboarding_steps():
    html("""
    <div class="steps">
        <div class="step"><div class="step-num">1</div><h4>Add your API key</h4>
            <p>Paste your Google Gemini key in the sidebar. It stays in this session only.</p></div>
        <div class="step"><div class="step-num">2</div><h4>Upload a document</h4>
            <p>PDF, DOCX, CSV, XLSX or XLS. It is split and indexed automatically.</p></div>
        <div class="step"><div class="step-num">3</div><h4>Ask anything</h4>
            <p>Get answers based only on your file, with the source passages shown.</p></div>
    </div>
    """)


def side_title(text: str):
    html(f'<div class="side-title">{escape(text)}</div>')


def panel_title(icon: str, title: str, subtitle: str):
    html(f'<div class="panel-title">{icon} {escape(title)}</div><div class="panel-sub">{escape(subtitle)}</div>')


def doc_card(name: str, size_bytes: int, sections: int, chunks: int, embedding_model: str):
    size_kb = size_bytes / 1024
    size = f"{size_kb / 1024:.1f} MB" if size_kb >= 1024 else f"{size_kb:.0f} KB"
    html(f"""
    <div class="doc-card">
        <div class="doc-icon">📄</div>
        <div><div class="doc-name">{escape(name)}</div>
        <div class="doc-meta">{size} · indexed with {escape(embedding_model)}</div></div>
    </div>
    <div class="stats">
        <div class="stat"><b>{sections}</b><span>Sections</span></div>
        <div class="stat"><b>{chunks}</b><span>Chunks</span></div>
        <div class="stat"><b>✓</b><span>Ready</span></div>
    </div>
    """)


def empty_state(icon: str, title: str, text: str):
    html(f'<div class="empty"><div class="icon">{icon}</div><h4>{escape(title)}</h4><div>{escape(text)}</div></div>')
