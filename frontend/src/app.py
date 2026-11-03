import streamlit as st
from utils.env_variables import display_values, load_environment_variables
from utils.log_init import initialize_logs

if "logs_initialized" not in st.session_state:
    initialize_logs("Streamlit App")
    load_environment_variables()
    display_values(include_prefix="BACKEND")
    st.session_state["logs_initialized"] = True

if "user" in st.session_state:
    st.switch_page("pages/main_app.py")
else:
    st.switch_page("pages/home.py")
