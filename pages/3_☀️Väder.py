import os
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium
from datetime import datetime
from google.oauth2 import service_account
from google.cloud import bigquery
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd
from datetime import datetime


credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

client = bigquery.Client(credentials=credentials, project=credentials.project_id)


@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def count_trafikolycka(city_name):
    query = f"""
    SELECT COUNT(*) AS trafikolycka_count
    FROM `crime-in-sweden-project.Crime_in_Sweden.unique_events`
    WHERE name = 'Trafikolycka' AND location_name = '{city_name}'
    """
    query_job = client.query(query)
    results = query_job.result()
    for row in results:
        return row["trafikolycka_count"]
    return 0


@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def count_trafikolycka_all():
    query = f"""
    SELECT COUNT(*) AS trafikolycka_count_all
    FROM `crime-in-sweden-project.Crime_in_Sweden.unique_events`
    WHERE name = 'Trafikolycka'
    """
    query_job = client.query(query)
    results = query_job.result()
    for row in results:
        return row["trafikolycka_count_all"]
    return 0


@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def get_top_5_trafikolycka():
    query = """
    SELECT location_name, COUNT(*) AS trafikolycka_count
    FROM `crime-in-sweden-project.Crime_in_Sweden.unique_events`
    WHERE name = 'Trafikolycka'
    GROUP BY location_name
    ORDER BY trafikolycka_count DESC
    LIMIT 5
    """
    query_job = client.query(query)
    results = query_job.result()
    cities = []
    counts = []
    for row in results:
        cities.append(row["location_name"])
        counts.append(row["trafikolycka_count"])
    return cities, counts


@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def get_main_cities_from_bigquery():
    query = """
    SELECT DISTINCT location_name, latitude, longitude
    FROM `crime-in-sweden-project.Crime_in_Sweden.unique_events`
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """
    query_job = client.query(query)
    results = query_job.result()

    main_cities = {}
    for row in results:
        main_cities[row["location_name"]] = (row["latitude"], row["longitude"])

    return main_cities


main_cities = get_main_cities_from_bigquery()


@st.cache_data(ttl=3600)  # Cache the result for 1 hour
def fetch_weather_data(latitude, longitude):
    api_url = f"https://opendata-download-metanalys.smhi.se/api/category/mesan2g/version/1/geotype/point/lon/{longitude}/lat/{latitude}/data.json"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(
            f"Failed to fetch data for ({latitude}, {longitude}): {response.status_code} - {response.text}"
        )
        return None


def format_valid_time(valid_time):
    dt = datetime.strptime(valid_time, "%Y-%m-%dT%H:%M:%SZ")
    formatted_date = dt.strftime("%d-%m-%Y")
    formatted_time = dt.strftime("%H:%M")
    return formatted_date, formatted_time


def categorize_weather(temp, wind_gust, precipitation, visibility):
    if temp < -5 or temp > 35 or wind_gust > 25 or precipitation > 5 or visibility < 1:
        return "Dålig"
    elif temp < 0 or wind_gust > 20 or precipitation > 2 or visibility < 2:
        return "Måttlig"
    else:
        return "Bra"


# Streamlit App Title
st.title("Körsäkerhet i Realtid ⚠️ och Väderinsikter 🌤️")

st.sidebar.header("🏙️ Platsval")

select_all = st.sidebar.checkbox(
    "Markera för Alla platser eller Avmarkera för en specifik plats", value=True
)

if select_all:
    selected_cities = list(sorted(main_cities.keys()))

else:
    selected_city = st.sidebar.selectbox(
        "Välj en plats", list(sorted(main_cities.keys()))
    )
    selected_cities = [selected_city]

if select_all:
    trafikolycka_count_all = count_trafikolycka_all()

    st.subheader(
        f"Totalt antal trafikolyckor som rapporterats hittills i alla städer: {trafikolycka_count_all}"
    )
    st.write(
        "För körsäkerhetstips följ denna länk: https://trafiko.se/faktabank/halt-vaglag"
    )

    cities, counts = get_top_5_trafikolycka()

    st.sidebar.header("💥Topp 5 Platser med Flest Olyckor")
    fig, ax = plt.subplots()
    ax.bar(cities, counts, color="skyblue")
    ax.set_xlabel("Plats")
    ax.set_ylabel("Antal Olyckor")

    st.sidebar.pyplot(fig)

