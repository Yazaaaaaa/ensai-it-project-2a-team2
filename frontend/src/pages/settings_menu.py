import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger


logger = get_page_logger("settings.py")
st.title("⚙️ Settings")


def safe_get_api_data(response, data_key="data"):
    """
    Normalises the API response to prevent type errors.
    - If `response` is a dict → returns `response[data_key]` or an empty list
    - If `response` is a str → returns an empty list and logs the error
    - Otherwise → returns an empty list
    """
    # Cas 1: Réponse est une chaîne (erreur)
    if isinstance(response, str):
        logger.error(f"API returned string (error): {response}")
        st.error(f"❌ Server error: {response}")
        return []

    # Cas 2: Réponse est une liste (backend direct)
    if isinstance(response, list):
        return response  # ✅ Retourne la liste directement

    # Cas 3: Réponse est un dict (format standard)
    if isinstance(response, dict):
        data = response.get(data_key, response)  # ✅ Gère les deux formats

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Essayer de trouver une liste dans le dict
            for value in data.values():
                if isinstance(value, list):
                    return value
            return []
        else:
            logger.error(f"Unexpected data type in response: {type(data)}")
            return []

    # Cas 4: Autre type
    logger.error(f"API returned unexpected type: {type(response)}")
    return []


# ========== VÉRIFICATION DE LA CONNEXION ==========
if "user" not in st.session_state:
    st.warning("⚠️ Please log in to access settings.")
    if st.button("Go to Login", type="primary"):
        st.switch_page("pages/home.py")
    st.stop()

# ========== RÉCUPÉRATION DES INFOS UTILISATEUR ==========
user = st.session_state["user"]
access_token = user.get("access_token")
user_id = user.get("id_user")
user_role = user.get("role_user", "user")

# ========== AFFICHAGE DES INFOS PERSONNELLES ==========
st.header("👤 My Account")
st.markdown(f"""
**Email:** {user.get("email", "N/A")}  \
**Role:** {user_role}  \
**ID:** {user_id}  \
**Created at:** {user.get("created_at", "N/A")}
""")


# ========== HISTORIQUE DES CONNEXIONS ==========
st.markdown("---")
st.subheader("📅 Connection History")

if not user_id:
    st.error("User ID is missing. Please log in again.")
    st.stop()

try:
    connections_response = api_client.get(
        f"/connections/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if connections_response.get("status_code") != 200:
        st.error(f"Failed to load connections: {connections_response.get('data', {}).get('detail', 'Unknown error')}")
        st.stop()

    connections = connections_response.get("data", [])

    if not connections:
        st.info("No connection history found.")
    else:
        table_data = []
        for conn in connections:
            table_data.append([
                conn.get("id_login", "N/A"),
                conn.get("login_at", "N/A")
                ])
        st.table({
            "Connection ID": [row[0] for row in table_data],
            "Date": [row[1] for row in table_data]
            })
except Exception as e:
    st.error(f"Failed to load connection history: {str(e)}")
    logger.error(f"Error loading connections: {str(e)}")

# ========== BOUTON DE DÉCONNEXION ==========
st.markdown("---")
if st.button("🔚 Log Out", type="secondary"):
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

# ========== FONCTIONNALITÉS ADMIN ==========
if user_role == "admin":
    st.markdown("---")
    st.header("🛡️ Admin Panel")

    # ===== 1. Bannir un utilisateur =====
    st.subheader("Ban a User")
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

    # ===== Connection history of all users =====
    st.subheader("📊 All Connections")
    if st.button("Load All Connections", key="load_all_connections"):
        try:
            all_connections_response = api_client.get("/connections/")

            all_connections = safe_get_api_data(all_connections_response)

            if not all_connections:
                st.info("No connections found.")
            else:
                if isinstance(all_connections, list):
                    st.dataframe(all_connections, use_container_width=True)
                else:
                    st.error("Invalid data format received from server")
                    logger.error(f"Expected list, got: {type(all_connections)}")

        except Exception as e:
            st.error(f"Failed to load all connections: {str(e)}")
            logger.error(f"Error loading all connections: {str(e)}")

    # Data importation
    st.subheader("📥 Data Import")
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
