"""
Streamlit page for user account registration.

Allows users to create a new profile with password and email.

Endpoint used:
    POST /user
"""

import os

import streamlit as st
from utils.api_client import api_client
from utils.log_init import get_page_logger

st.title("Create a user account")
logger = get_page_logger("create_user.py")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

password_min_length = int(os.environ["PASSWORD_MIN_LENGTH"])

is_pwd_long_enough = len(password) >= password_min_length
st.write("✅" if is_pwd_long_enough else "❌", f"At least {password_min_length} characters")

role_user = st.selectbox("What is your role?", ("admin", "user"))

with st.container(horizontal_alignment="center"):
    if st.button("Create", width=150, disabled=not email or not is_pwd_long_enough):
        logger.info("Create a user")
        user = {
            "email": email,
            "password": password,
            "role_user": role_user,
        }

        response = api_client.post("/user/", json=user)

        if response:
            if response["status_code"] == 200:
                st.success(f"Player with email {email} successfully created! 🎉")
                logger.info("User account created successfully")
            else:
                st.error(f"Error: {response['data']}")
                logger.info("Error while creating a user account")

if st.button("Back to homepage", type="primary"):
    st.switch_page("pages/home.py")
