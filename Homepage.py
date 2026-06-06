# streamlit_app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Demo App", page_icon="🚀")

if not st.user.is_logged_in:
    st.title("Please log in")
    st.button("Log in with Google", on_click=st.login)
    st.stop()

pages = {
    "Menu": [
        st.Page("repository/Home.py", title="Home", icon="🏠"),
        st.Page("repository/Upload_Image.py", title="Upload Image", icon="📤"),
        st.Page("repository/Search_Image.py", title="Search Image", icon="🔍"),
    ]
}

pg = st.navigation(pages)
pg.run()

with st.sidebar:
    st.button("Log out", on_click=st.logout)
    st.write(f"Logged in as: {(" ".join(st.user.name.split()[:2]))}\n({st.user.email})")