# Initialize Folium Map
sweden_map = folium.Map(location=[62, 15], zoom_start=5)

color_mapping = {"Bra": "green", "Måttlig": "yellow", "Dålig": "red"}

for city in selected_cities:
    lat, lon = main_cities[city]
    weather_data = fetch_weather_data(lat, lon)

    if weather_data:
        most_recent_entry = weather_data["timeSeries"][0]
        valid_time = most_recent_entry["validTime"]
        formatted_date, formatted_time = format_valid_time(valid_time)

        temp = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "t"
            ),
            None,
        )
        wind_gust = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "gust"
            ),
            None,
        )
        precipitation = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "prec1h"
            ),
            None,
        )
        snow_precipitation = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "frsn1h"
            ),
            None,
        )
        visibility = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "vis"
            ),
            5,
        )  # Default to 5km if not available
        wind_speed = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "ws"
            ),
            None,
        )
        precip_sort_code = next(
            (
                param["values"][0]
                for param in most_recent_entry["parameters"]
                if param["name"] == "prsort"
            ),
            None,
        )

        # Convert precipitation type code to descriptive name
        precip_sort = {
            0: "Ingen nederbörd",
            1: "Snö",
            2: "Snö och regn",
            3: "Regn",
            4: "Duggregn",
            5: "Underkylt regn",
            6: "Underkylt duggregn",
        }
        precip_sort = precip_sort.get(precip_sort_code, "Unknown")

        # Categorize weather conditions
        condition = categorize_weather(
            temp if temp is not None else 0,
            wind_gust if wind_gust is not None else 0,
            precipitation if precipitation is not None else 0,
            visibility,
        )

        color = color_mapping.get(condition, "gray")

        # Define the popup content conditionally
        popup_content = None
        if select_all:
            popup_content = folium.Popup(
                f"""Stad 🏙️: {city} 
            Körsäkerhet 🚗: {condition} 
            Temp 🌡️: {temp}°C 
            Nederbörd 🌧️: {precipitation}mm 
            Snö ❄️: {snow_precipitation}mm 
            Synlighet 👁️: {visibility}km""",
                parse_html=True,
            )

        folium.CircleMarker(
            location=(lat, lon),
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.6,
            popup=popup_content,
        ).add_to(sweden_map)

    if not select_all:

        st.markdown(
            f"""
                 <style>
                .container {{
                 padding: 10px;
                 border: 1px solid #ddd;
                 border-radius: 5px;
                 margin-bottom: 10px;
                 }}
                 .small-font {{
                 font-size: 28px !important;
                 }}
                 </style>
                 """,
            unsafe_allow_html=True,
        )

        # If a single city is selected, display the traffic incident count below the map
        if not select_all:
            trafikolycka_count = count_trafikolycka(selected_city)

        st.subheader(f"🏙️ Plats: {city} ")
        st.subheader(f"💥 Antal olyckor rapporterade hittills: {trafikolycka_count} ")

        # First row: 3 columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong> 📅 Datum & Tid</strong>
                    <div class='small-font'>{formatted_date}, {formatted_time}</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
                     <div class='container'>
                     <strong>🌡️ Temperatur</strong>
                     <div class='small-font'>{temp} °C</div>
                     </div>
                     """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>💨 Vindby</strong>
                    <div class='small-font'>{wind_gust} m/s</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        # Second row: 3 columns
        col1_1, col2_1, col3_1 = st.columns(3)

        with col1_1:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>🌧️ Nederbörd</strong>
                    <div class='small-font'>{precipitation} mm</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        with col2_1:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>❄️ Snö</strong>
                    <div class='small-font'>{snow_precipitation} mm</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        with col3_1:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>👁️ Synlighet</strong>
                    <div class='small-font'>{visibility} km</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        # Third row: 3 columns
        col1_2, col2_2, col3_2 = st.columns(3)

        with col1_2:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>🌬️ Vindhastighet</strong>
                    <div class='small-font'>{wind_speed} m/s</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        with col2_2:
            st.markdown(
                f"""
                    <div class='container'>
                    <strong>☂️ Nederbördssortering</strong>
                    <div class='small-font'>{precip_sort}</div>
                    </div>
                    """,
                unsafe_allow_html=True,
            )

        with col3_2:
            # Use thumbs up for good condition, thumbs down for bad
            condition_symbol = (
                "👍" if condition == "Bra" else "👎" if condition == "Dålig" else "⚖️"
            )
            st.markdown(
                f"""
             <div class='container'>
             <strong>🚗 Körsäkerhet</strong>
             <div class='small-font'>{condition_symbol} {condition}</div>
             </div>
             """,
                unsafe_allow_html=True,
            )


# Add a legend to the map
legend_html = """
<div style="
    position: fixed; 
    bottom: 10px; left: 50px; width: 150px; height: 110px; 
    border:2px solid grey; z-index:9999; font-size:14px;
    background-color:white; padding: 10px; border-radius: 5px;">
    &nbsp; <b>Weather Condition</b><br>
    &nbsp; <i style="color:green;">&#9679;</i>&nbsp; Good<br>
    &nbsp; <i style="color:yellow;">&#9679;</i>&nbsp; Moderate<br>
    &nbsp; <i style="color:red;">&#9679;</i>&nbsp; Bad<br>
