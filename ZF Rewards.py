import os
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
st.caption("Filter by location and view Name, Weekly Average Hours, Monthly Average Hours, and Range Total charts.")

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
# REQUIRED COLUMNS FROM YOUR SPREADSHEET
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

df["Total weekly"] = pd.to_numeric(df["Total weekly"], errors="coerce").fillna(0)
df["Total Monthly"] = pd.to_numeric(df["Total Monthly"], errors="coerce").fillna(0)

df = df[
    df["Location"].notna()
    & (df["Location"] != "")
    & (df["Location"].str.lower() != "nan")
]

df["Range - Total"] = df["Range - Total"].replace(
    ["nan", "None", "", "NaN"],
    "Not specified"
)

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
# OVERALL KPI SUMMARY - AVERAGES ONLY
# =========================================================
st.subheader("Overall Summary")

kpi1, kpi2, kpi3 = st.columns(3)

kpi1.metric("Selected Locations", f"{len(selected_locations):,}")
kpi2.metric("Weekly Average Hours", f"{filtered_df['Total weekly'].mean():,.2f}")
kpi3.metric("Monthly Average Hours", f"{filtered_df['Total Monthly'].mean():,.2f}")

st.divider()

# =========================================================
# SELECTED LOCATION SUMMARY TABLE - AVERAGES ONLY
# =========================================================
st.subheader("Selected Location Summary")

location_summary = (
    filtered_df
    .groupby("Location", as_index=False)
    .agg({
        "Name": "count",
        "Total weekly": "mean",
        "Total Monthly": "mean"
    })
    .rename(columns={
        "Name": "Number of Records",
        "Total weekly": "Weekly Average Hours",
        "Total Monthly": "Monthly Average Hours"
    })
    .sort_values("Weekly Average Hours", ascending=False)
)

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
# DASHBOARD PER SELECTED LOCATION
# =========================================================
st.subheader("Location Details")

location_tabs = st.tabs([str(location) for location in selected_locations])

for tab, location in zip(location_tabs, selected_locations):

    with tab:
        location_df = df[df["Location"] == location].copy()

        st.markdown(f"## {str(location).title()}")

        # Average hours by Name
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
        # LOCATION KPIs - AVERAGES ONLY
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
                    f"Number of people to show in graph for {str(location).title()}",
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
