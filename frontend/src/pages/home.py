"""
Streamlit home page.

Provides options to log in, sign up for a new account, or reset the database.

Endpoints used:
    POST /login
    GET /reset_database
"""

import streamlit as st
from streamlit import config

from utils.api_client import api_client
from utils.log_init import get_page_logger

if "player" in st.session_state:
    st.switch_page("pages/player_menu.py")

st.set_page_config(page_title="Coin flip game", page_icon="🪙", layout="centered")

st.markdown(
    f"""
    <div style="text-align:center">
        <h1 style="color:{config.get_option("theme.primaryColor")}">Coin flip game</h1>
    </div>
    """,
    unsafe_allow_html=True,
)
logger = get_page_logger("home")

username = st.text_input("Username", placeholder="Enter username")
password = st.text_input("Password", type="password", placeholder="Enter password")

with st.container(horizontal_alignment="center"):
    if st.button("Log in"):
        logger.info(f"Attempting login for user: {username}")

        try:
            response = api_client.post("/login", json={"username": username, "password": password})

            if response:
                status_code = response.get("status_code")
                data = response.get("data")

                if status_code == 200:
                    logger.info(f"User {username} successfully logged in.")
                    player = data
                    st.session_state["player"] = player
                    st.session_state["access_token"] = player["access_token"]
                    st.success(f"Welcome {player['username']} ! 🎉")
                    st.switch_page("pages/player_menu.py")
                elif status_code == 401:
                    logger.warning(f"Login failed: 401 Unauthorized for user {username}.")
                    st.error("Invalid credentials")
                else:
                    logger.error(f"Login failed: Status {status_code}, Data: {data}")
                    st.error("Server error, see logs.")
            else:
                logger.error("API returned None or empty response")
                st.error("No response from server.")

        except Exception as e:
            logger.exception(f"Critical error during API call: {str(e)}")
            st.error(f"Connection error: {str(e)}")

st.space("small")

if st.button("Sign Up"):
    st.switch_page("pages/create_player.py")

if st.button("Reset Database", type="primary"):
    logger.info("Reset the database")
    response = api_client.get("/reset_database")

    if response:
        logger.info("Database successfully reset")
        st.toast("Database successfully reset ✅")
    else:
        logger.info("Error during database reset")
        st.toast("Error during database reset ❌")