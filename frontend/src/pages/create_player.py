"""
Streamlit page for player account registration.

Allows users to create a new player profile with username, password, Elo, email, etc.

Endpoint used:
    POST /player
"""

import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

st.title("Create a player account")
logger = get_page_logger("create_player")

username = st.text_input("Username", max_chars=30)
password = st.text_input("Password", type="password")

is_pwd_long_enough = len(password) >= 35
st.write("✅" if is_pwd_long_enough else "❌", "At least 35 characters")

elo = st.number_input("Elo", min_value=1000, max_value=3000)
email = st.text_input("Email")
pokemon_fan = st.checkbox("Pokemons fan?")

with st.container(horizontal_alignment="center"):
    if st.button("Create", width=150, disabled=not username or not is_pwd_long_enough):
        logger.info("Create a player")
        player = {
            "username": username,
            "password": password,
            "elo": elo,
            "email": email,
            "pokemon_fan": pokemon_fan,
        }

        response = api_client.post("/player/", json=player)

        if response:
            if response["status_code"] == 200:
                st.success(f"Player {username} successfully created! 🎉")
                logger.info("Player created successfully")
            else:
                st.error(f"Error: {response['data']}")
                logger.info("Error while creating player")

if st.button("Back to homepage", type="primary"):
    st.switch_page("pages/home.py")