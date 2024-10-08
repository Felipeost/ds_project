
import streamlit as st
from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import json

# Load credentials from the JSON key file
credentials = service_account.Credentials.from_service_account_file(
    r"C:\Users\seema\OneDrive\Skrivbord\police api\crime-in-sweden-project-fd7f2891a629.json"
)

# Initialize BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Define all cities with coordinates
main_cities = {
    "Stockholm": (59.3293, 18.0686),
    "Gothenburg": (57.7089, 11.9746),
    "Malmö": (55.6040, 13.0038),
    "Uppsala": (59.8586, 17.6389),
    "Västerås": (59.6090, 16.5373),
    "Olofström": (56.1147, 14.5826),
    "Järfälla": (59.4011, 17.9414),
    "Södertälje": (59.1915, 17.6263),
    "Linköping": (58.4109, 15.6212),
    "Lund": (55.7047, 13.1910),
    "Kalmar": (56.6614, 16.3591),
    "Eskilstuna": (59.3682, 16.5072),
    "Ystad": (55.4262, 13.8295),
    "Borlänge": (60.4850, 15.4245),
    "Göteborg": (57.7089, 11.9746),
    "Helsingborg": (56.0465, 12.6945),
    "Markaryd": (56.1675, 13.5065),
    "Solna": (59.3326, 18.0295),
    "Umeå": (63.8258, 20.2630),
    "Sala": (59.8984, 16.5957),
    "Ronneby": (56.2381, 15.3156),
    "Härnösand": (62.6345, 17.9431),
    "Västervik": (57.6397, 16.6631),
    "Jönköping": (57.7816, 14.1572),
    "Kungsbacka": (57.4874, 12.0652),
    "Norrköping": (58.5862, 16.1904),
    "Skurup": (55.5920, 13.4700),
    "Höör": (55.8475, 13.7857),
    "Hässleholm": (56.1520, 13.7533),
    "Karlstad": (59.4023, 13.5038),
    "Kristianstad": (56.0295, 14.1556),
    "Luleå": (65.5846, 22.1549),
    "Enköping": (59.6378, 17.0570),
    "Hallsberg": (59.0853, 14.5258),
    "Nacka": (59.3153, 18.1846),
    "Lerum": (57.7260, 12.2947),
    "Tidaholm": (58.3173, 13.8983),
    "Staffanstorp": (55.6543, 13.1915),
    "Landskrona": (55.8833, 12.8333),
    "Örebro": (59.2753, 15.2069),
    "Söderhamn": (61.2961, 17.0882),
    "Borås": (57.7311, 13.1015),
    "Vimmerby": (57.6648, 15.8524),
    "Haninge": (59.1270, 18.0720),
    "Sandviken": (60.6298, 16.9493),
    "Bromölla": (56.0734, 14.5594),
    "Ludvika": (60.1451, 15.2062),
    "Alingsås": (57.9377, 12.5424),
    "Gävle": (60.6749, 17.1419),
    "Ovanåker": (61.3341, 15.7912),
    "Trelleborg": (55.3660, 13.1580),
    "Skövde": (58.3935, 13.8524),
    "Stockholms län": (59.3346, 18.0678),
    "Växjö": (56.8765, 14.8096),
    "Boden": (65.8420, 21.7006),
    "Falun": (60.6067, 15.6284),
    "Haparanda": (65.8397, 24.1347),
    "Sundsvall": (62.3908, 17.3069),
    "Östersund": (63.1790, 14.6353),
    "Karlskrona": (56.1610, 15.5869),
    "Ängelholm": (56.2412, 12.8551),
    "Sundbyberg": (59.3656, 17.9651),
    "Kiruna": (67.8557, 20.2253),
    "Forshaga": (59.4105, 13.4756),
    "Skellefteå": (64.7493, 20.9545),
    "Åre": (63.4160, 13.0877),
    "Burlöv": (55.6152, 13.0246),
    "Hallands län": (56.9926, 12.6855),
    "Värmlands län": (59.6653, 13.4426),
    "Halmstad": (56.6759, 12.8615),
    "Örebro län": (59.2680, 15.1521),
    "Västra Götalands län": (58.3940, 12.5714),
    "Dalarnas län": (60.4137, 15.6581),
    "Sigtuna": (59.6074, 17.7568),
    "Partille": (57.7050, 12.0241),
    "Avesta": (60.1212, 16.1792),
    "Gällivare": (67.1386, 20.6742),
    "Torsby": (60.2334, 13.3526),
    "Kil": (59.3947, 13.7040),
    "Tingsryd": (56.2919, 14.8803),
    "Gävleborgs län": (61.2064, 16.1642),
    "Täby": (59.4393, 18.0690),
    "Gotlands län": (57.5160, 18.6734),
    "Gotland": (57.5654, 18.5322),
    "Karlshamn": (56.1032, 14.8623),
    "Vänersborg": (58.3631, 12.3563),
    "Piteå": (65.3152, 21.4081),
    "Arvidsjaur": (65.5876, 19.2994),
    "Lidköping": (58.5007, 13.1514),
    "Älvsbyn": (65.6156, 20.6520),
    "Bollnäs": (61.3036, 16.5701),
    "Tyresö": (59.2570, 18.2821),
    "Älvkarleby": (60.6749, 17.1419),
    "Kungälv": (57.8511, 11.9751),
    "Värmdö": (58.2812, 18.3961),
    "Berg": (60.4968, 16.8434),
    "Huddinge": (59.1950, 17.9732),
    "Hofors": (60.4539, 16.1882),
    "Västerbottens län": (64.3944, 20.9285),
    "Säffle": (59.3770, 13.2580),
    "Norsjö": (64.0702, 19.6038),
    "Kumla": (59.1673, 14.6975),
    "Ljungby": (56.8237, 13.9795),
    "Eslöv": (55.8464, 13.3088),
    "Rättvik": (60.7625, 14.4703)
}

