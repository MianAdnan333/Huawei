import streamlit as st

CSS = """
<style>
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
.block-container { padding-top: 2.5rem; max-width: 820px; }

.hero { text-align: center; margin: 1.5rem 0 1.75rem; }
.hero-icon { font-size: 3rem; line-height: 1; }
.hero-title {
    font-size: 2.1rem;
    font-weight: 800;
    margin: 0.5rem 0 0.25rem;
    background: linear-gradient(90deg, #6C5CE7, #00B894);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.hero-subtitle { opacity: 0.7; font-size: 1rem; }

.status-pill {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 999px;
    font-size: 0.8rem;
    background: rgba(0, 184, 148, 0.15);
    color: #00A383;
    font-weight: 600;
}
</style>
"""


def apply_styles():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-icon">{icon}</div>
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
