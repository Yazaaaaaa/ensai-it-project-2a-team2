import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

# REMOVAL OF THE NAVBAR
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

logger = get_page_logger("settings.py")
st.title("Settings")

# CONNEXION CHECK
if "user" not in st.session_state:
    st.warning("Please log in to access settings.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/home.py")
    st.stop()

# PERSONAL DATA
user = st.session_state["user"]
access_token = user.get("access_token")
user_id = user.get("id_user")
user_role = user.get("role_user", "user")

st.header("My Account", icon=":material/person:")
st.markdown(f"""
**Email:** {user.get("email", "N/A")}  \
**Role:** {user_role}  \
**ID:** {user_id}  \
**Created at:** {user.get("created_at", "N/A")}
""")


# USER'S CONNEXION HISTORY
st.markdown("---")
st.subheader("Connection History", icon=":material/date_range:")

if not user_id:
    st.error("User ID is missing. Please log in again.")
    st.stop()

response = api_client.get(
    f"/connections/users/{user_id}", headers={"Authorization": f"Bearer {access_token}"}
    )
if response.get("status_code") != 200:
    st.error(f"Failed to load connections: {response.get('data', {}).get('detail', 'Unknown error')}")
else:
    st.dataframe(response["data"], width="stretch", column_order=("id_login", "login_at"))

# LOGOUT BUTTON
st.markdown("---")
if st.button("Log Out", type="secondary", icon=":material/logout:"):
    try:
        logout_response = api_client.post(
            "/users/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if logout_response.get("status_code") == 204:
            del st.session_state["user"]
            if "access_token" in st.session_state:
                del st.session_state["access_token"]
            st.success("Successfully logged out!")
            st.rerun()
        else:
            st.error(f"Logout failed: {logout_response.get('data', {}).get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Logout error: {str(e)}")
        logger.error(f"Logout error: {str(e)}")

# ADMIN PANEL
if user_role == "admin":
    st.markdown("---")
    st.header("Admin Panel", icon=":material/admin_panel_settings:")

    # Ban a user
    st.subheader("Ban a User", icon=":material/block:")
    ban_user_id = st.number_input("User ID to ban", min_value=1, key="ban_user_id")
    if st.button("Ban User", type="primary", key="ban_button"):
        try:
            ban_response = api_client.post(
                f"/admin/users/{ban_user_id}/ban",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if ban_response.get("status_code") == 204:
                st.success(f"User {ban_user_id} banned successfully!")
            else:
                st.error(f"Failed to ban user: {ban_response.get('data', {}).get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Error banning user: {str(e)}")
            logger.error(f"Error banning user: {str(e)}")

    # Connection history of all users
    st.subheader(" All Connections", icon=":material/date_range:")
    if st.button("Load All Connections", key="load_all_connections"):
        response = api_client.get(
            "/connections/", headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.get("status_code") != 200:
            st.error(f"Failed to load connections: {response.get('data', {}).get('detail', 'Unknown error')}")
        else:
            st.dataframe(response["data"], width="stretch")

    # Data importation
    st.subheader(" Data Import", icon=":material/database_upload:")
    if st.button("Start Data Import", key="import_data"):
        try:
            import_response = api_client.post(
                "/admin/import",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if import_response.get("status_code") == 202:
                st.success("Data import started in background!")
            else:
                st.error(f"Failed to start import: {import_response.get('data', {}).get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"Import error: {str(e)}")
            logger.error(f"Import error: {str(e)}")
