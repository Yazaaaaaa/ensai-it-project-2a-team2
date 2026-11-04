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


if "user" not in st.session_state:
    st.warning("Please log in first.")
    st.stop()

USER_ID = st.session_state["user"]["id_user"]
BACKEND_URL = "http://localhost:5000"
NEO_URL = "/neo"
FAVORITES_URL = "/favorite"
ALERTS_URL = "/alert"


def api(method: str, path: str, **kwargs):
    """Calls the backend with the user's token. Returns None if it is unreachable."""
    token = st.session_state.get("access_token")
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        return requests.request(
            method, f"{BACKEND_URL}{path}", headers=headers, timeout=15, **kwargs
        )
    except requests.exceptions.RequestException as e:
        st.error(f"Backend unreachable: {e}")
        return None


def error_detail(response) -> str:
    try:
        return str(response.json().get("detail", response.text))
    except ValueError:
        return response.text


def get_json(path: str, default, **kwargs):
    """GET returning the JSON body, or `default` after displaying the error."""
    response = api("GET", path, **kwargs)
    if response is None:
        return default
    if response.status_code != 200:
        st.error(f"Error {response.status_code}: {error_detail(response)}")
        return default
    return response.json()


def mutate(method: str, path: str, ok_status: int, message: str, **kwargs):
    """POST/PATCH/DELETE. On success: remember a message and reload the page."""
    response = api(method, path, **kwargs)
    if response is None:
        return
    if response.status_code == ok_status:
        st.session_state["flash"] = message
        st.rerun()
    st.error(f"Error {response.status_code}: {error_detail(response)}")


@st.cache_data(ttl=60)
def search_neos(params: dict, sort_by: str | None, descending: bool):
    query = {**params, "descending": str(descending).lower()}
    if sort_by:
        query["sort_by"] = sort_by
    return get_json(NEO_URL, [], params=query)


@st.cache_data(ttl=300)
def fetch_close_approaches(neo_id):
    return get_json(f"{NEO_URL}/{neo_id}/close-approaches", [])


@st.cache_data(ttl=300)
def fetch_chart(user_id: int, id_neo: int, orbiting_body: str) -> bytes | None:
    # user_id is only part of the cache key: the route depends on the authenticated user
    response = api(
        "GET",
        f"{FAVORITES_URL}/{id_neo}/distances/chart",
        params={"orbiting_body": orbiting_body},
    )
    return response.content if response is not None and response.status_code == 200 else None


def alert_form(key: str, id_neo: int | None):
    """Form creating an alert. id_neo=None creates an alert on any NEO."""
    with st.form(key):
        c1, c2 = st.columns(2)
        threshold_km = c1.number_input(
            "Passes closer than (km)",
            min_value=1.0, value=5_000_000.0, step=100_000.0, format="%.0f",
        )
        size = c2.number_input(
            "Larger than (m, 0 = any size)", min_value=0.0, value=0.0, step=10.0,
        )
        if st.form_submit_button("Create alert"):
            mutate(
                "POST", ALERTS_URL, 201, "Alert created",
                json={
                    "id_user": USER_ID,
                    "id_neo": id_neo,
                    "threshold_km": threshold_km,
                    "threshold_size": size or None,
                    "is_active": True,
                },
            )


# Data loaded once per run, shared by the tabs
favorites = get_json(f"{FAVORITES_URL}/{USER_ID}", [])
alerts = get_json(f"{ALERTS_URL}/{USER_ID}", [])
triggered = get_json(f"{ALERTS_URL}/{USER_ID}/triggered", [])
favorite_ids = {f["id_neo"] for f in favorites}
favorite_labels = {
    f["id_neo"]: f"{f['neo']['name_neo']} (ID {f['id_neo']})" for f in favorites
}

if "flash" in st.session_state:
    st.toast(st.session_state.pop("flash"))

# F6: notification when the user logs in (once per session), banner afterwards
token = st.session_state.get("access_token")
if triggered:
    if st.session_state.get("notified_for") != token:
        st.toast(f"{len(triggered)} alert(s) triggered", icon="🚨")
        st.session_state["notified_for"] = token
    st.warning(
        f"🚨 {len(triggered)} upcoming close approach(es) trigger one of your alerts. "
        "See the Alerts tab."
    )


