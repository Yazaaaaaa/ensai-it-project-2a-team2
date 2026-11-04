"""
Streamlit main page with a dashboord.

Provides options to see an overview of favorites neos, alerts,...

Endpoints used:
    ?
"""

import json
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="Neo-watch", page_icon="🌠", layout="centered")
st.title("Dashboard")

BACKEND_URL = "http://localhost:5000"


# Functions to import data from backend
@st.cache_data(ttl=300)
def fetch_neos():
    """Get all Neos from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/neo/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed for getting data: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_close_approaches(neo_id):
    """Get near Neos from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/neo/{neo_id}/approaches")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return []

@st.cache_data(ttl=300)
def fetch_user_connections(user_id):
    """Get user's connection history"""
    try:
        response = requests.get(f"{BACKEND_URL}/connections/users/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return []


tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "⭐ Favorites", "🚨 Alerts", "➕ Add a NEO", "🔍 Browse a NEO"])

# ============ OVERVIEW ============
with tab1:
    st.header("📊 Overview")
    neos = fetch_neos()

    if not neos:
        st.warning("No NEOs in database")
    else:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Number of NEOs", len(neos))

        with col2:
            hazardous_count = sum(1 for neo in neos if neo.get("is_hazardous"))
            st.metric("Hazardous NEOs ", hazardous_count, delta="High risk" if hazardous_count > 0 else None)

        with col3:
            custom_count = sum(1 for neo in neos if neo.get("is_custom"))
            st.metric("custom NEOs", custom_count)

        with col4:
            avg_diameter = sum(
                (neo.get("diameter_min_m", 0) + neo.get("diameter_max_m", 0)) / 2
                for neo in neos if neo.get("diameter_min_m") and neo.get("diameter_max_m")
            ) / len(neos) if neos else 0
            st.metric("Average diameter", f"{avg_diameter:.0f} m")

        st.markdown("---")

        # Graphs
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Breakdown by level of hazard")
            hazard_data = pd.DataFrame({
                "Type": ["Hazardous", "Non hazardous"],
                "Count": [hazardous_count, len(neos) - hazardous_count]
            })
            fig = px.pie(hazard_data, values="Count", names="Type", color_discrete_sequence=["#50C878", "#FF4500"])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Breakdown by size (average diameter)")
            # Filter NEOs using diameter data
            diameter_data = []
            for neo in neos:
                if neo.get("diameter_min_m") and neo.get("diameter_max_m"):
                    diameter_data.append({
                        "name": neo.get("name_neo", "Unknown"),
                        "diameter": (neo["diameter_min_m"] + neo["diameter_max_m"]) / 2
                    })
            if diameter_data:
                df_diameter = pd.DataFrame(diameter_data)
                fig = px.bar(df_diameter.sort_values("diameter", ascending=False).head(10),
                             x="name", y="diameter",
                             title="Top 10 NEOs by diameter",
                             labels={"diameter": "Average diameter (m)", "name": "NEO"})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No diameter data available")

        st.markdown("---")

        # List of NEOs with filters
        st.subheader("🔭 List of NEOs")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_hazardous = st.checkbox("Hazardous", value=False)
        with col2:
            filter_custom = st.checkbox("Custom", value=False)
        with col3:
            sort_by = st.selectbox("Sort by", ["Name", "Diameter", "Hazard level"])

        # Appliquer les filtres
        filtered_neos = neos
        if filter_hazardous:
            filtered_neos = [neo for neo in filtered_neos if neo.get("is_hazardous")]
        if filter_custom:
            filtered_neos = [neo for neo in filtered_neos if neo.get("is_custom")]

        # Trier
        if sort_by == "Name":
            filtered_neos = sorted(filtered_neos, key=lambda x: x.get("name_neo", ""))
        elif sort_by == "Diameter":
            filtered_neos = sorted(filtered_neos, key=lambda x: (x.get("diameter_min_m", 0) + x.get("diameter_max_m", 0)) / 2, reverse=True)
        elif sort_by == "Hazard level":
            filtered_neos = sorted(filtered_neos, key=lambda x: x.get("is_hazardous", False), reverse=True)

        # Display in a DataFrame
        if filtered_neos:
            df = pd.DataFrame(filtered_neos)
            display_columns = ["id_neo", "nasa_id", "name_neo", "diameter_min_m", "diameter_max_m", "is_hazardous", "is_custom"]
            available_columns = [col for col in display_columns if col in df.columns]
            st.dataframe(df[available_columns], use_container_width=True)
        else:
            st.info("No NEO find for your search criteria")

with tab2:
    st.header("⭐ Favorites")
    st.info("🚧 Fonctionnalité à implémenter: Intégration avec l'endpoint /favorites de votre backend")

    # Exemple de structure pour plus tard
    # favorites = fetch_favorites(st.session_state["user"]["id_user"])
    # if favorites:
    #     st.dataframe(pd.DataFrame(favorites))
    # else:
    #     st.info("Vous n'avez aucun NEO en favoris.")

