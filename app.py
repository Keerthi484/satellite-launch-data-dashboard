import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="Satellite Launch Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        background-color: #0b0d12;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    .dashboard-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .dashboard-subtitle {
        color: #9ca3af;
        font-size: 16px;
        margin-bottom: 25px;
    }

    .metric-card {
        background: #151821;
        border: 1px solid #292d38;
        border-radius: 14px;
        padding: 20px;
        min-height: 125px;
    }

    .metric-label {
        color: #9ca3af;
        font-size: 14px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 800;
        margin-top: 8px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    .satellite-card {
        background: #151821;
        border: 1px solid #292d38;
        border-radius: 14px;
        padding: 22px;
        margin-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@st.cache_data
def load_launch_sites():
    return pd.read_csv("launch_sites.csv")


try:
    launch_sites = load_launch_sites()
except Exception as e:
    st.error("Could not load launch_sites.csv")
    st.code(str(e))
    st.stop()

# ---------------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------------

launch_sites["country"] = launch_sites["country"].fillna("Unknown")
launch_sites["site_name"] = launch_sites["site_name"].fillna("Unknown")
launch_sites["operator"] = launch_sites["operator"].fillna("Unknown")

launch_sites["total_launches"] = pd.to_numeric(
    launch_sites["total_launches"], errors="coerce"
).fillna(0)

launch_sites["success_rate"] = pd.to_numeric(
    launch_sites["success_rate"], errors="coerce"
).fillna(0)

launch_sites["latitude"] = pd.to_numeric(
    launch_sites["latitude"], errors="coerce"
)

launch_sites["longitude"] = pd.to_numeric(
    launch_sites["longitude"], errors="coerce"
)

launch_sites["is_active_2024"] = pd.to_numeric(
    launch_sites["is_active_2024"], errors="coerce"
).fillna(0)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.title("🛰️ Dashboard Controls")

st.sidebar.markdown("### Country")

countries = sorted(
    launch_sites["country"].dropna().unique().tolist()
)

country_options = ["All Countries"] + countries

selected_country = st.sidebar.selectbox(
    "Select a country",
    country_options,
)

if selected_country == "All Countries":
    filtered_sites = launch_sites.copy()
else:
    filtered_sites = launch_sites[
        launch_sites["country"] == selected_country
    ].copy()

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="dashboard-title">🛰️ Satellite Launch Intelligence</div>',
    unsafe_allow_html=True,
)

if selected_country == "All Countries":
    subtitle = "Global launch-site and mission intelligence"
else:
    subtitle = f"Country analysis — {selected_country}"

st.markdown(
    f'<div class="dashboard-subtitle">{subtitle}</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------

total_sites = len(filtered_sites)
total_launches = int(filtered_sites["total_launches"].sum())

active_sites = int(
    filtered_sites["is_active_2024"].sum()
)

avg_success = (
    filtered_sites["success_rate"].mean()
    if len(filtered_sites) > 0
    else 0
)

countries_count = filtered_sites["country"].nunique()

# Estimated successful/failed launches
successful_launches = round(
    sum(
        row["total_launches"] * row["success_rate"]
        for _, row in filtered_sites.iterrows()
    )
)

failed_launches = max(
    total_launches - successful_launches,
    0,
)

overall_success = (
    successful_launches / total_launches
    if total_launches > 0
    else 0
)

# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">🚀 Total Launches</div>
            <div class="metric-value">{total_launches:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">📍 Launch Sites</div>
            <div class="metric-value">{total_sites:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">🌍 Countries</div>
            <div class="metric-value">{countries_count:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">🟢 Active Sites</div>
            <div class="metric-value">{active_sites:,}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k5:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">📈 Success Rate</div>
            <div class="metric-value">{overall_success:.1%}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------
# WORLD MAP + SUCCESS/FAILURE
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🌍 Global Launch-Site Intelligence</div>',
    unsafe_allow_html=True,
)

map_col, pie_col = st.columns([1.55, 1])

with map_col:

    map_data = filtered_sites.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    if len(map_data) > 0:

        fig_map = px.scatter_geo(
            map_data,
            lat="latitude",
            lon="longitude",
            hover_name="site_name",
            hover_data={
                "country": True,
                "operator": True,
                "total_launches": True,
                "success_rate": ":.1%",
                "latitude": False,
                "longitude": False,
            },
            size="total_launches",
            color="success_rate",
            projection="natural earth",
            title="Satellite Launch Sites",
        )

        fig_map.update_layout(
            height=520,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(
            fig_map,
            width="stretch",
        )

    else:
        st.info("No map data available.")

with pie_col:

    pie_df = pd.DataFrame(
        {
            "Outcome": ["Successful", "Failed"],
            "Launches": [
                successful_launches,
                failed_launches,
            ],
        }
    )

    fig_pie = px.pie(
        pie_df,
        names="Outcome",
        values="Launches",
        hole=0.48,
        title="Success vs Failure",
    )

    fig_pie.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_pie,
        width="stretch",
    )

# ---------------------------------------------------------
# COUNTRY ANALYSIS
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">📊 Country Analysis</div>',
    unsafe_allow_html=True,
)

country_launches = (
    filtered_sites.groupby("country", as_index=False)["total_launches"]
    .sum()
    .sort_values("total_launches", ascending=False)
)

country_launches = country_launches.head(15)

fig_country = px.bar(
    country_launches,
    x="country",
    y="total_launches",
    title="Launches by Country",
    labels={
        "country": "Country",
        "total_launches": "Launches",
    },
)

fig_country.update_layout(
    height=430,
    xaxis_tickangle=-35,
    paper_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig_country,
    width="stretch",
)

# ---------------------------------------------------------
# SUCCESS RATE + ACTIVE SITES
# ---------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    success_df = (
        filtered_sites.groupby("country", as_index=False)["success_rate"]
        .mean()
        .sort_values("success_rate", ascending=False)
    )

    success_df = success_df.head(15)

    fig_success = px.bar(
        success_df,
        x="country",
        y="success_rate",
        title="Average Success Rate by Country",
        labels={
            "country": "Country",
            "success_rate": "Success Rate",
        },
    )

    fig_success.update_yaxes(
        tickformat=".0%"
    )

    fig_success.update_layout(
        height=420,
        xaxis_tickangle=-35,
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_success,
        width="stretch",
    )

with col2:

    active_df = pd.DataFrame(
        {
            "Status": ["Active", "Inactive"],
            "Sites": [
                active_sites,
                max(total_sites - active_sites, 0),
            ],
        }
    )

    fig_active = px.pie(
        active_df,
        names="Status",
        values="Sites",
        hole=0.45,
        title="Active vs Inactive Launch Sites",
    )

    fig_active.update_layout(
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_active,
        width="stretch",
    )

# ---------------------------------------------------------
# TOP LAUNCH SITES
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🚀 Major Launch Sites</div>',
    unsafe_allow_html=True,
)

top_sites = (
    filtered_sites[
        [
            "site_name",
            "country",
            "operator",
            "total_launches",
            "success_rate",
            "is_active_2024",
        ]
    ]
    .sort_values(
        "total_launches",
        ascending=False,
    )
    .head(10)
)

fig_sites = px.bar(
    top_sites,
    x="site_name",
    y="total_launches",
    color="success_rate",
    title="Top Launch Sites by Total Launches",
    labels={
        "site_name": "Launch Site",
        "total_launches": "Total Launches",
        "success_rate": "Success Rate",
    },
)

fig_sites.update_layout(
    height=450,
    xaxis_tickangle=-40,
    paper_bgcolor="rgba(0,0,0,0)",
)

st.plotly_chart(
    fig_sites,
    width="stretch",
)

# ---------------------------------------------------------
# LAUNCH SITE TABLE
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">📋 Launch Site Details</div>',
    unsafe_allow_html=True,
)

