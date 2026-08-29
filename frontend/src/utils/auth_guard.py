import logging
import time

import streamlit as st


def check_authentification():
    """Checks if the user is authenticated.

    If the user is not logged, he is redirected to the home page.
    """
    if not st.session_state.get("access_token"):
        logging.info("Not logged in, return to the home page")
        st.error("You must be logged in to access this page. Return to the home page")
        time.sleep(1)
        st.switch_page("pages/home.py")