# ============ ALERTS ============
with tab3:
    st.header("🚨 Alerts")
    st.info("🚧 Fonctionnalité à implémenter: Afficher les NEOs avec des approches proches")

    # Exemple: Récupérer les NEOs avec des approches dans les 30 jours
    # close_approaches = []
    # for neo in fetch_neos():
    #     approaches = fetch_close_approaches(neo["id_neo"])
    #     for approach in approaches:
    #         approach_date = datetime.strptime(approach["approach_date"], "%Y-%m-%d")
    #         if (approach_date - datetime.now()).days <= 30:
    #             close_approaches.append({**neo, **approach})

    # if close_approaches:
    #     df = pd.DataFrame(close_approaches)
    #     st.dataframe(df)
    # else:
    #     st.success("✅ Aucune alerte pour les 30 prochains jours")

# ============ ONGLET 4: ADD A NEO ============
with tab4:
    st.header("➕ Add a NEO")

    with st.form("add_neo_form"):
        col1, col2 = st.columns(2)

        with col1:
            name_neo = st.text_input("Nom du NEO *", key="name_neo")
            nasa_id = st.text_input("NASA ID", key="nasa_id")
            is_hazardous = st.checkbox("Est dangereux", value=False)
            is_custom = st.checkbox("Personnalisé", value=True)

        with col2:
            diameter_min = st.number_input("Diamètre min (m)", min_value=0.0, value=0.0)
            diameter_max = st.number_input("Diamètre max (m)", min_value=0.0, value=0.0)
            magnitude = st.number_input("Magnitude absolue", min_value=0.0, value=0.0)
            created_by = st.number_input("Créé par (ID utilisateur)",
                                         value=st.session_state["user"]["id_user"],
                                         disabled=True)

        submit_button = st.form_submit_button("Ajouter le NEO")

        if submit_button:
            if not name_neo:
                st.error("Le nom du NEO est obligatoire !")
            else:
                new_neo = {
                    "name_neo": name_neo,
                    "nasa_id": nasa_id,
                    "diameter_min_m": diameter_min,
                    "diameter_max_m": diameter_max,
                    "absolute_magnitude": magnitude,
                    "is_hazardous": is_hazardous,
                    "is_custom": is_custom,
                    "created_by_user_id": created_by
                }

                try:
                    response = requests.post(f"{BACKEND_URL}/neo/", json=new_neo)
                    if response.status_code == 201:
                        st.success("✅ NEO ajouté avec succès !")
                        st.experimental_rerun()  # Rafraîchir pour voir le nouveau NEO
                    else:
                        st.error(f"❌ Erreur: {response.text}")
                except Exception as e:
                    st.error(f"Erreur lors de l'ajout: {e}")

# ============ ONGLET 5: BROWSE A NEO ============
with tab5:
    st.header("🔍 Browse a NEO")

    # Sélection d'un NEO
    neos = fetch_neos()
    if not neos:
        st.warning("Aucun NEO disponible.")
    else:
        neo_names = [f"{neo.get('name_neo', 'Inconnu')} (ID: {neo.get('id_neo')})" for neo in neos]
        selected_neo_name = st.selectbox("Sélectionnez un NEO", neo_names)

        if selected_neo_name:
            # Extraire l'ID du NEO sélectionné
            selected_neo_id = int(selected_neo_name.split("ID: ")[1].rstrip(")"))

            # Trouver le NEO correspondant
            selected_neo = next((neo for neo in neos if neo["id_neo"] == selected_neo_id), None)

            if selected_neo:
                st.markdown("---")
                st.subheader(f"🪐 {selected_neo.get('name_neo', 'NEO')}")

                # Afficher les informations du NEO
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("NASA ID", selected_neo.get("nasa_id", "N/A"))
                    st.metric("Diamètre min", f"{selected_neo.get('diameter_min_m', 0)} m")
                    st.metric("Est dangereux", "✅ Oui" if selected_neo.get("is_hazardous") else "❌ Non")

                with col2:
                    st.metric("Diamètre max", f"{selected_neo.get('diameter_max_m', 0)} m")
                    st.metric("Magnitude", selected_neo.get("absolute_magnitude", "N/A"))
                    st.metric("Personnalisé", "✅ Oui" if selected_neo.get("is_custom") else "❌ Non")

                with col3:
                    if selected_neo.get("created_by_user_id"):
                        st.metric("Créé par", selected_neo["created_by_user_id"])

                st.markdown("---")

                # Récupérer les approches proches
                st.subheader("📅 Approches proches")
                approaches = fetch_close_approaches(selected_neo_id)

                if approaches:
                    df_approaches = pd.DataFrame(approaches)
                    if "approach_date" in df_approaches.columns:
                        df_approaches["approach_date"] = pd.to_datetime(df_approaches["approach_date"])
                        df_approaches = df_approaches.sort_values("approach_date")
                        st.dataframe(df_approaches, use_container_width=True)

                        # Graphique des distances
                        if "miss_distance_km" in df_approaches.columns:
                            fig = px.line(df_approaches, x="approach_date", y="miss_distance_km",
                                          title="Distance de passage au fil du temps",
                                          labels={"miss_distance_km": "Distance (km)", "approach_date": "Date"})
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.json(approaches)
                else:
                    st.info("Aucune approche proche enregistrée pour ce NEO.")