display_columns = [
    "site_name",
    "country",
    "operator",
    "active_from",
    "active_to",
    "is_active_2024",
    "total_launches",
    "success_rate",
    "altitude_m",
    "launch_pads",
]

available_columns = [
    c for c in display_columns
    if c in filtered_sites.columns
]

table = filtered_sites[available_columns].copy()

if "success_rate" in table.columns:
    table["success_rate"] = table["success_rate"].map(
        lambda x: f"{x:.1%}"
    )

if "is_active_2024" in table.columns:
    table["is_active_2024"] = table["is_active_2024"].map(
        lambda x: "Active" if x == 1 else "Inactive"
    )

st.dataframe(
    table,
    width="stretch",
    hide_index=True,
)

# ---------------------------------------------------------
# SATELLITE SECTION
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">🛰️ Satellite Intelligence</div>',
    unsafe_allow_html=True,
)

st.info(
    "Satellite-level information will appear here once the "
    "satellites.csv dataset is added. The current launch_sites.csv "
    "contains launch-site information, not individual satellite records."
)

st.markdown(
    """
    <div class="satellite-card">
        <h3>🛰️ Satellite Details</h3>
        <p>
        Select a country and, once the satellite dataset is connected,
        you will be able to search individual satellites and view
        their description, mission information and image.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    "Satellite Launch Intelligence • Built with Streamlit • "
    "Launch-site data source: launch_sites.csv"
)