def fetch_weather_data(latitude, longitude):
    api_url = f"https://opendata-download-metanalys.smhi.se/api/category/mesan2g/version/1/geotype/point/lon/{longitude}/lat/{latitude}/data.json"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch data for {latitude}, {longitude}: {response.status_code}")
        return None

def categorize_weather(temp, wind_gust, precipitation):
    if temp < -5 or temp > 35 or wind_gust > 15 or precipitation > 5:
        return 'Bad'
    elif temp < 0 or wind_gust > 10 or precipitation > 2:
        return 'Moderate'
    else:
        return 'Good'

# Create tabs
tabs = st.tabs(["Crime", "Weather"])

# Crime Tab
with tabs[0]:
    st.header("Crimes in Sweden")
    
    # SQL query to fetch crime data
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
    
    # Execute the query and convert to DataFrame
    df = client.query(query).to_dataframe()
    
    # Define main categories based on the 'name' column without modifying original 'name'
    main_categories_mapping = {
        'Trafikolycka': 'Trafikolycka',
        'Brand': 'Brand',
        'Stöld': 'Stöld',
        'Narkotikabrott': 'Narkotikabrott',
        'Rån': 'Rån',
        'Mord/dråp': 'Mord/dråp',
        'Inbrott': 'Inbrott',
        'Skottlossning': 'Skottlossning',
        'Explosion': 'Explosion'
    }
    
    # Create a new column for main categories based on the mapping
    df['main_categories'] = df['name'].apply(lambda x: main_categories_mapping.get(x, 'Ovrigt'))
    
    # Sidebar for filters
    st.sidebar.header("Filters")  # Main heading for the filters section
    
    # Expander for categories filter with checkboxes
    with st.sidebar.expander("Select Event Categories"):
        # "Select All" checkbox for event categories
        select_all_categories = st.checkbox("Select All Event Categories", value=True)
    
        selected_categories = []
        for category in sorted(df['main_categories'].unique()):
            if st.checkbox(category, value=select_all_categories):  # Default to "Select All" state
                selected_categories.append(category)
    
    # Expander for location filter with checkboxes
    with st.sidebar.expander("Select Locations"):
        select_all_locations = st.checkbox("Select All Locations", value=True)
        
        selected_locations = []
        for location in sorted(df['location_name'].unique()):
            if st.checkbox(location, value=select_all_locations):  # Default to "Select All" state
                selected_locations.append(location)
    
    # Expander for date filter
    with st.sidebar.expander("Select Date Range"):
        start_date = st.date_input("Start Date", value=pd.to_datetime(df['date'].min()))
        end_date = st.date_input("End Date", value=pd.to_datetime(df['date'].max()))
    
    # Check if categories or locations are selected
    if not selected_categories:
        selected_categories = df['main_categories'].unique()  # Include all if none selected
    
    if not selected_locations:
        selected_locations = df['location_name'].unique()  # Include all if none selected
    
    # Filter the DataFrame based on selected categories, locations, and date range
    filtered_df = df[
        (df['main_categories'].isin(selected_categories)) & 
        (df['location_name'].isin(selected_locations)) & 
        (df['date'] >= start_date) & 
        (df['date'] <= end_date)
    ]
    
    # Display the top 3 incidents based on their count
    top_incidents = (filtered_df['name']
                     .value_counts()
                     .nlargest(3)
                     .reset_index()
                     .rename(columns={'name': 'Incident type'}))
    
    # Add a new column for the index starting from 1
    top_incidents.index = top_incidents.index + 1
    
    # Show the top incidents in a table
    st.subheader("Top 3 Incidents")
    st.table(top_incidents)
    
    # Create a new map for the filtered data
    filtered_map = folium.Map(location=[61.0, 15.0], zoom_start=5)
    
    # Define a mapping for your main categories and their corresponding Font Awesome icons and colors
    icon_mapping = {
        'Trafikolycka': ('car', 'blue'),
        'Brand': ('fire', 'red'),
        'Stöld': ('lock', 'orange'),
        'Narkotikabrott': ('leaf', 'green'),
        'Rån': ('user-secret', 'purple'),
        'Mord/dråp': ('skull-crossbones', 'black'),
        'Inbrott': ('home', 'darkgreen'),
        'Skottlossning': ('crosshairs', 'gray'),
        'Explosion': ('bomb', 'yellow'),
        'Ovrigt': ('question-circle', 'darkblue')
    }
    
    # Add markers with pop-ups using Font Awesome icons based on filtered data
    for _, row in filtered_df.iterrows():
        icon_name, icon_color = icon_mapping.get(row['main_categories'], ('info-circle', 'blue'))  # Default to blue icon if not found
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            icon=folium.Icon(icon=icon_name, prefix='fa', color=icon_color),  # Use the corresponding color
            popup=f"""
                <strong>Location:</strong> {row['location_name']}<br>
                <strong>Date:</strong> {row['date']}<br>
                <strong>Time:</strong> {row['time']}<br>
                <strong>Summary:</strong> {row['summary']}<br>
                <strong>Name:</strong> {row['name']}
            """,
        ).add_to(filtered_map)
    
    # Display the updated map
    st_folium(filtered_map, width=700, height=500)

