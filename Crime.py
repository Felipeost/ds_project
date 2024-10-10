import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import folium
from streamlit_folium import st_folium

# Load credentials from the JSON key file
credentials = service_account.Credentials.from_service_account_file(
    r"C:\Users\lalka\OneDrive\Skrivbord\Studier\Projekt\working repo\ds_project\crime-in-sweden-project-47eef163c346.json"
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Create tabs
tabs = st.tabs(["Händelser", "Väder"])

# Crime Tab
with tabs[0]:
    st.header("Händelser i Sverige rapporterade av Polisen")
    
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
            'Trafikbrott', 'Trafikhinder', 'Trafikkontroll', 'Trafikolycka', 
            'Trafikolycka, personskada', 'Trafikolycka, singel', 
            'Trafikolycka, smitning från', 'Trafikolycka, vilt', 'Rattfylleri'
        ]
        explosion = ['Bombhot', 'Detonation', 'Explosion']
        ran_stold = [
            'Inbrott', 'Inbrott, försök', 'Häleri', 'Motorfordon, anträffat stulet', 
            'Motorfordon, stöld', 'Stöld', 'Stöld, försök', 'Stöld, ringa', 
            'Stöld/inbrott', 'Rån', 'Rån väpnat', 'Rån övrigt', 'Rån, försök'
        ]
        skottlossning = ['Skottlossning', 'Skottlossning, misstänkt']
        vald = [
            'Bråk', 'Misshandel', 'Misshandel, grov', 'Mord/dråp', 
            'Mord/dråp, försök', 'Olaga hot', 'Våld/hot mot tjänsteman', 
            'Våldtäkt', 'Våldtäkt, försök'
        ]
        brand = ['Brand', 'Brand automatlarm']

        if event_type in trafik:
            return 'Trafik'
        elif event_type in explosion:
            return 'Explosion'
        elif event_type in ran_stold:
            return 'Rån och Stöld'
        elif event_type in skottlossning:
            return 'Skottlossning'
        elif event_type in vald:
            return 'Våld'
        elif event_type in brand:
            return 'Brand'
        else:
            return 'Annat'

    df['main_categories'] = df['name'].apply(categorize_event)
    
    st.sidebar.header("Filtrera")
    
    with st.sidebar.expander("Välj händelsekategori"):
        selected_category = st.radio("Välj händelsekategori", options=["Alla"] + sorted(df['main_categories'].unique()), index=0)

    with st.sidebar.expander("Välj län"):
        selected_location = st.radio("Välj län", options=["Alla"] + sorted(df['location_name'].unique()), index=0)

    with st.sidebar.expander("Välj period"):
        start_date = st.date_input("Startdatum", value=pd.to_datetime(df['date'].min()))
        end_date = st.date_input("Slutdatum", value=pd.to_datetime(df['date'].max()))
    
    filtered_df = df[ 
        ((df['main_categories'] == selected_category) | (selected_category == "Alla")) & 
        ((df['location_name'] == selected_location) | (selected_location == "Alla")) & 
        (df['date'] >= start_date) & 
        (df['date'] <= end_date)
    ]

    # Create a new map for the filtered data
    filtered_map = folium.Map(location=[61.0, 15.0], zoom_start=5)
    
    icon_mapping = {
        'Trafik': ('car', 'blue'),
        'Brand': ('fire', 'red'),
        'Rån och Stöld': ('lock', 'orange'),
        'Våld': ('skull-crossbones', 'black'),
        'Skottlossning': ('crosshairs', 'gray'),
        'Explosion': ('bomb', 'yellow'),
        'Ovrigt': None
    }

    # Add markers for each event
    for _, row in filtered_df.iterrows():
        icon_name, icon_color = icon_mapping.get(row['main_categories'], ('info-circle', 'blue'))
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.Icon(icon=icon_name, prefix='fa', color=icon_color),
            popup=folium.Popup(
                html=f"""
                <div style="width: 200px; white-space: normal;">
                    <strong>Län:</strong> {row['location_name']}<br>
                    <strong>Händelse:</strong> {row['name']}<br>
                    <strong>Datum:</strong> {row['date']}<br>
                    <strong>Tid:</strong> {row['time']}<br>
                    {row['summary']}<br>
                </div>
                """,
                max_width=200
            ),
        ).add_to(filtered_map)

    # Display the updated map
    st_folium(filtered_map, width=1000, height=700)
