import os
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# PAGE SETUP
# =========================================================
st.set_page_config(
    page_title="ZF Rewards Dashboard",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# COLORS
# =========================================================
GREEN = "#008000"
LIGHT_GREEN = "#EAF7EA"

# =========================================================
# CUSTOM CSS
# =========================================================
st.markdown(
    f"""
    <style>
        h1, h2, h3 {{
            color: {GREEN};
        }}

        [data-testid="stSidebar"] {{
            background-color: {LIGHT_GREEN};
        }}

        div[data-testid="stMetric"] {{
            background-color: #F4FBF4;
            border: 1px solid #CFE8CF;
            padding: 14px;
            border-radius: 12px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# TITLE
# =========================================================
st.title("ZF Rewards Dashboard")
st.caption(
    "Filter by location and compare weekly average hours, monthly average hours, "
    "range totals, and same-company performance across locations."
)

# =========================================================
# FILE UPLOAD / AUTO LOAD
# =========================================================
st.sidebar.header("Upload Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload Excel Spreadsheet",
    type=["xlsx", "xls"]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FILE = os.path.join(BASE_DIR, "Data for python.xlsx")


def load_excel(file_source):
    return pd.read_excel(file_source, sheet_name=0, header=0)


if uploaded_file is not None:
    df_raw = load_excel(uploaded_file)

elif os.path.exists(DEFAULT_FILE):
    df_raw = load_excel(DEFAULT_FILE)

else:
    st.info(
        "Please upload your Excel spreadsheet using the upload box on the left sidebar."
    )
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
    "Total Monthly"
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
# CLEAN DATA
# =========================================================
df["Name"] = df["Name"].astype(str).str.strip()
df["Location"] = df["Location"].astype(str).str.strip()
df["Range - Total"] = df["Range - Total"].astype(str).str.strip()

# Keep blanks as NaN instead of forcing them to zero
df["Total weekly"] = pd.to_numeric(df["Total weekly"], errors="coerce")
df["Total Monthly"] = pd.to_numeric(df["Total Monthly"], errors="coerce")

# Remove blank or invalid locations
df = df[
    df["Location"].notna()
    & (df["Location"] != "")
    & (df["Location"].str.lower() != "nan")
]

# Clean blank range values
df["Range - Total"] = df["Range - Total"].replace(
    ["nan", "None", "", "NaN"],
    "Not specified"
)

# =========================================================
# COMPANY NAME CLEANING
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
    "SHELL": "Shell"
}


def identify_company_group(name):
    cleaned = clean_company_text(name)

    for keyword, brand_name in BRAND_KEYWORDS.items():
        if keyword in cleaned:
            return brand_name

    return cleaned.title()


df["Company Group"] = df["Name"].apply(identify_company_group)

# =========================================================
# SIDEBAR LOCATION SLICER
# =========================================================
st.sidebar.header("Location Slicer")

locations = sorted(df["Location"].dropna().unique())

selected_locations = st.sidebar.multiselect(
    "Select Location",
    options=locations,
    default=locations[:1] if len(locations) > 0 else []
)

if not selected_locations:
    st.warning("Please select at least one location from the slicer on the left.")
    st.stop()

filtered_df = df[df["Location"].isin(selected_locations)].copy()

# =========================================================
# OVERALL KPI SUMMARY
# =========================================================
st.subheader("Overall Summary")

kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric("Selected Locations", f"{len(selected_locations):,}")
kpi2.metric("Weekly Average Hours", f"{filtered_df['Total weekly'].mean():,.2f}")
kpi3.metric("Monthly Average Hours", f"{filtered_df['Total Monthly'].mean():,.2f}")

st.divider()

# =========================================================
# LOCATION SUMMARY TABLE
# =========================================================
st.subheader("Selected Location Summary")

location_summary = (
    filtered_df
    .groupby("Location", as_index=False)
    .agg(
        Number_of_Records=("Name", "count"),
        Weekly_Average_Hours=("Total weekly", "mean"),
        Monthly_Average_Hours=("Total Monthly", "mean")
    )
    .sort_values("Weekly_Average_Hours", ascending=False)
)

location_summary = location_summary.rename(columns={
    "Number_of_Records": "Number of Records",
    "Weekly_Average_Hours": "Weekly Average Hours",
    "Monthly_Average_Hours": "Monthly Average Hours"
})

location_summary["Weekly Average Hours"] = location_summary["Weekly Average Hours"].round(2)
location_summary["Monthly Average Hours"] = location_summary["Monthly Average Hours"].round(2)

st.dataframe(
    location_summary,
    use_container_width=True,
    height=250,
    hide_index=True
)

st.divider()

# =========================================================
# COMPARISON GRAPHS
# =========================================================
st.subheader("Comparison Graphs")

# Leave out locations with fewer than 10 entries
location_counts = df.groupby("Location").size().reset_index(name="Entry Count")
valid_locations = location_counts[location_counts["Entry Count"] >= 10]["Location"].tolist()

comparison_df = df[df["Location"].isin(valid_locations)].copy()
comparison_df = comparison_df.dropna(subset=["Total weekly"])

# =========================================================
# HIGHEST AND LOWEST WEEKLY HOURS BY LOCATION
# =========================================================
st.markdown("### Highest and Lowest Weekly Hours by Location")
st.caption("Locations with fewer than 10 entries are excluded.")

if len(comparison_df) > 0:

    high_low_df = (
        comparison_df
        .groupby("Location", as_index=False)
        .agg(
            Highest_Weekly_Hours=("Total weekly", "max"),
            Lowest_Weekly_Hours=("Total weekly", "min"),
            Entry_Count=("Name", "count")
        )
        .sort_values("Highest_Weekly_Hours", ascending=False)
    )

    high_low_df["Highest Weekly Hours"] = high_low_df["Highest_Weekly_Hours"].round(2)
    high_low_df["Lowest Weekly Hours"] = high_low_df["Lowest_Weekly_Hours"].round(2)

    high_low_long = high_low_df.melt(
        id_vars=["Location", "Entry_Count"],
        value_vars=["Highest Weekly Hours", "Lowest Weekly Hours"],
        var_name="Measure",
        value_name="Weekly Hours"
    )

    high_low_fig = px.bar(
        high_low_long,
        x="Location",
        y="Weekly Hours",
        color="Measure",
        barmode="group",
        text="Weekly Hours",
        title="Highest vs Lowest Weekly Hours by Location"
    )

    high_low_fig.update_traces(
        texttemplate="%{text:,.2f}",
        textposition="outside"
    )

    high_low_fig.update_layout(
        height=600,
        plot_bgcolor="white",
        paper_bgcolor="white",
        title_font_color=GREEN,
        xaxis_title="Location",
        yaxis_title="Weekly Hours",
        xaxis_tickangle=-45,
        legend_title_text="Measure"
    )

    st.plotly_chart(high_low_fig, use_container_width=True)

    st.markdown("### Highest and Lowest Weekly Hours Table")

    display_high_low_df = high_low_df[[
        "Location",
        "Entry_Count",
        "Highest Weekly Hours",
        "Lowest Weekly Hours"
    ]].rename(columns={
        "Entry_Count": "Entry Count"
    })

    st.dataframe(
        display_high_low_df,
        use_container_width=True,
        height=350,
        hide_index=True
    )

else:
    st.info("There are no locations with at least 10 entries.")

st.divider()

# =========================================================
# SAME COMPANY ACROSS DIFFERENT LOCATIONS
# =========================================================
st.markdown("### Same Company Comparison Across Locations")
st.caption(
    "This compares companies that appear in more than one location. "
    "Locations with fewer than 10 entries are excluded."
)

same_company_base = comparison_df.copy()

company_location_summary = (
    same_company_base
    .groupby(["Company Group", "Location"], as_index=False)
    .agg(
        Entry_Count=("Name", "count"),
        Weekly_Average_Hours=("Total weekly", "mean"),
        Highest_Weekly_Hours=("Total weekly", "max"),
        Lowest_Weekly_Hours=("Total weekly", "min"),
        Monthly_Average_Hours=("Total Monthly", "mean")
    )
)

company_location_summary["Weekly_Average_Hours"] = company_location_summary["Weekly_Average_Hours"].round(2)
company_location_summary["Highest_Weekly_Hours"] = company_location_summary["Highest_Weekly_Hours"].round(2)
company_location_summary["Lowest_Weekly_Hours"] = company_location_summary["Lowest_Weekly_Hours"].round(2)
company_location_summary["Monthly_Average_Hours"] = company_location_summary["Monthly_Average_Hours"].round(2)

company_location_counts = (
    company_location_summary
    .groupby("Company Group")["Location"]
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
        company for company in company_options
        if company in ["Burger King", "Debonairs", "KFC", "McDonald's", "Nando's", "Steers"]
    ]

    default_companies = priority_companies[:5] if priority_companies else company_options[:5]

    selected_companies = st.multiselect(
        "Select companies to compare across locations",
        options=company_options,
        default=default_companies
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
            title="Weekly Average Hours for Same Companies Across Locations"
        )

        company_compare_fig.update_traces(
            texttemplate="%{text:,.2f}",
            textposition="outside"
        )

        company_compare_fig.update_layout(
            height=650,
            plot_bgcolor="white",
            paper_bgcolor="white",
            title_font_color=GREEN,
            xaxis_title="Company",
            yaxis_title="Weekly Average Hours",
            legend_title_text="Location",
            xaxis_tickangle=-30
        )

        st.plotly_chart(company_compare_fig, use_container_width=True)

        st.markdown("### Same Company Comparison Table")

        same_company_table = selected_company_df.rename(columns={
            "Company Group": "Company",
            "Entry_Count": "Entry Count",
            "Weekly_Average_Hours": "Weekly Average Hours",
            "Highest_Weekly_Hours": "Highest Weekly Hours",
            "Lowest_Weekly_Hours": "Lowest Weekly Hours",
            "Monthly_Average_Hours": "Monthly Average Hours"
        })

        same_company_table = same_company_table[[
            "Company",
            "Location",
            "Entry Count",
            "Weekly Average Hours",
            "Highest Weekly Hours",
            "Lowest Weekly Hours",
            "Monthly Average Hours"
        ]].sort_values(["Company", "Location"])

        st.dataframe(
            same_company_table,
            use_container_width=True,
            height=400,
            hide_index=True
        )

    else:
        st.info("Please select at least one company to compare.")

else:
    st.info(
        "No same-company matches were found across different locations after excluding locations with fewer than 10 entries."
    )

st.divider()

# =========================================================
# DASHBOARD PER SELECTED LOCATION
# =========================================================
st.subheader("Location Details")

location_tabs = st.tabs([str(location) for location in selected_locations])

for tab, location in zip(location_tabs, selected_locations):

    with tab:
        location_df = df[df["Location"] == location].copy()

        st.markdown(f"## {str(location).title()}")

        table_df = (
            location_df
            .groupby("Name", as_index=False)
            .agg({
                "Total weekly": "mean",
                "Total Monthly": "mean"
            })
            .rename(columns={
                "Total weekly": "Weekly Average Hours",
                "Total Monthly": "Monthly Average Hours"
            })
            .sort_values("Weekly Average Hours", ascending=False)
        )

        table_df["Weekly Average Hours"] = table_df["Weekly Average Hours"].round(2)
        table_df["Monthly Average Hours"] = table_df["Monthly Average Hours"].round(2)

        # =============================================
        # LOCATION KPIs
        # =============================================
        c1, c2, c3 = st.columns(3)

        c1.metric("Names", f"{table_df['Name'].nunique():,}")
        c2.metric("Weekly Average Hours", f"{table_df['Weekly Average Hours'].mean():,.2f}")
        c3.metric("Monthly Average Hours", f"{table_df['Monthly Average Hours'].mean():,.2f}")

        # =============================================
        # SCROLLABLE TABLE
        # =============================================
        st.markdown("### Name, Weekly Average Hours and Monthly Average Hours Table")

        st.dataframe(
            table_df,
            use_container_width=True,
            height=450,
            hide_index=True
        )

        # =============================================
        # WEEKLY AVERAGE HOURS BAR CHART
        # =============================================
        st.markdown("### Weekly Average Hours Graph")

        if len(table_df) > 0:

            if len(table_df) == 1:
                chart_df = table_df.copy()
            else:
                top_n = st.slider(
                    f"Number of people/companies to show in graph for {str(location).title()}",
                    min_value=1,
                    max_value=len(table_df),
                    value=min(30, len(table_df)),
                    key=f"top_n_{location}"
                )

                chart_df = table_df.head(top_n)

            weekly_fig = px.bar(
                chart_df,
                x="Weekly Average Hours",
                y="Name",
                orientation="h",
                text="Weekly Average Hours",
                title=f"Weekly Average Hours by Name - {str(location).title()}",
                color_discrete_sequence=[GREEN]
            )

            weekly_fig.update_layout(
                yaxis=dict(autorange="reversed"),
                height=max(500, len(chart_df) * 30),
                plot_bgcolor="white",
                paper_bgcolor="white",
                title_font_color=GREEN,
                xaxis_title="Weekly Average Hours",
                yaxis_title="Name"
            )

            weekly_fig.update_traces(
                texttemplate="%{text:,.2f}",
                textposition="outside"
            )

            st.plotly_chart(
                weekly_fig,
                use_container_width=True
            )

        else:
            st.info("No weekly average records available for this location.")

        # =============================================
        # RANGE - TOTAL PIE CHART
        # =============================================
        st.markdown("### Range - Total Pie Chart")

        range_df = (
            location_df
            .groupby("Range - Total", as_index=False)
            .agg({
                "Name": "count",
                "Total weekly": "mean",
                "Total Monthly": "mean"
            })
            .rename(columns={
                "Name": "Count",
                "Total weekly": "Weekly Average Hours",
                "Total Monthly": "Monthly Average Hours"
            })
            .sort_values("Count", ascending=False)
        )

        range_df["Weekly Average Hours"] = range_df["Weekly Average Hours"].round(2)
        range_df["Monthly Average Hours"] = range_df["Monthly Average Hours"].round(2)

        if len(range_df) > 0:

            pie_fig = px.pie(
                range_df,
                names="Range - Total",
                values="Count",
                title=f"Range - Total Distribution - {str(location).title()}",
                color_discrete_sequence=px.colors.sequential.Greens
            )

            pie_fig.update_traces(
                textposition="inside",
                textinfo="percent+label"
            )

            pie_fig.update_layout(
                height=550,
                title_font_color=GREEN,
                paper_bgcolor="white"
            )

            st.plotly_chart(
                pie_fig,
                use_container_width=True
            )

            st.markdown("### Range - Total Table")

            st.dataframe(
                range_df,
                use_container_width=True,
                height=300,
                hide_index=True
            )

        else:
            st.info("No Range - Total records available for this location.")

        st.divider()

# =========================================================
# DOWNLOAD FILTERED DATA
# =========================================================
st.sidebar.divider()
st.sidebar.header("Download")

download_df = filtered_df.rename(columns={
    "Total weekly": "Weekly Hours",
    "Total Monthly": "Monthly Hours"
})

csv_data = download_df.to_csv(index=False).encode("utf-8")

st.sidebar.download_button(
    label="Download Filtered Data as CSV",
    data=csv_data,
    file_name="filtered_location_data.csv",
    mime="text/csv"
)
