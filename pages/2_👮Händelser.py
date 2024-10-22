import os
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyecharts.charts import Bar, Line
from pyecharts import options as opts
from streamlit_echarts import st_pyecharts
from pyecharts.commons.utils import JsCode

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

client = bigquery.Client(credentials=credentials, project=credentials.project_id)

st.set_page_config(layout="wide")

st.header("Händelser i Sverige rapporterade av Polisen 👮‍♂️")
st.write(
    """
            Få mer insikt genom att klicka på markören!
            """
)

query = """
SELECT
    location_name,
    name,
    summary,
    date,
    time,
    latitude,
    longitude
FROM
    `crime-in-sweden-project.Crime_in_Sweden.unique_events`
"""

df = client.query(query).to_dataframe()


def categorize_event(event_type):
    trafik = [
        "Trafikbrott",
        "Trafikhinder",
        "Trafikkontroll",
        "Trafikolycka",
        "Trafikolycka, personskada",
        "Trafikolycka, singel",
        "Trafikolycka, smitning från",
        "Trafikolycka, vilt",
        "Rattfylleri",
    ]
    explosion = ["Bombhot", "Detonation", "Explosion"]
    ran_stold = [
        "Inbrott",
        "Inbrott, försök",
        "Häleri",
        "Motorfordon, anträffat stulet",
        "Motorfordon, stöld",
        "Stöld",
        "Stöld, försök",
        "Stöld, ringa",
        "Stöld/inbrott",
        "Rån",
        "Rån väpnat",
        "Rån övrigt",
        "Rån, försök",
    ]
    skottlossning = ["Skottlossning", "Skottlossning, misstänkt"]
    vald = [
        "Bråk",
        "Misshandel",
        "Misshandel, grov",
        "Mord/dråp",
        "Mord/dråp, försök",
        "Olaga hot",
        "Våld/hot mot tjänsteman",
        "Våldtäkt",
        "Våldtäkt, försök",
    ]
    brand = ["Brand", "Brand automatlarm"]

    if event_type in trafik:
        return "Trafik"
    elif event_type in explosion:
        return "Explosion"
    elif event_type in ran_stold:
        return "Rån och Stöld"
    elif event_type in skottlossning:
        return "Skottlossning"
    elif event_type in vald:
        return "Våld"
    elif event_type in brand:
        return "Brand"
    else:
        return "Annat"


df["main_categories"] = df["name"].apply(categorize_event)

st.sidebar.header("Filtrera")

# Select category
selected_category = st.sidebar.selectbox(
    "Välj händelsekategori",
    options=["Alla"] + sorted(df["main_categories"].unique()),
    index=0,
)

# Select location
selected_location = st.sidebar.selectbox(
    "Välj plats",
    options=["Alla"] + sorted(df["location_name"].unique()),
    index=0,
)

with st.sidebar.expander("Välj period"):
    start_date = st.date_input("Startdatum", value=pd.to_datetime(df["date"].min()))
    end_date = st.date_input("Slutdatum", value=pd.to_datetime(df["date"].max()))

filtered_df = df[
    ((df["main_categories"] == selected_category) | (selected_category == "Alla"))
    & ((df["location_name"] == selected_location) | (selected_location == "Alla"))
    & (df["date"] >= start_date)
    & (df["date"] <= end_date)
]

filtered_map = folium.Map(location=[61.0, 15.0], zoom_start=5)

icon_mapping = {
    "Trafik": ("car", "blue"),
    "Brand": ("fire", "red"),
    "Rån och Stöld": ("lock", "orange"),
    "Våld": ("skull-crossbones", "black"),
    "Skottlossning": ("crosshairs", "gray"),
    "Explosion": ("bomb", "orange"),
    "Ovrigt": None,
}

if "clicked_location" not in st.session_state:
    st.session_state["clicked_location"] = None

event_counts = (
    filtered_df.groupby(["latitude", "longitude"]).size().reset_index(name="count")
)

for _, row in event_counts.iterrows():
    count = int(row["count"])
    lat = row["latitude"]
    lon = row["longitude"]

    event_category = filtered_df[
        (filtered_df["latitude"] == lat) & (filtered_df["longitude"] == lon)
    ]["main_categories"].values[0]
    icon_name, icon_color = icon_mapping.get(event_category, ("info-circle", "green"))

    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(icon=icon_name, prefix="fa", color=icon_color),
        tooltip=f"Antal: {count}",
    ).add_to(filtered_map)

clicked_data = st_folium(filtered_map, width=1000, height=700)

if clicked_data and clicked_data["last_object_clicked"]:
    clicked_lat = clicked_data["last_object_clicked"]["lat"]
    clicked_lon = clicked_data["last_object_clicked"]["lng"]

    events_at_location = filtered_df[
        (filtered_df["latitude"] == clicked_lat)
        & (filtered_df["longitude"] == clicked_lon)
    ]

    if not events_at_location.empty:
        events_at_location = events_at_location.sort_values(by="date", ascending=False)

        st.sidebar.subheader("Information")
        for _, event in events_at_location.iterrows():
            st.sidebar.markdown(
                f"""
            <div style="width: 200px; white-space: normal; margin-bottom: 10px;">
                <strong>Län:</strong> {event['location_name']}<br>
                <strong>Händelse:</strong> {event['name']}<br>
                <strong>Datum:</strong> {event['date']}<br>
                <strong>Tid:</strong> {event['time']}<br>
                {event['summary']}<br>
            </div>
            <hr style="border: 1px solid #ccc;">
            """,
                unsafe_allow_html=True,
            )