</div>
"""
sweden_map.get_root().html.add_child(folium.Element(legend_html))

# Display the map in Streamlit
st_folium(sweden_map, width=800, height=500)


# Helper function to load comments from a CSV file
def load_comments():
    try:
        return pd.read_csv("comments.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Namn", "Plats", "Datum & Tid", "Uppdatering"])


# Helper function to save comments to a CSV file
def save_comments(df):
    df.to_csv("comments.csv", index=False)


# Load existing comments from the CSV file
if "comments" not in st.session_state:
    st.session_state.comments = load_comments()

# Title for Community Reports Section
st.header("🔴 Live Trafikuppdateringar")
st.write(
    "💬 Dela en uppdatering om aktuella trafik- eller körsäkerhetsförhållanden. Observera: Detta avsnitt är avsett för passagerare eller individer som inte längre kör bil."
)

# Input fields for name, location, and comment
name = st.text_input("Ditt Namn:")
location = st.selectbox("Din Plats:", list(sorted(main_cities.keys())))
comment = st.text_area("Uppdatering:")

# Input fields for date and time
date = st.date_input("Datum:", value=datetime.today())
time = st.time_input("Tid:", value=datetime.now().time())

# Submit button
if st.button("Skicka in rapport"):
    if name and location and comment:
        # Combine date and time into a single datetime column
        datetime_str = datetime.combine(date, time).strftime("%Y-%m-%d %H:%M")
        # Append new comment to the DataFrame
        new_comment = pd.DataFrame(
            {
                "Namn": [name],
                "Plats": [location],
                "Datum & Tid": [datetime_str],
                "Uppdatering": [comment],
            }
        )
        st.session_state.comments = pd.concat(
            [st.session_state.comments, new_comment], ignore_index=True
        )

        # Save comments to the CSV file
        save_comments(st.session_state.comments)

        st.success("Din rapport har skickats!")
    else:
        st.error("Vänligen fyll i alla fält.")

# Display all submitted comments
if not st.session_state.comments.empty:
    st.subheader("📑Inlämnade Rapporter")

    # Add a selectbox for filtering comments by location (with all cities)
    filter_location = st.selectbox(
        "Filtrera efter plats:", ["Alla"] + list(sorted(main_cities.keys()))
    )

    # Filter comments based on selected location
    if filter_location != "Alla":
        filtered_comments = st.session_state.comments[
            st.session_state.comments["Plats"] == filter_location
        ]
    else:
        filtered_comments = st.session_state.comments

    # Check if there are comments for the selected location
    if filtered_comments.empty:
        st.info(f"Inga uppdateringar för {filter_location}.")
    else:
        # Display filtered comments without the index
        st.write(filtered_comments.to_html(index=False), unsafe_allow_html=True)
