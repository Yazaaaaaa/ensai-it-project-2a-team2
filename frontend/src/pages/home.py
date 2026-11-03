"""
Streamlit home page.

Provides options to log in, sign up for a new account.

Endpoints used:
    POST /login
"""

import streamlit as st
from streamlit import config
from utils.api_client import api_client
from utils.log_init import get_page_logger

if "user" in st.session_state:
    st.switch_page("pages/main_app.py")

st.set_page_config(page_title="Neo-watch", page_icon="🌠", layout="centered")

st.markdown(
    f"""
    <div style="text-align:center">
        <h1 style="color:{config.get_option("theme.primaryColor")}">Neo-watch</h1>
    </div>
    """,
    unsafe_allow_html=True,
)
logger = get_page_logger("home")

email = st.text_input("Email", placeholder="Enter your Email")
password = st.text_input("Password", type="password", placeholder="Enter your password")

with st.container(horizontal_alignment="center"):
    if st.button("Log in"):
        logger.info(f"Attempting login for user: {email}")

        try:
            response = api_client.post("/login", json={"email": email, "password": password})

            if response:
                status_code = response.get("status_code")
                data = response.get("data")

                if status_code == 200:
                    logger.info(f"User {email} successfully logged in.")
                    user = data
                    st.session_state["user"] = user
                    st.session_state["access_token"] = user["access_token"]
                    st.success(f"Welcome {user['id_user']} ! 🎉")
                    st.switch_page("pages/main_app.py")
                elif status_code == 401:
                    logger.warning(f"Login failed: 401 Unauthorized for user {email}.")
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
    st.switch_page("pages/create_user.py")