# Weather Tab
with tabs[1]:
    st.header("Weather Conditions for Driving")
    
    # Multi-select for cities
    selected_cities = st.multiselect("Select Cities", list(main_cities.keys()), default=["Stockholm"])
    
    # Initialize a DataFrame to store weather conditions
    weather_conditions = []
    
    # Create a Folium map for weather conditions
    weather_map = folium.Map(location=[61.0, 15.0], zoom_start=5)
    
    for city in selected_cities:
        lat, lon = main_cities[city]
        weather_data = fetch_weather_data(lat, lon)
        
        if weather_data:
            try:
                most_recent_entry = weather_data['timeSeries'][0]  # Only the first (most recent) entry
                valid_time = most_recent_entry['validTime']
                parameters = most_recent_entry['parameters']
                
                temp = next(param['values'][0] for param in parameters if param['name'] == 't')
                wind_gust = next(param['values'][0] for param in parameters if param['name'] == 'gust')
                precipitation = next(param['values'][0] for param in parameters if param['name'] == 'prec1h')
    
                # Categorize weather conditions
                condition = categorize_weather(temp, wind_gust, precipitation)
    
                # Append to the DataFrame
                weather_conditions.append({
                    "City": city,
                    "Time": valid_time,
                    "Temperature (°C)": temp,
                    "Wind Gust (m/s)": wind_gust,
                    "Precipitation (mm)": precipitation,
                    "Traffic Condition": condition
                })
    
                # Define color based on condition
                if condition == 'Good':
                    color = 'green'
                elif condition == 'Moderate':
                    color = 'orange'
                else:
                    color = 'red'
    
                # Add marker to the map
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    popup=f"""
                        <strong>City:</strong> {city}<br>
                        <strong>Time:</strong> {valid_time}<br>
                        <strong>Temperature:</strong> {temp}°C<br>
                        <strong>Wind Gust:</strong> {wind_gust} m/s<br>
                        <strong>Precipitation:</strong> {precipitation} mm<br>
                        <strong>Traffic Condition:</strong> <span style="color:{color}; font-weight:bold;">{condition}</span>
                    """,
                    color=color,
                    fill=True,
                    fill_color=color
                ).add_to(weather_map)
    
            except (KeyError, StopIteration):
                st.error(f"Unexpected data format received for {city}.")
        else:
            st.error(f"No weather data available for {city}.")
    
    # Display the weather conditions in a table
    if weather_conditions:
        weather_df = pd.DataFrame(weather_conditions)
        st.subheader("Current Weather Conditions")
        st.table(weather_df)
    
    # Display the weather map
    st.subheader("Weather Conditions Map")
    st_folium(weather_map, width=700, height=500)

