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
password_min_length = 8

is_pwd_long_enough = len(password) >= password_min_length
st.write("✅" if is_pwd_long_enough else "❌", f"At least {password_min_length} characters")

role = st.selectbox("What is your role?", ("admin", "user"), index=None, placeholder="Select your role")

with st.container(horizontal_alignment="center"):
    if st.button("Create", width=150, disabled=not email or not is_pwd_long_enough):
        logger.info("Create a user")
        user = {
            "email": email,
            "password": password,
            "role_user": role,
        }

        try:
            response = api_client.post("/users/", json=user)

            if response["status_code"] in [200, 201]:
                st.success(f"Account with email {email} successfully created! 🎉")
                logger.info("User account created successfully")
            else:
                error_msg = response.get("detail", response.get("message", "Unknown error"))
                st.error(f"Error: {error_msg}")
                logger.error(f"Error creating user: {error_msg}")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")
            logger.error(f"API request failed: {str(e)}")

st.write(f"Données envoyées: {user}")

if st.button("Back to homepage", type="primary"):
    st.switch_page("pages/home.py")

