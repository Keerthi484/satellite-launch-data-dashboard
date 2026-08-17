import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from urllib.parse import quote

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Satellite Launch Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# CUSTOM CSS
# =========================================================

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
        font-size: 40px;
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
        min-height: 120px;
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

    .site-card {
        background: #151821;
        border: 1px solid #292d38;
        border-radius: 16px;
        padding: 24px;
        margin-top: 10px;
    }

    .site-description {
        color: #d1d5db;
        line-height: 1.7;
        font-size: 15px;
    }

    .source-text {
        color: #6b7280;
        font-size: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# LOAD LAUNCH-SITE DATA
# =========================================================

@st.cache_data
def load_launch_sites():
    return pd.read_csv("launch_sites.csv")


try:
    launch_sites = load_launch_sites()

except Exception as e:
    st.error("Could not load launch_sites.csv")
    st.code(str(e))
    st.stop()


# =========================================================
# CLEAN DATA
# =========================================================

required_columns = [
    "country",
    "site_name",
    "operator",
    "total_launches",
    "success_rate",
    "latitude",
    "longitude",
    "is_active_2024",
]

missing_columns = [
    column
    for column in required_columns
    if column not in launch_sites.columns
]

if missing_columns:

    st.error(
        "The launch_sites.csv file is missing these columns:"
    )

    st.write(missing_columns)

    st.stop()


launch_sites["country"] = (
    launch_sites["country"]
    .fillna("Unknown")
    .astype(str)
)

launch_sites["site_name"] = (
    launch_sites["site_name"]
    .fillna("Unknown")
    .astype(str)
)

launch_sites["operator"] = (
    launch_sites["operator"]
    .fillna("Unknown")
    .astype(str)
)


launch_sites["total_launches"] = pd.to_numeric(
    launch_sites["total_launches"],
    errors="coerce",
).fillna(0)


launch_sites["success_rate"] = pd.to_numeric(
    launch_sites["success_rate"],
    errors="coerce",
).fillna(0)


launch_sites["latitude"] = pd.to_numeric(
    launch_sites["latitude"],
    errors="coerce",
)


launch_sites["longitude"] = pd.to_numeric(
    launch_sites["longitude"],
    errors="coerce",
)


launch_sites["is_active_2024"] = pd.to_numeric(
    launch_sites["is_active_2024"],
    errors="coerce",
).fillna(0)


# =========================================================
# OPTIONAL COLUMNS
# =========================================================

if "launch_pads" not in launch_sites.columns:
    launch_sites["launch_pads"] = 0

if "altitude_m" not in launch_sites.columns:
    launch_sites["altitude_m"] = 0

if "active_from" not in launch_sites.columns:
    launch_sites["active_from"] = "Unknown"

if "active_to" not in launch_sites.columns:
    launch_sites["active_to"] = "Present"

if "latitude_advantage" not in launch_sites.columns:
    launch_sites["latitude_advantage"] = 0


launch_sites["launch_pads"] = pd.to_numeric(
    launch_sites["launch_pads"],
    errors="coerce",
).fillna(0)


launch_sites["altitude_m"] = pd.to_numeric(
    launch_sites["altitude_m"],
    errors="coerce",
).fillna(0)


launch_sites["latitude_advantage"] = pd.to_numeric(
    launch_sites["latitude_advantage"],
    errors="coerce",
).fillna(0)


# =========================================================
# WIKIPEDIA INFORMATION LOOKUP
# =========================================================

@st.cache_data(ttl=86400)
def get_site_information(site_name):

    try:

        search_url = (
            "https://en.wikipedia.org/w/api.php"
        )

        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": site_name,
            "format": "json",
            "utf8": 1,
            "srlimit": 1,
        }

        response = requests.get(
            search_url,
            params=search_params,
            timeout=10,
            headers={
                "User-Agent": (
                    "SatelliteLaunchAnalytics/1.0"
                )
            },
        )

        response.raise_for_status()

        search_data = response.json()

        results = (
            search_data
            .get("query", {})
            .get("search", [])
        )

        if not results:

            return {
                "title": site_name,
                "description": (
                    "No public description was found "
                    "for this launch site."
                ),
                "image": None,
                "url": None,
            }

        page_title = results[0]["title"]

        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + quote(
                page_title.replace(" ", "_")
            )
        )

        summary_response = requests.get(
            summary_url,
            timeout=10,
            headers={
                "User-Agent": (
                    "SatelliteLaunchAnalytics/1.0"
                )
            },
        )

        summary_response.raise_for_status()

        summary = summary_response.json()

        description = summary.get(
            "extract",
            "No description is available.",
        )

        image = None

        thumbnail = summary.get(
            "thumbnail"
        )

        if thumbnail:

            image = thumbnail.get(
                "source"
            )

        page_url = (
            "https://en.wikipedia.org/wiki/"
            + quote(
                page_title.replace(" ", "_")
            )
        )

        return {
            "title": page_title,
            "description": description,
            "image": image,
            "url": page_url,
        }

    except Exception:

        return {
            "title": site_name,
            "description": (
                "Public information could not "
                "be retrieved automatically. "
                "The statistics shown below "
                "come from the project dataset."
            ),
            "image": None,
            "url": None,
        }


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🛰️ Dashboard Controls")

