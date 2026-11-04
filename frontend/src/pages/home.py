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

        # ✅ Vérification que email et password ne sont pas vides
        if not email or not password:
            st.error("❌ Email and password are required!")
            logger.warning("Login failed: Empty email or password")
            st.stop()  # Arrête l'exécution

        try:
            # ✅ Appel à /login
            response = api_client.post("/login", json={"email": email, "password": password})

            # ✅ Vérification de la réponse
            if not response:
                st.error("❌ No response from server.")
                logger.error("API returned None or empty response")
                st.stop()

            status_code = response.get("status_code")
            data = response.get("data", {})

            # ✅ Gestion des erreurs
            if status_code == 401:
                st.error("❌ Invalid credentials")
                logger.warning(f"Login failed: 401 Unauthorized for user {email}.")
                st.stop()

            elif status_code != 200:
                st.error(f"❌ Server error: {data.get('detail', 'Unknown error')}")
                logger.error(f"Login failed: Status {status_code}, Data: {data}")
                st.stop()

            # ✅ Login réussi : récupérer toutes les infos
            access_token = data.get("access_token")
            user_id = data.get("id_user")

            if not access_token or not user_id:
                st.error("❌ Missing access token or user ID in response")
                logger.error("Invalid response format from /login")
                st.stop()

            # ✅ Récupérer les infos complètes via /users/me
            user_full = api_client.get(
                "/users/me",
                headers={"Authorization": f"Bearer {access_token}"}
            ).get("data", {})

            # ✅ Vérifier que user_full contient bien les infos
            if not user_full:
                st.error("❌ Failed to load user data from /users/me")
                logger.error("Empty response from /users/me")
                st.stop()

            # ✅ Stocker TOUTES les infos dans session_state
            st.session_state["user"] = {
                **user_full,  # ✅ email, role_user, created_at, etc.
                "access_token": access_token,
                "id_user": user_id  # ✅ Garde aussi l'ID pour référence
            }

            st.success("✅ Login successful!")
            logger.info(f"User {email} logged in successfully")
            st.switch_page("pages/main_app.py")

        except Exception as e:
            logger.exception(f"Critical error during API call: {str(e)}")
            st.error(f"❌ Connection error: {str(e)}")
            # ✅ Nettoyer la session en cas d'erreur
            if "user" in st.session_state:
                del st.session_state["user"]

st.space("small")

if st.button("Sign Up"):
    st.switch_page("pages/create_user.py")

