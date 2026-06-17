import os
import re

import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="BCFOOD Recommended Hours Dashboard",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# BCFOOD BRANDING
# =========================================================
COMPANY_NAME = "BCFOOD"
COMPANY_SUBTITLE = (
    "Bargaining Council For The Food, Retail, Restaurant, Catering & Allied Trades"
)

PRIMARY = "#17406D"
PRIMARY_DARK = "#112F51"
SECONDARY = "#0F6FC6"
ACCENT = "#009DD9"
ACCENT_DARK = "#0B5294"
LIGHT_BLUE = "#DBEFF9"
SOFT_BLUE = "#F3FAFD"
TEAL = "#0BD0D9"
SLATE = "#405060"
ORANGE = "#F49100"

BCFOOD_SEQUENCE = [
    PRIMARY,
    SECONDARY,
    ACCENT,
    TEAL,
    "#10CF9B",
    "#7CCA62",
    "#A5C249",
    ORANGE,
]

# =========================================================
# FILE PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "Data for python.xlsx")
LOGO_FILE = os.path.join(BASE_DIR, "bcfood_logo.png")


def show_logo(width=260):
    """Display BCFOOD logo if the logo file exists."""
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=width)
    else:
        st.warning("Logo file not found. Please place bcfood_logo.png in the same folder.")


def show_sidebar_logo():
    """Display BCFOOD logo in sidebar if the logo file exists."""
    if os.path.exists(LOGO_FILE):
        st.sidebar.image(LOGO_FILE, use_container_width=True)


# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    f"""
    <style>
        h1, h2, h3 {{
            color: {PRIMARY};
        }}

        [data-testid="stSidebar"] {{
            background-color: {LIGHT_BLUE};
        }}

        div[data-testid="stMetric"] {{
            background-color: {SOFT_BLUE};
            border: 1px solid {LIGHT_BLUE};
            padding: 14px;
            border-radius: 12px;
        }}

        div[data-testid="stMetric"] label {{
            color: {SLATE};
        }}

        .stButton > button {{
            border-color: {ACCENT};
            color: {PRIMARY};
            border-radius: 20px;
        }}

        .stButton > button:hover {{
            border-color: {PRIMARY};
            color: {PRIMARY};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# TITLE
# =========================================================
header_logo, header_text = st.columns([1.1, 4.5])

with header_logo:
    show_logo(width=260)

with header_text:
    st.title("BCFOOD Recommended Hours Dashboard")
    st.caption(
        "Filter by location and Range - Total, compare actual hours, "
        "review recommendations, and analyse same-restaurant performance across locations."
    )

# =========================================================
# FILE UPLOAD / AUTO LOAD
# =========================================================
show_sidebar_logo()
st.sidebar.header("Upload Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload Excel Spreadsheet",
    type=["xlsx", "xls"],
)


def load_excel(file_source):
    return pd.read_excel(file_source, sheet_name=0, header=0)


if uploaded_file is not None:
    df_raw = load_excel(uploaded_file)
elif os.path.exists(DEFAULT_FILE):
    df_raw = load_excel(DEFAULT_FILE)
else:
    st.info("Please upload your Excel spreadsheet using the upload box on the left sidebar.")
    st.stop()

# Clean column names
df_raw.columns = df_raw.columns.astype(str).str.strip()

# =========================================================
# REQUIRED COLUMNS
# =========================================================
required_columns = [
    "Name",
    "Location",
    "Range - Total",
    "Total weekly",
    "Total Monthly",
]

missing_columns = [col for col in required_columns if col not in df_raw.columns]

if missing_columns:
    st.error("Some required columns are missing from the spreadsheet.")
    st.write("Missing columns:")
    st.write(missing_columns)

    st.write("Columns found in your spreadsheet:")
    st.write(list(df_raw.columns))

    st.stop()

df = df_raw[required_columns].copy()

# =========================================================
# RANGE RECOMMENDATIONS
# =========================================================
RANGE_ORDER = [
    "01 - 09 hours",
    "10 - 14 hours",
    "15 to 18 hours",
    "19 to 24 hours",
]

RANGE_RECOMMENDATIONS = {
    "01 - 09 hours": {
        "Recommended Monthly Hours": 140,
        "Recommendation": "Recommended hours per month - 140 hours",
    },
    "10 - 14 hours": {
        "Recommended Monthly Hours": 160,
        "Recommendation": "Recommended hours per month - Min 160 hours",
    },
    "15 to 18 hours": {
        "Recommended Monthly Hours": 180,
        "Recommendation": "Recommended hours per month - Min 180 hours",
    },
    "19 to 24 hours": {
        "Recommended Monthly Hours": 195,
        "Recommendation": "Recommended hours per month - Min 195 hours",
    },
}


def normalise_range_total(value):
    """Standardise known Range - Total labels while keeping unknown labels visible."""
    raw_value = str(value).strip()

    if raw_value.lower() in ["nan", "none", "", "not specified"]:
        return "Not specified"

    numbers = [int(number) for number in re.findall(r"\d+", raw_value)]

    if len(numbers) >= 2:
        start, end = numbers[0], numbers[1]

        if start <= 1 and end <= 9:
            return "01 - 09 hours"
        if 10 <= start <= 14 and 10 <= end <= 14:
            return "10 - 14 hours"
        if 15 <= start <= 18 and 15 <= end <= 18:
            return "15 to 18 hours"
        if 19 <= start <= 24 and 19 <= end <= 24:
            return "19 to 24 hours"

    return raw_value


def recommendation_text(range_value):
    return RANGE_RECOMMENDATIONS.get(
        range_value,
        {"Recommendation": "No recommendation available"},
    )["Recommendation"]


def recommendation_hours(range_value):
    return RANGE_RECOMMENDATIONS.get(
        range_value,
        {"Recommended Monthly Hours": pd.NA},
    )["Recommended Monthly Hours"]


def sort_range_values(values):
    def sort_key(value):
        if value in RANGE_ORDER:
            return (RANGE_ORDER.index(value), value)
        if value == "Not specified":
            return (998, value)
        return (999, str(value))

    return sorted(values, key=sort_key)


# =========================================================
# CLEAN DATA
# =========================================================
df["Name"] = df["Name"].astype(str).str.strip()
df["Location"] = df["Location"].astype(str).str.strip()
df["Range - Total"] = df["Range - Total"].apply(normalise_range_total)

df["Total weekly"] = pd.to_numeric(df["Total weekly"], errors="coerce")
df["Total Monthly"] = pd.to_numeric(df["Total Monthly"], errors="coerce")

df = df[
    df["Location"].notna()
    & (df["Location"] != "")
    & (df["Location"].str.lower() != "nan")
]

df["Recommendation"] = df["Range - Total"].apply(recommendation_text)
df["Recommended Monthly Hours"] = df["Range - Total"].apply(recommendation_hours)

# =========================================================
# RESTAURANT / COMPANY NAME CLEANING
# =========================================================
def clean_company_text(value):
    value = str(value).upper().strip()
    value = re.sub(r"[^A-Z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


BRAND_KEYWORDS = {
    "BURGER KING": "Burger King",
    "DEBONAIRS": "Debonairs",
    "DEBONAIRS PIZZA": "Debonairs",
    "KFC": "KFC",
    "MCDONALD": "McDonald's",
    "MCDONALDS": "McDonald's",
    "NANDOS": "Nando's",
    "NANDO": "Nando's",
    "STEERS": "Steers",
    "FISHAWAYS": "Fishaways",
    "WIMPY": "Wimpy",
    "SPUR": "Spur",
    "ROMANS PIZZA": "Romans Pizza",
    "ROMAN S PIZZA": "Romans Pizza",
    "CHICKEN LICKEN": "Chicken Licken",
    "GALITOS": "Galito's",
    "GALITO": "Galito's",
    "PIZZA HUT": "Pizza Hut",
    "SUBWAY": "Subway",
    "SHOPRITE": "Shoprite",
    "CHECKERS": "Checkers",
    "PICK N PAY": "Pick n Pay",
    "PNP": "Pick n Pay",
    "WOOLWORTHS": "Woolworths",
    "CLICKS": "Clicks",
    "DIS CHEM": "Dis-Chem",
    "DISCHEM": "Dis-Chem",
    "BOXER": "Boxer",
    "PEP": "PEP",
    "ACKERMANS": "Ackermans",
    "MR PRICE": "Mr Price",
    "TOTAL": "Total",
    "SASOL": "Sasol",
    "ENGEN": "Engen",
    "BP": "BP",
    "SHELL": "Shell",
}


def identify_company_group(name):
    cleaned = clean_company_text(name)

    for keyword, brand_name in BRAND_KEYWORDS.items():
        if keyword in cleaned:
            return brand_name

    return cleaned.title()


df["Company Group"] = df["Name"].apply(identify_company_group)

# =========================================================
# BUTTON SLICER HELPERS
# =========================================================
def button_multiselect(label, options, default, key, container=st):
    """
    Render a button-style multi-select slicer.
    Uses st.pills when available; otherwise falls back to checkboxes.
    """
    options = list(options)
    default = [item for item in default if item in options]

    if hasattr(container, "pills"):
        selected = container.pills(
            label,
            options=options,
            default=default,
            selection_mode="multi",
            key=key,
        )
        return list(selected or [])

    container.markdown(f"**{label}**")
    selected = []
    columns = container.columns(2)

    for index, option in enumerate(options):
        option_key = f"{key}_{index}_{str(option)}"
        with columns[index % 2]:
            if st.checkbox(str(option), value=option in default, key=option_key):
                selected.append(option)

    return selected


# =========================================================
# SIDEBAR SLICERS
# =========================================================
st.sidebar.header("Dashboard Slicers")

locations = sorted(df["Location"].dropna().unique())

selected_locations = button_multiselect(
    "Select Location",
    options=locations,
    default=locations[:1] if len(locations) > 0 else [],
    key="location_slicer",
    container=st.sidebar,
)

if not selected_locations:
    st.warning("Please select at least one location from the Location slicer on the left.")
    st.stop()

location_filtered_df = df[df["Location"].isin(selected_locations)].copy()
range_options = sort_range_values(location_filtered_df["Range - Total"].dropna().unique())

selected_ranges = button_multiselect(
    "Select Range - Total",
    options=range_options,
    default=range_options,
    key="range_total_slicer",
    container=st.sidebar,
)

if not selected_ranges:
    st.warning("Please select at least one Range - Total value from the slicer on the left.")
    st.stop()

filtered_df = location_filtered_df[
    location_filtered_df["Range - Total"].isin(selected_ranges)
].copy()

if filtered_df.empty:
    st.warning("No records match the selected Location and Range - Total slicers.")
    st.stop()

# =========================================================
# OVERALL KPI SUMMARY - AVERAGES
# =========================================================
st.subheader("Overall Summary")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Selected Locations", f"{len(selected_locations):,}")
kpi2.metric("Selected Ranges", f"{len(selected_ranges):,}")
kpi3.metric("Weekly Average Hours", f"{filtered_df['Total weekly'].mean():,.2f}")
kpi4.metric("Monthly Average Hours", f"{filtered_df['Total Monthly'].mean():,.2f}")

st.divider()

# =========================================================
# RANGE RECOMMENDATION SUMMARY
# =========================================================
st.subheader("Range - Total Recommendations")

recommendation_summary = pd.DataFrame(
    [
        {
            "Range - Total": range_value,
            "Recommended Monthly Hours": recommendation_hours(range_value),
            "Recommendation": recommendation_text(range_value),
        }
        for range_value in selected_ranges
    ]
)

st.dataframe(
    recommendation_summary,
    use_container_width=True,
    height=min(260, 80 + (len(recommendation_summary) * 38)),
    hide_index=True,
)

st.markdown("### Organisations for Selected Location and Range")

organisation_table = filtered_df[
    [
        "Location",
        "Range - Total",
        "Name",
        "Total weekly",
        "Total Monthly",
        "Recommendation",
    ]
].copy()

organisation_table = organisation_table.rename(
    columns={
        "Name": "Organisation",
        "Total weekly": "Weekly Hours",
        "Total Monthly": "Monthly Hours",
    }
)

organisation_table["Weekly Hours"] = organisation_table["Weekly Hours"].round(2)
organisation_table["Monthly Hours"] = organisation_table["Monthly Hours"].round(2)

organisation_table = organisation_table.sort_values(
    ["Location", "Range - Total", "Organisation"],
    ascending=[True, True, True],
)

st.dataframe(
    organisation_table,
    use_container_width=True,
    height=400,
    hide_index=True,
)

st.divider()

# =========================================================
# LOCATION SUMMARY TABLE - AVERAGES
# =========================================================
st.subheader("Selected Location Summary")

location_summary = (
    filtered_df.groupby("Location", as_index=False)
    .agg(
        Number_of_Records=("Name", "count"),
        Weekly_Average_Hours=("Total weekly", "mean"),
        Monthly_Average_Hours=("Total Monthly", "mean"),
    )
    .sort_values("Weekly_Average_Hours", ascending=False)
)

location_summary = location_summary.rename(
    columns={
        "Number_of_Records": "Number of Records",
        "Weekly_Average_Hours": "Weekly Average Hours",
        "Monthly_Average_Hours": "Monthly Average Hours",
    }
)

location_summary["Weekly Average Hours"] = location_summary[
    "Weekly Average Hours"
].round(2)
location_summary["Monthly Average Hours"] = location_summary[
    "Monthly Average Hours"
].round(2)

st.dataframe(
    location_summary,
    use_container_width=True,
    height=250,
    hide_index=True,
)

st.divider()

# =========================================================
# COMPARISON GRAPHS
# =========================================================
st.subheader("Comparison Graphs")

# Exclude locations with fewer than 10 filtered entries.
location_counts = filtered_df.groupby("Location").size().reset_index(name="Entry Count")
valid_locations = location_counts[location_counts["Entry Count"] >= 10]["Location"].tolist()

comparison_df = filtered_df[filtered_df["Location"].isin(valid_locations)].copy()
comparison_df = comparison_df.dropna(subset=["Total weekly"])

# =========================================================
# HIGHEST AND LOWEST WEEKLY HOURS BY LOCATION - ACTUAL
# =========================================================
st.markdown("### Highest and Lowest Weekly Hours by Location")
st.caption(
    "Locations with fewer than 10 filtered entries are excluded. "
    "Bar labels show only the actual weekly hours."
)

if len(comparison_df) > 0:
    highest_rows = comparison_df.loc[
        comparison_df.groupby("Location")["Total weekly"].idxmax()
    ].copy()

    lowest_rows = comparison_df.loc[
        comparison_df.groupby("Location")["Total weekly"].idxmin()
    ].copy()

    highest_rows["Measure"] = "Highest Weekly Hours"
    lowest_rows["Measure"] = "Lowest Weekly Hours"

    high_low_long = pd.concat([highest_rows, lowest_rows], ignore_index=True)

    high_low_long["Weekly Hours"] = high_low_long["Total weekly"].round(2)

    high_low_fig = px.bar(
        high_low_long,
        x="Location",
        y="Weekly Hours",
        color="Measure",
        barmode="group",
        text="Weekly Hours",
        hover_data={
            "Company Group": True,
            "Name": True,
            "Weekly Hours": ":.2f",
            "Measure": True,
            "Location": True,
        },
        title="Highest vs Lowest Weekly Hours by Location",
        color_discrete_map={
            "Highest Weekly Hours": PRIMARY,
            "Lowest Weekly Hours": ACCENT,
        },
    )

    high_low_fig.update_traces(
        texttemplate="%{text:,.2f} hrs",
        textposition="inside",
        textangle=-90,
        textfont_size=12,
        insidetextanchor="middle",
        cliponaxis=False,
    )

    high_low_fig.update_layout(
        height=700,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color=PRIMARY,
        xaxis_title="Location",
        yaxis_title="Weekly Hours",
        xaxis_tickangle=-45,
        legend_title_text="Measure",
        bargap=0.45,
        bargroupgap=0.35,
    )

    st.plotly_chart(high_low_fig, use_container_width=True)

    st.markdown("### Highest and Lowest Weekly Hours Table")

    high_table = highest_rows[["Location", "Total weekly"]].copy()
    high_table = high_table.rename(
        columns={"Total weekly": "Highest Weekly Hours"}
    )

    low_table = lowest_rows[["Location", "Total weekly"]].copy()
    low_table = low_table.rename(
        columns={"Total weekly": "Lowest Weekly Hours"}
    )

    high_low_table = pd.merge(high_table, low_table, on="Location", how="inner")
    high_low_table = pd.merge(high_low_table, location_counts, on="Location", how="left")

    high_low_table["Highest Weekly Hours"] = high_low_table[
        "Highest Weekly Hours"
    ].round(2)
    high_low_table["Lowest Weekly Hours"] = high_low_table[
        "Lowest Weekly Hours"
    ].round(2)

    high_low_table = high_low_table[
        [
            "Location",
            "Entry Count",
            "Highest Weekly Hours",
            "Lowest Weekly Hours",
        ]
    ].sort_values("Highest Weekly Hours", ascending=False)

    st.dataframe(
        high_low_table,
        use_container_width=True,
        height=400,
        hide_index=True,
    )
else:
    st.info("There are no selected locations with at least 10 filtered entries.")

st.divider()

# =========================================================
# DASHBOARD PER SELECTED LOCATION
# =========================================================
st.subheader("Location Details")

location_tabs = st.tabs([str(location) for location in selected_locations])

for tab, location in zip(location_tabs, selected_locations):
    with tab:
        location_df = filtered_df[filtered_df["Location"] == location].copy()

        st.markdown(f"## {str(location).title()}")

        if location_df.empty:
            st.info("No records for this location after applying the Range - Total slicer.")
            continue

        # =================================================
        # ACTUAL HOURS TABLE
        # =================================================
        table_df = location_df[
            [
                "Name",
                "Range - Total",
                "Total weekly",
                "Total Monthly",
                "Recommendation",
            ]
        ].copy()

        table_df = table_df.rename(
            columns={
                "Name": "Organisation",
                "Total weekly": "Weekly Hours",
                "Total Monthly": "Monthly Hours",
            }
        )

        table_df["Weekly Hours"] = table_df["Weekly Hours"].round(2)
        table_df["Monthly Hours"] = table_df["Monthly Hours"].round(2)

        table_df = table_df.sort_values("Weekly Hours", ascending=False)

        # =============================================
        # LOCATION KPIs - AVERAGES
        # =============================================
        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Organisations", f"{table_df['Organisation'].nunique():,}")
        c2.metric("Selected Ranges", f"{location_df['Range - Total'].nunique():,}")
        c3.metric("Weekly Average Hours", f"{table_df['Weekly Hours'].mean():,.2f}")
        c4.metric("Monthly Average Hours", f"{table_df['Monthly Hours'].mean():,.2f}")

        # =============================================
        # SCROLLABLE TABLE - ACTUAL HOURS
        # =============================================
        st.markdown("### Organisation, Weekly Hours and Monthly Hours Table")

        st.dataframe(
            table_df,
            use_container_width=True,
            height=450,
            hide_index=True,
        )

        # =============================================
        # WEEKLY HOURS BAR CHART - ACTUAL HOURS
        # =============================================
        st.markdown("### Weekly Hours Graph")

        if len(table_df) > 0:
            if len(table_df) == 1:
                chart_df = table_df.copy()
            else:
                top_n = st.slider(
                    f"Number of organisations to show in graph for {str(location).title()}",
                    min_value=1,
                    max_value=len(table_df),
                    value=min(30, len(table_df)),
                    key=f"top_n_{location}",
                )

                chart_df = table_df.head(top_n)

            weekly_fig = px.bar(
                chart_df,
                x="Weekly Hours",
                y="Organisation",
                orientation="h",
                text="Weekly Hours",
                title=f"Actual Weekly Hours by Organisation - {str(location).title()}",
                color_discrete_sequence=[PRIMARY],
            )

            weekly_fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=max(500, len(chart_df) * 30),
                plot_bgcolor="white",
                paper_bgcolor="white",
                title_font_color=PRIMARY,
                xaxis_title="Weekly Hours",
                yaxis_title="Organisation",
                bargap=0.35,
            )

            weekly_fig.update_traces(
                texttemplate="%{text:,.2f}",
                textposition="outside",
                marker_color=PRIMARY,
            )

            st.plotly_chart(weekly_fig, use_container_width=True)
        else:
            st.info("No weekly hours records available for this location.")

        # =============================================
        # RANGE - TOTAL PIE CHART
        # =============================================
        st.markdown("### Range - Total Pie Chart")

        range_df = (
            location_df.groupby("Range - Total", as_index=False)
            .agg(
                Count=("Name", "count"),
                Weekly_Average_Hours=("Total weekly", "mean"),
                Monthly_Average_Hours=("Total Monthly", "mean"),
            )
            .sort_values("Count", ascending=False)
        )

        range_df["Weekly_Average_Hours"] = range_df["Weekly_Average_Hours"].round(2)
        range_df["Monthly_Average_Hours"] = range_df["Monthly_Average_Hours"].round(2)
        range_df["Recommendation"] = range_df["Range - Total"].apply(recommendation_text)

        range_df = range_df.rename(
            columns={
                "Weekly_Average_Hours": "Weekly Average Hours",
                "Monthly_Average_Hours": "Monthly Average Hours",
            }
        )

        if len(range_df) > 0:
            pie_fig = px.pie(
                range_df,
                names="Range - Total",
                values="Count",
                title=f"Range - Total Distribution - {str(location).title()}",
                color_discrete_sequence=BCFOOD_SEQUENCE,
            )

            pie_fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
            )

            pie_fig.update_layout(
                height=550,
                title_font_color=PRIMARY,
                paper_bgcolor="white",
            )

            st.plotly_chart(pie_fig, use_container_width=True)

            st.markdown("### Range - Total Table")

            st.dataframe(
                range_df,
                use_container_width=True,
                height=300,
                hide_index=True,
            )
        else:
            st.info("No Range - Total records available for this location.")

        st.divider()

# =========================================================
# SAME RESTAURANT ACROSS DIFFERENT LOCATIONS - AVERAGES
# MOVED TO END OF DASHBOARD
# =========================================================
st.subheader("Same Restaurant Comparison Across Locations")
st.caption(
    "This compares restaurants that appear in more than one selected location. "
    "Locations with fewer than 10 filtered entries are excluded."
)

same_company_base = comparison_df.copy()

company_location_summary = (
    same_company_base.groupby(["Company Group", "Location"], as_index=False)
    .agg(
        Entry_Count=("Name", "count"),
        Weekly_Average_Hours=("Total weekly", "mean"),
        Highest_Weekly_Hours=("Total weekly", "max"),
        Lowest_Weekly_Hours=("Total weekly", "min"),
        Monthly_Average_Hours=("Total Monthly", "mean"),
    )
)

if len(company_location_summary) > 0:
    company_location_summary["Weekly_Average_Hours"] = company_location_summary[
        "Weekly_Average_Hours"
    ].round(2)
    company_location_summary["Highest_Weekly_Hours"] = company_location_summary[
        "Highest_Weekly_Hours"
    ].round(2)
    company_location_summary["Lowest_Weekly_Hours"] = company_location_summary[
        "Lowest_Weekly_Hours"
    ].round(2)
    company_location_summary["Monthly_Average_Hours"] = company_location_summary[
        "Monthly_Average_Hours"
    ].round(2)

    company_location_counts = (
        company_location_summary.groupby("Company Group")["Location"]
        .nunique()
        .reset_index(name="Number of Locations")
    )

    companies_in_multiple_locations = company_location_counts[
        company_location_counts["Number of Locations"] >= 2
    ]["Company Group"].tolist()

    company_location_summary = company_location_summary[
        company_location_summary["Company Group"].isin(companies_in_multiple_locations)
    ].copy()

if len(company_location_summary) > 0:
    company_options = sorted(company_location_summary["Company Group"].unique())

    priority_companies = [
        company
        for company in company_options
        if company
        in [
            "Burger King",
            "Debonairs",
            "KFC",
            "McDonald's",
            "Nando's",
            "Steers",
            "Chicken Licken",
            "Galito's",
        ]
    ]

    default_companies = priority_companies[:8] if priority_companies else company_options[:8]

    selected_companies = button_multiselect(
        "Select restaurants to compare across locations",
        options=company_options,
        default=default_companies,
        key="company_comparison_slicer",
        container=st,
    )

    selected_company_df = company_location_summary[
        company_location_summary["Company Group"].isin(selected_companies)
    ].copy()

    if len(selected_company_df) > 0:
        company_compare_fig = px.bar(
            selected_company_df,
            x="Company Group",
            y="Weekly_Average_Hours",
            color="Location",
            barmode="group",
            text="Weekly_Average_Hours",
            hover_data={
                "Company Group": True,
                "Location": True,
                "Weekly_Average_Hours": ":.2f",
                "Highest_Weekly_Hours": ":.2f",
                "Lowest_Weekly_Hours": ":.2f",
                "Monthly_Average_Hours": ":.2f",
            },
            title="Weekly Average Hours for Same Restaurants Across Locations",
            color_discrete_sequence=BCFOOD_SEQUENCE,
        )

        company_compare_fig.update_traces(
            texttemplate="%{text:,.2f} hrs",
            textposition="outside",
            textfont_size=11,
        )

        company_compare_fig.update_layout(
            height=750,
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_font_color=PRIMARY,
            xaxis_title="Restaurant",
            yaxis_title="Weekly Average Hours",
            legend_title_text="Location",
            xaxis_tickangle=-30,
            bargap=0.45,
            bargroupgap=0.35,
        )

        st.plotly_chart(company_compare_fig, use_container_width=True)

        st.markdown("### Same Restaurant Comparison Table")

        same_company_table = selected_company_df.rename(
            columns={
                "Company Group": "Restaurant",
                "Entry_Count": "Entry Count",
                "Weekly_Average_Hours": "Weekly Average Hours",
                "Highest_Weekly_Hours": "Highest Weekly Hours",
                "Lowest_Weekly_Hours": "Lowest Weekly Hours",
                "Monthly_Average_Hours": "Monthly Average Hours",
            }
        )

        same_company_table = same_company_table[
            [
                "Restaurant",
                "Location",
                "Entry Count",
                "Weekly Average Hours",
                "Highest Weekly Hours",
                "Lowest Weekly Hours",
                "Monthly Average Hours",
            ]
        ].sort_values(["Restaurant", "Location"])

        st.dataframe(
            same_company_table,
            use_container_width=True,
            height=400,
            hide_index=True,
        )
    else:
        st.info("Please select at least one restaurant to compare.")
else:
    st.info(
        "No same-restaurant matches were found across different selected locations "
        "after excluding locations with fewer than 10 filtered entries."
    )

# =========================================================
# DOWNLOAD FILTERED DATA
# =========================================================
st.sidebar.divider()
st.sidebar.header("Download")

download_df = filtered_df.rename(
    columns={
        "Name": "Organisation",
        "Total weekly": "Weekly Hours",
        "Total Monthly": "Monthly Hours",
    }
)

csv_data = download_df.to_csv(index=False).encode("utf-8")

st.sidebar.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="bcfood_filtered_location_range_data.csv",
    mime="text/csv",
)
