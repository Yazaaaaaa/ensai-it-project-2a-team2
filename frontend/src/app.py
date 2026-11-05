import streamlit as st

from utils.env_variables import display_values, load_environment_variables
from utils.log_init import initialize_logs

st.markdown(
    """
    <style>
        .stApp > header + div > div:first-child {
            display: none !important;
        }
        [data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stPageLink"] {
            display: none !important;
        }
    </style>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const style = document.createElement('style');
            style.innerHTML = `
                .stApp > header + div > div:first-child,
                [data-testid="stSidebar"],
                [data-testid="stPageLink"] {
                    display: none !important;
                }
            `;
            document.head.appendChild(style);
        });
    </script>
    """,
    unsafe_allow_html=True
)

if "logs_initialized" not in st.session_state:
    initialize_logs("Streamlit App")
    load_environment_variables()
    display_values(include_prefix="BACKEND")
    st.session_state["logs_initialized"] = True

if "user" in st.session_state:
    st.switch_page("pages/main_app.py")
else:
    st.switch_page("pages/home.py")
