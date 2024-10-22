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
            xaxis_opts=opts.AxisOpts(name="Kategori", axislabel_opts={"rotate": 45}),
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
