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

# Load credentials from the JSON key file
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(
    script_dir, "..", "crime-in-sweden-project-47eef163c346.json"
)

credentials = service_account.Credentials.from_service_account_file(credentials_path)

client = bigquery.Client(credentials=credentials, project=credentials.project_id)

st.set_page_config(layout="wide")

tabs = st.tabs(["Händelser", "Analys"])

with tabs[0]:
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
        "Explosion": ("bomb", "yellow"),
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
        icon_name, icon_color = icon_mapping.get(
            event_category, ("info-circle", "green")
        )

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
            events_at_location = events_at_location.sort_values(
                by="date", ascending=False
            )

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

with tabs[1]:
    st.header("Analys av Polisens Rapporterade Händelser i Sverige 📊")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔸 Top 5 Mest Rapporterade Händelser")

        top_incidents = (
            filtered_df["name"]
            .value_counts()
            .nlargest(5)
            .reset_index()
            .rename(columns={"name": "Händelsetyp", "count": "Antal"})
        )

        top_incidents.index = top_incidents.index + 1
        st.table(top_incidents)

    with col2:
        st.subheader("🔸 Top 5 Mängd Händelser per Plats")

        city_counts = filtered_df["location_name"].value_counts().nlargest(5)

        city_colors = ["#FF6F61", "#6B5B95", "#88B04B", "#F7CAC9", "#92A8D1"]

        city_bar = (
            Bar(init_opts=opts.InitOpts())
            .add_xaxis(city_counts.index.tolist())
            .add_yaxis(
                "Mängd händelser",
                city_counts.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        f"function(params) {{ return ['{city_colors[0]}', '{city_colors[1]}', '{city_colors[2]}', '{city_colors[3]}', '{city_colors[4]}'][params.dataIndex]; }}"
                    )
                ),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    name="Stad",
                    axislabel_opts=opts.LabelOpts(rotate=-90, interval=0),
                ),
                yaxis_opts=opts.AxisOpts(name="Mängd"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        # Render the chart with specified size
        st_pyecharts(city_bar)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🔸 Mängd Händelser per Kategori")

        incident_counts = filtered_df["main_categories"].value_counts()

        category_colors = ["#FFD700", "#FF6347", "#4682B4", "#32CD32", "#9370DB"]

        bar = (
            Bar()
            .add_xaxis(incident_counts.index.tolist())
            .add_yaxis(
                "Mängd händelser",
                incident_counts.values.tolist(),
                itemstyle_opts=opts.ItemStyleOpts(
                    color=JsCode(
                        f"function(params) {{ return ['{category_colors[0]}', '{category_colors[1]}', '{category_colors[2]}', '{category_colors[3]}', '{category_colors[4]}'][params.dataIndex]; }}"
                    )
                ),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    name="Kategori", axislabel_opts={"rotate": 45}
                ),
                yaxis_opts=opts.AxisOpts(name="Mängd"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        st_pyecharts(bar)

    with col4:
        st.subheader("🔸 Händelser över tid")

        filtered_df["date"] = pd.to_datetime(filtered_df["date"])
        crimes_over_time = (
            filtered_df.groupby(filtered_df["date"].dt.to_period("D"))
            .size()
            .reset_index(name="count")
        )
        crimes_over_time["date"] = crimes_over_time["date"].dt.strftime("%Y-%m-%d")

        line_color = "#FF4500"

        line = (
            Line()
            .add_xaxis(crimes_over_time["date"].tolist())
            .add_yaxis(
                "Mängd Händelser",
                crimes_over_time["count"].tolist(),
                itemstyle_opts=opts.ItemStyleOpts(color=line_color),
            )
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(name="Datum", axislabel_opts={"rotate": 45}),
                yaxis_opts=opts.AxisOpts(name="Mängd"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(is_show=False),
            )
        )
        st_pyecharts(line)