def mean_diameter(neo: dict) -> float | None:
    low, high = neo.get("diameter_min_m"), neo.get("diameter_max_m")
    return (low + high) / 2 if low and high else None


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Overview", "⭐ Favorites", "🚨 Alerts", "➕ Add a NEO", "🔍 Browse a NEO"]
)

# ============ OVERVIEW ============
with tab1:
    st.header("📊 Overview")
    neos = fetch_neos()

    if not neos:
        st.warning("No NEOs in database")
    else:
        diameters = [d for d in map(mean_diameter, neos) if d is not None]
        hazardous_count = sum(1 for n in neos if n.get("is_hazardous"))
        custom_count = sum(1 for n in neos if n.get("is_custom"))
        avg_diameter = sum(diameters) / len(diameters) if diameters else 0

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

        filtered_neos = neos
        if filter_hazardous:
            filtered_neos = [n for n in filtered_neos if n.get("is_hazardous")]
        if filter_custom:
            filtered_neos = [n for n in filtered_neos if n.get("is_custom")]

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
    if not favorites:
        st.info("You have no favorite NEO yet. Add some from the 'Browse a NEO' tab.")
    else:
        st.dataframe(
            pd.DataFrame([{
                "id_neo": f["id_neo"],
                "name": f["neo"]["name_neo"],
                "diameter_min_m": f["neo"]["diameter_min_m"],
                "diameter_max_m": f["neo"]["diameter_max_m"],
                "hazardous": f["neo"]["is_hazardous"],
                "added_at": f["added_at"],
            } for f in favorites]),
            hide_index=True, width="stretch",
        )

        id_neo = st.selectbox(
            "Select a favorite", list(favorite_labels),
            format_func=favorite_labels.get, key="selected_favorite",
        )
        if st.button("Remove from favorites"):
            mutate("DELETE", f"{FAVORITES_URL}/{USER_ID}/{id_neo}", 204, "Removed from favorites")

        st.subheader("📈 Distance over time")
        body = st.text_input("Orbiting body (empty = all bodies)", value="Earth", key="distance_body")
        history = get_json(f"{FAVORITES_URL}/{id_neo}/distances", None, params={"orbiting_body": body})

        if history and history["points"]:
            closest = history["closest"]
            st.metric(
                "Closest approach", f"{closest['miss_distance_km']:,.0f} km",
                help=f"On {closest['date'][:10]}",
            )
            png = fetch_chart(USER_ID, id_neo, body)
            if png:
                st.image(png, width="stretch")
                st.download_button(
                    "Download the chart (PNG)", data=png,
                    file_name=f"neo_{id_neo}_distances.png", mime="image/png",
                )
            with st.expander("Data"):
                st.dataframe(pd.DataFrame(history["points"]), hide_index=True, width="stretch")
        elif history is not None:
            st.info("No close approach recorded for this NEO.")

        st.subheader("🚨 Alert on this NEO")
        alert_form(f"alert_form_fav_{id_neo}", id_neo)

