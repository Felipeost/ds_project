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

credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

st.set_page_config(layout="wide")
tabs = st.tabs(["Händelser", "Analys"])

def load_data():
    query = """
    SELECT location_name, name, summary, date, time, latitude, longitude
    FROM `crime-in-sweden-project.Crime_in_Sweden.unique_events`
    """
    return client.query(query).to_dataframe()

def categorize_event(event_type):
    categories = {
        "Trafik": ["Trafikbrott", "Trafikhinder", "Trafikkontroll", "Trafikolycka", "Rattfylleri"],
        "Explosion": ["Bombhot", "Detonation", "Explosion"],
        "Rån och Stöld": ["Inbrott", "Häleri", "Motorfordon, stöld", "Rån"],
        "Skottlossning": ["Skottlossning"],
        "Våld": ["Bråk", "Misshandel", "Mord/dråp", "Olaga hot", "Våldtäkt"],
        "Brand": ["Brand", "Brand automatlarm"],
    }
    for category, types in categories.items():
        if event_type in types:
            return category
    return "Annat"

df = load_data()
df["main_categories"] = df["name"].apply(categorize_event)

with tabs[0]:
    st.header("Händelser i Sverige rapporterade av Polisen 👮‍♂️")
    st.write("Få mer insikt genom att klicka på markören!")
    
    st.sidebar.header("Filtrera")
    selected_category = st.sidebar.selectbox("Välj händelsekategori", ["Alla"] + sorted(df["main_categories"].unique()))
    selected_location = st.sidebar.selectbox("Välj plats", ["Alla"] + sorted(df["location_name"].unique()))
    
    with st.sidebar.expander("Välj period"):
        start_date = st.date_input("Startdatum", value=pd.to_datetime(df["date"].min()))
        end_date = st.date_input("Slutdatum", value=pd.to_datetime(df["date"].max()))
    
    filtered_df = df[
        ((df["main_categories"] == selected_category) | (selected_category == "Alla")) &
        ((df["location_name"] == selected_location) | (selected_location == "Alla")) &
        (df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))
    ]
    
    filtered_map = folium.Map(location=[61.0, 15.0], zoom_start=5)
    icon_mapping = {
        "Trafik": ("car", "blue"), "Brand": ("fire", "red"),
        "Rån och Stöld": ("lock", "orange"), "Våld": ("skull-crossbones", "black"),
        "Skottlossning": ("crosshairs", "gray"), "Explosion": ("bomb", "orange")
    }
    
    event_counts = filtered_df.groupby(["latitude", "longitude"]).size().reset_index(name="count")
    
    for _, row in event_counts.iterrows():
        lat, lon, count = row["latitude"], row["longitude"], int(row["count"])
        event_category = filtered_df[(filtered_df["latitude"] == lat) & (filtered_df["longitude"] == lon)]["main_categories"].values[0]
        icon_name, icon_color = icon_mapping.get(event_category, ("info-circle", "green"))
        folium.Marker(location=[lat, lon], icon=folium.Icon(icon=icon_name, prefix="fa", color=icon_color), tooltip=f"Antal: {count}").add_to(filtered_map)
    
    clicked_data = st_folium(filtered_map, width=1000, height=700)
    if clicked_data and clicked_data["last_object_clicked"]:
        lat, lon = clicked_data["last_object_clicked"]["lat"], clicked_data["last_object_clicked"]["lng"]
        events_at_location = filtered_df[(filtered_df["latitude"] == lat) & (filtered_df["longitude"] == lon)]
        st.sidebar.subheader("Information")
        for _, event in events_at_location.sort_values("date", ascending=False).iterrows():
            st.sidebar.markdown(f"""
            <strong>Län:</strong> {event['location_name']}<br>
            <strong>Händelse:</strong> {event['name']}<br>
            <strong>Datum:</strong> {event['date']}<br>
            <strong>Tid:</strong> {event['time']}<br>
            {event['summary']}<hr style="border: 1px solid #ccc;">
            """, unsafe_allow_html=True)

with tabs[1]:
    st.header("Analys av Polisens Rapporterade Händelser i Sverige")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 3 Mest Rapporterade Händelser")
        
        top_incidents = (filtered_df['name']
                         .value_counts()
                         .nlargest(5)
                         .reset_index()
                         .rename(columns={'index': 'Händelsetyp', 'name': 'Count'}))
        
        top_incidents.index = top_incidents.index + 1
        st.table(top_incidents)
    
    with col2:
        st.subheader("Top 5 Mängd Händelser per Stad")
    
        city_counts = filtered_df['location_name'].value_counts().nlargest(5)

        city_colors = ["#FF6F61", "#6B5B95", "#88B04B", "#F7CAC9", "#92A8D1"]

        city_bar = (
            Bar(init_opts=opts.InitOpts())
            .add_xaxis(city_counts.index.tolist())
            .add_yaxis(
                "Mängd händelser", 
                city_counts.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(f"function(params) {{ return ['{city_colors[0]}', '{city_colors[1]}', '{city_colors[2]}', '{city_colors[3]}', '{city_colors[4]}'][params.dataIndex]; }}")
                )
            )
            .reversal_axis()
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(name="Mängd"),
                yaxis_opts=opts.AxisOpts(name="Stad"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
            )
        )
        st_pyecharts(city_bar)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Mängd Händelser per Kategori")
        
        incident_counts = filtered_df['main_categories'].value_counts()

        category_colors = ["#FFD700", "#FF6347", "#4682B4", "#32CD32", "#9370DB"]

        bar = (
            Bar()
            .add_xaxis(incident_counts.index.tolist())
            .add_yaxis(
                "Mängd händelser", 
                incident_counts.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(f"function(params) {{ return ['{category_colors[0]}', '{category_colors[1]}', '{category_colors[2]}', '{category_colors[3]}', '{category_colors[4]}'][params.dataIndex]; }}")
                )
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(name="Kategori", axislabel_opts={"rotate": 45}),
                yaxis_opts=opts.AxisOpts(name="Mängd"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
            )
        )
        st_pyecharts(bar)
    
    with col4:
        st.subheader("Händelser över tid")
        
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        crimes_over_time = filtered_df.groupby(filtered_df['date'].dt.to_period('D')).size().reset_index(name='count')
        crimes_over_time['date'] = crimes_over_time['date'].dt.strftime('%Y-%m-%d')

        line_color = "#FF4500"

        line = (
            Line()
            .add_xaxis(crimes_over_time['date'].tolist())
            .add_yaxis(
                "Mängd Händelser", 
                crimes_over_time['count'].tolist(),
                itemstyle_opts=opts.ItemStyleOpts(color=line_color)
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(name="Datum", axislabel_opts={"rotate": 45}),
                yaxis_opts=opts.AxisOpts(name="Mängd"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
            )
        )
        st_pyecharts(line)