st.sidebar.markdown(
    "### 🌍 Country"
)

countries = sorted(
    launch_sites["country"]
    .dropna()
    .unique()
    .tolist()
)

country_options = [
    "All Countries"
] + countries

selected_country = st.sidebar.selectbox(
    "Select a country",
    country_options,
)


# =========================================================
# MAIN FILTER
# =========================================================

if selected_country == "All Countries":

    filtered_sites = launch_sites.copy()

else:

    filtered_sites = launch_sites[
        launch_sites["country"]
        == selected_country
    ].copy()


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="dashboard-title">
        🛰️ Satellite Launch Intelligence
    </div>
    """,
    unsafe_allow_html=True,
)


if selected_country == "All Countries":

    subtitle = (
        "Global launch-site infrastructure "
        "and performance analysis"
    )

else:

    subtitle = (
        f"Launch-site analysis for "
        f"{selected_country}"
    )


st.markdown(
    f"""
    <div class="dashboard-subtitle">
        {subtitle}
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SEARCH BAR
# =========================================================

search_text = st.text_input(
    "🔎 Search country or launch site",
    placeholder=(
        "Example: India, Sriharikota, "
        "Cape Canaveral..."
    ),
)


if search_text.strip():

    search_lower = (
        search_text
        .strip()
        .lower()
    )

    search_mask = (
        filtered_sites["country"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
        |
        filtered_sites["site_name"]
        .str.lower()
        .str.contains(
            search_lower,
            na=False,
        )
    )

    filtered_sites = (
        filtered_sites[search_mask]
        .copy()
    )


# =========================================================
# KPI CALCULATIONS
# =========================================================

total_sites = len(
    filtered_sites
)

total_launches = int(
    filtered_sites[
        "total_launches"
    ].sum()
)

active_sites = int(
    filtered_sites[
        "is_active_2024"
    ].sum()
)

country_count = (
    filtered_sites[
        "country"
    ].nunique()
)


successful_launches = round(
    sum(
        row["total_launches"]
        * row["success_rate"]
        for _, row
        in filtered_sites.iterrows()
    )
)

failed_launches = max(
    total_launches
    - successful_launches,
    0,
)


overall_success = (

    successful_launches
    / total_launches

    if total_launches > 0

    else 0
)


# =========================================================
# KPI CARDS
# =========================================================

k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-label">
        🚀 Total Launches
        </div>

        <div class="metric-value">
        {total_launches:,}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with k2:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-label">
        📍 Launch Sites
        </div>

        <div class="metric-value">
        {total_sites:,}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with k3:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-label">
        🌍 Countries
        </div>

        <div class="metric-value">
        {country_count:,}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with k4:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-label">
        🟢 Active Sites
        </div>

        <div class="metric-value">
        {active_sites:,}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with k5:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-label">
        🎯 Success Rate
        </div>

        <div class="metric-value">
        {overall_success:.1%}
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# NO RESULTS CHECK
# =========================================================

if len(filtered_sites) == 0:

    st.warning(
        "No launch sites match your current search."
    )

    st.stop()


# =========================================================
# WORLD MAP
# =========================================================

st.markdown(
    "## 🌍 Global Launch-Site Map"
)


map_data = filtered_sites.dropna(
    subset=[
        "latitude",
        "longitude",
    ]
)


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
        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(
        fig_map,
        width="stretch",
    )

else:

    st.info(
        "No valid coordinates are available "
        "for the current selection."
    )


# =========================================================
# SUCCESS / FAILURE PIE CHART
# =========================================================

st.markdown(
    "## 🎯 Launch Outcomes"
)


pie_data = pd.DataFrame(
    {
        "Outcome": [
            "Successful",
            "Failed",
        ],
        "Launches": [
            successful_launches,
            failed_launches,
        ],
    }
)


fig_pie = px.pie(
    pie_data,
    names="Outcome",
    values="Launches",
    hole=0.48,
    title="Success vs Failure",
)


fig_pie.update_layout(
    height=430,
    margin=dict(
        l=0,
        r=0,
        t=50,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)


st.plotly_chart(
    fig_pie,
    width="stretch",
)


# =========================================================
# COUNTRY ANALYSIS
# =========================================================

st.markdown(
    "## 📊 Launches by Country"
)


country_launches = (
    filtered_sites
    .groupby(
        "country",
        as_index=False,
    )["total_launches"]
    .sum()
    .sort_values(
        "total_launches",
        ascending=False,
    )
)


fig_country = px.bar(
    country_launches.head(15),
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
    margin=dict(
        l=0,
        r=0,
        t=50,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)


st.plotly_chart(
    fig_country,
    width="stretch",
)


# =========================================================
# SUCCESS RATE BY COUNTRY
# =========================================================

st.markdown(
    "## 📈 Success Rate by Country"
)


success_country = (
    filtered_sites
    .groupby(
        "country",
        as_index=False,
    )["success_rate"]
    .mean()
    .sort_values(
        "success_rate",
        ascending=False,
    )
)


fig_success = px.bar(
    success_country.head(15),
    x="country",
    y="success_rate",
    title="Average Success Rate",
    labels={
        "country": "Country",
        "success_rate": "Success Rate",
    },
)


fig_success.update_yaxes(
    tickformat=".0%"
)


fig_success.update_layout(
    height=430,
    xaxis_tickangle=-35,
    margin=dict(
        l=0,
        r=0,
        t=50,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)


st.plotly_chart(
    fig_success,
    width="stretch",
)


# =========================================================
# TOP LAUNCH SITES
# =========================================================

st.markdown(
    "## 🚀 Major Launch Sites"
)


top_sites = (
    filtered_sites[
        [
            "site_name",
            "country",
            "operator",
            "total_launches",
            "success_rate",
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
    title="Top Launch Sites",
    labels={
        "site_name": "Launch Site",
        "total_launches": "Total Launches",
        "success_rate": "Success Rate",
    },
)


fig_sites.update_layout(
    height=450,
    xaxis_tickangle=-40,
    margin=dict(
        l=0,
        r=0,
        t=50,
        b=0,
    ),
    paper_bgcolor="rgba(0,0,0,0)",
)


st.plotly_chart(
    fig_sites,
    width="stretch",
)


# =========================================================
# LAUNCH SITE EXPLORER
# =========================================================

st.markdown("---")

st.markdown(
    "## 🚀 Explore a Launch Site"
)


site_names = sorted(
    filtered_sites[
        "site_name"
    ]
    .dropna()
    .unique()
    .tolist()
)


if site_names:

    selected_site_name = st.selectbox(
        "Select a launch site",
        site_names,
    )


    selected_site = (
        filtered_sites[
            filtered_sites["site_name"]
            == selected_site_name
        ]
        .iloc[0]
    )


    # =====================================================
    # GET PUBLIC SITE INFORMATION
    # =====================================================

    with st.spinner(
        "Loading launch-site information..."
    ):

        site_info = get_site_information(
            selected_site_name
        )


    # =====================================================
    # IMAGE + DESCRIPTION
    # =====================================================

    image_col, description_col = st.columns(
        [1, 1.4]
    )


    with image_col:

        if site_info["image"]:

            st.image(
                site_info["image"],
                caption=selected_site_name,
                width="stretch",
            )

        else:

            st.info(
                "No suitable public image was "
                "found automatically."
            )


    with description_col:

        st.markdown(
            f"### 📍 {selected_site_name}"
        )

        st.markdown(
            f"""
            <div class="site-card">

            <div class="site-description">

            {site_info["description"]}

            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


        if site_info["url"]:

            st.markdown(
                f"[Read more about this site on Wikipedia]({site_info['url']})"
            )


    # =====================================================
    # SITE STATISTICS
    # =====================================================

    st.markdown(
        "### 📊 Launch-Site Statistics"
    )


    s1, s2, s3, s4 = st.columns(4)


    with s1:

        st.metric(
            "Country",
            selected_site["country"],
        )


    with s2:

        st.metric(
            "Operator",
            selected_site["operator"],
        )


    with s3:

        st.metric(
            "Total Launches",
            f"{int(selected_site['total_launches']):,}",
        )


    with s4:

        st.metric(
            "Success Rate",
            f"{selected_site['success_rate']:.1%}",
        )


    s5, s6, s7, s8 = st.columns(4)


    with s5:

        st.metric(
            "Launch Pads",
            int(selected_site["launch_pads"]),
        )


    with s6:

        st.metric(
            "Altitude",
            f"{selected_site['altitude_m']:,.0f} m",
        )


    with s7:

        status = (
            "Active"
            if selected_site["is_active_2024"] == 1
            else "Inactive"
        )

        st.metric(
            "Status",
            status,
        )


    with s8:

        st.metric(
            "Latitude Advantage",
            f"{selected_site['latitude_advantage']:.1f}",
        )


    # =====================================================
    # OPERATING PERIOD
    # =====================================================

    st.markdown(
        "### 📅 Operating Period"
    )


    p1, p2 = st.columns(2)


    with p1:

        st.metric(
            "Active From",
            str(
                selected_site[
                    "active_from"
                ]
            ),
        )


    with p2:

        active_to = selected_site[
            "active_to"
        ]

        if pd.isna(active_to):

            active_to = "Present"

        st.metric(
            "Active To",
            str(active_to),
        )


    # =====================================================
    # SITE LOCATION
    # =====================================================

    st.markdown(
        "### 📍 Launch-Site Location"
    )


    location_data = pd.DataFrame(
        {
            "latitude": [
                selected_site[
                    "latitude"
                ]
            ],
            "longitude": [
                selected_site[
                    "longitude"
                ]
            ],
        }
    )


    if (
        pd.notna(
            selected_site["latitude"]
        )
        and
        pd.notna(
            selected_site["longitude"]
        )
    ):

        st.map(
            location_data,
            latitude="latitude",
            longitude="longitude",
            size=100,
        )

    else:

        st.info(
            "Location coordinates are unavailable."
        )


else:

    st.info(
        "No launch sites are available."
    )


# =========================================================
# DATA TABLE
# =========================================================

st.markdown("---")

st.markdown(
    "## 📋 Launch-Site Dataset"
)


st.dataframe(
    filtered_sites,
    width="stretch",
    hide_index=True,
)


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "Satellite Launch Intelligence • "
    "Launch-site data from launch_sites.csv • "
    "Public descriptions and images are retrieved "
    "from Wikipedia where available."
)
