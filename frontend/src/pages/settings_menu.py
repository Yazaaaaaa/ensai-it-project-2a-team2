import streamlit as st

from utils.api_client import api_client
from utils.log_init import get_page_logger

# ========== INITIALISATION ==========

logger = get_page_logger("settings.py")
st.title("⚙️ Settings")


def safe_get_api_data(response, data_key="data"):
    """
    Normalise la réponse de l'API pour éviter les erreurs de type.
    - Si `response` est un dict → retourne `response[data_key]` ou une liste vide
    - Si `response` est une str (erreur) → retourne une liste vide et log l'erreur
    - Sinon → retourne une liste vide
    """
    if isinstance(response, dict):
        return response.get(data_key, [])
    elif isinstance(response, str):
        logger.error(f"API returned string (error): {response}")
        st.error(f"❌ Server error: {response}")  # Affiche l'erreur à l'utilisateur
        return []
    else:
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
user_id = user.get("id_user")  # ✅ Définition de user_id
user_role = user.get("role_user", "user")  # ✅ Définition de user_role (avec fallback)

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
    st.error("❌ User ID is missing. Please log in again.")
    st.stop()

try:
    # ✅ Header cohérent avec le backend (Authorization: Bearer)
    connections_response = api_client.get(
        f"/connections/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}  # ✅ Header standard
    )

    if connections_response.get("status_code") != 200:
        st.error(f"❌ Failed to load connections: {connections_response.get('data', {}).get('detail', 'Unknown error')}")
        st.stop()

    connections = connections_response.get("data", [])

    if not connections:
        st.info("No connection history found.")
    else:
        for conn in connections:
            st.markdown(f"""
            - **Connection ID:** {conn.get("id_login", "N/A")}
              **Date:** {conn.get("login_at", "N/A")}
            """)
except Exception as e:
    st.error(f"❌ Failed to load connection history: {str(e)}")
    logger.error(f"Error loading connections: {str(e)}")

# ========== BOUTON DE DÉCONNEXION ==========
st.markdown("---")
if st.button("🔚 Log Out", type="secondary"):
    try:
        # ✅ Header cohérent
        logout_response = api_client.post(
            "/users/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if logout_response.get("status_code") == 204:
            del st.session_state["user"]
            if "access_token" in st.session_state:
                del st.session_state["access_token"]
            st.success("✅ Successfully logged out!")
            st.rerun()
        else:
            st.error(f"❌ Logout failed: {logout_response.get('data', {}).get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"❌ Logout error: {str(e)}")
        logger.error(f"Logout error: {str(e)}")

# ========== FONCTIONNALITÉS ADMIN ==========
if user_role == "admin":  # ✅ Utilisation de user_role
    st.markdown("---")
    st.header("🛡️ Admin Panel")

    # ===== 1. Bannir un utilisateur =====
    st.subheader("❌ Ban a User")
    ban_user_id = st.number_input("User ID to ban", min_value=1, key="ban_user_id")
    if st.button("Ban User", type="primary", key="ban_button"):
        try:
            # ✅ Header cohérent
            ban_response = api_client.post(
                f"/admin/users/{ban_user_id}/ban",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if ban_response.get("status_code") == 204:
                st.success(f"✅ User {ban_user_id} banned successfully!")
            else:
                st.error(f"❌ Failed to ban user: {ban_response.get('data', {}).get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Error banning user: {str(e)}")
            logger.error(f"Error banning user: {str(e)}")

    # ===== 2. Voir toutes les connexions =====
    st.subheader("📊 All Connections")
    if st.button("Load All Connections", key="load_all_connections"):
        try:
            all_connections_response = api_client.get("/connections/")
            all_connections = safe_get_api_data(all_connections_response)

            # ✅ Vérifiez que la réponse est valide
            if isinstance(all_connections_response, str):
                st.error(f"❌ Server error: {all_connections_response}")
                logger.error(f"Server returned string: {all_connections_response}")
                st.stop()

            all_connections_response = api_client.get("/connections/")
            all_connections = safe_get_api_data(all_connections_response)

            if not all_connections:
                st.info("No connections found.")
            elif isinstance(all_connections, list):
                st.dataframe(all_connections)
            else:
                st.error(f"❌ Invalid data format: {type(all_connections)}")
                logger.error(f"Invalid data type: {type(all_connections)}")

        except Exception as e:
            st.error(f"❌ Failed to load all connections: {str(e)}")
            logger.error(f"Error loading all connections: {str(e)}")

    # ===== 3. Importer des données =====
    st.subheader("📥 Data Import")
    if st.button("Start Data Import", key="import_data"):
        try:
            # ✅ Header cohérent
            import_response = api_client.post(
                "/admin/import",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if import_response.get("status_code") == 202:
                st.success("✅ Data import started in background!")
            else:
                st.error(f"❌ Failed to start import: {import_response.get('data', {}).get('detail', 'Unknown error')}")
        except Exception as e:
            st.error(f"❌ Import error: {str(e)}")
            logger.error(f"Import error: {str(e)}")
