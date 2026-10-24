import streamlit as st

from ui.chat import render_chat
from ui.login import render_login
from ui.styles import apply_styles

st.set_page_config(
    page_title="Your Custom Assistant",
    page_icon="🤖",
    layout="centered",
)
apply_styles()

connection = st.session_state.get("connection")
if connection is None:
    render_login()
else:
    render_chat(connection)