with tab3:
    st.header("🚨 Alerts")

    st.subheader("Triggered alerts")
    if triggered:
        st.dataframe(
            pd.DataFrame([{
                "NEO": t["neo"]["name_neo"],
                "approach_date": t["close_approach"]["approach_date"],
                "miss_distance_km": t["close_approach"]["miss_distance_km"],
                "velocity_kmh": t["close_approach"]["relative_velocity_kmh"],
                "diameter_max_m": t["neo"]["diameter_max_m"],
                "threshold_km": t["alert"]["threshold_km"],
                "threshold_size_m": t["alert"]["threshold_size"],
            } for t in triggered]),
            hide_index=True, width="stretch",
        )
    else:
        st.success("✅ No alert triggered")

    st.subheader("My alerts")
    if not alerts:
        st.info("You have no alert yet.")
    for a in alerts:
        neo = a.get("neo")
        condition = f"closer than {a['threshold_km']:,.0f} km"
        if a.get("threshold_size"):
            condition += f", larger than {a['threshold_size']:,.0f} m"

        c1, c2, c3, c4 = st.columns([3, 4, 1, 1])
        c1.write(f"**{neo['name_neo'] if neo else 'Any NEO'}**")
        c2.write(condition)
        active = c3.toggle(
            "Active", value=a["is_active"], key=f"active_{a['id_alert']}",
            label_visibility="collapsed",
        )
        if active != a["is_active"]:
            mutate("PATCH", f"{ALERTS_URL}/{USER_ID}/{a['id_alert']}", 200,
                   "Alert updated", json={"is_active": active})
        if c4.button("🗑️", key=f"delete_{a['id_alert']}"):
            mutate("DELETE", f"{ALERTS_URL}/{USER_ID}/{a['id_alert']}", 204, "Alert deleted")

    st.subheader("New alert")
    watch_options = [None, *favorite_labels]
    watched = st.selectbox(
        "NEO to watch", watch_options,
        format_func=lambda i: "Any NEO" if i is None else favorite_labels[i],
        key="alert_neo",
    )
    alert_form("alert_form_tab", watched)


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

    with st.form("search_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Name contains")
            hazardous = st.selectbox("Hazardous", ["Any", "Yes", "No"])
            body = st.text_input("Orbiting body (case-sensitive, e.g. Earth)")
            approach_date = st.text_input("Approach date (YYYY-MM-DD)")
        with c2:
            min_d = st.number_input("Min mean diameter (m)", min_value=0.0, value=0.0)
            max_d = st.number_input("Max mean diameter (m, 0 = no limit)", min_value=0.0, value=0.0)
            max_mag = st.number_input("Max absolute magnitude (0 = no limit)", min_value=0.0, value=0.0)
        with c3:
            sort_choice = st.selectbox("Sort by", ["name", "diameter", "magnitude", "hazardous", "(none)"])
            descending = st.checkbox("Descending")
            mine = st.checkbox("Only the NEOs I created")
        submitted = st.form_submit_button("Search")

    if submitted:
        params = {}
        if name:
            params["name"] = name
        if hazardous != "Any":
            params["is_hazardous"] = str(hazardous == "Yes").lower()
        if body:
            params["orbiting_body"] = body
        if approach_date:
            params["approach_date"] = approach_date
        if min_d > 0:
            params["min_diameter_m"] = min_d
        if max_d > 0:
            params["max_diameter_m"] = max_d
        if max_mag > 0:
            params["max_magnitude"] = max_mag
        if mine:
            params["user_id"] = USER_ID
        st.session_state["search"] = {
            "params": params,
            "sort_by": None if sort_choice == "(none)" else sort_choice,
            "descending": descending,
        }

    search = st.session_state.get(
        "search", {"params": {}, "sort_by": "name", "descending": False}
    )
    found = search_neos(search["params"], search["sort_by"], search["descending"])
    st.caption(f"{len(found)} NEO(s) found - click a row to see its details")

    if found:
        columns = ["id_neo", "nasa_id", "name_neo", "diameter_min_m", "diameter_max_m",
                   "absolute_magnitude", "is_hazardous", "is_custom"]
        event = st.dataframe(
            pd.DataFrame(found)[columns], hide_index=True, width="stretch",
            on_select="rerun", selection_mode="single-row", key="neo_table",
        )
        rows = event.selection.rows
        if rows:
            neo = found[rows[0]]
            st.subheader(f"🪐 {neo['name_neo']}")

            if neo["id_neo"] in favorite_ids:
                st.success("⭐ Already in your favorites")
            elif st.button("⭐ Add to favorites"):
                mutate("POST", FAVORITES_URL, 201, "Added to favorites",
                       json={"id_user": USER_ID, "id_neo": neo["id_neo"]})

            m1, m2, m3 = st.columns(3)
            m1.metric("Min diameter", f"{neo['diameter_min_m']} m")
            m2.metric("Max diameter", f"{neo['diameter_max_m']} m")
            m3.metric("Hazardous", "✅ Yes" if neo["is_hazardous"] else "❌ No")

            st.subheader("📅 Close approaches")
            approaches = fetch_close_approaches(neo["id_neo"])
            if approaches:
                df_a = pd.DataFrame(approaches)
                df_a["approach_date"] = pd.to_datetime(df_a["approach_date"])
                df_a = df_a.sort_values("approach_date")
                st.dataframe(df_a, hide_index=True, width="stretch")
                st.plotly_chart(
                    px.line(df_a, x="approach_date", y="miss_distance_km",
                            title="Miss distance over time",
                            labels={"miss_distance_km": "Distance (km)", "approach_date": "Date"}),
                    width="stretch",
                )
            else:
                st.info("No close approach recorded for this NEO.")