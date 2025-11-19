import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date
from who_growth_charts import WHOGrowthCharts  # this is the magic package

st.set_page_config(page_title="Child Growth Chart", layout="centered")
st.title("WHO Child Growth Centile Calculator")
st.markdown("### Interactive digital growth charts • 0–19 years • Official WHO standards")

# --- Sidebar: Child details ---
with st.sidebar:
    st.header("Child Details")
    name = st.text_input("Child's name (optional)", "")
    dob = st.date_input("Date of birth", date(2023, 1, 1))
    sex = st.radio("Sex", ["Male", "Female"])

# --- Main: Measurements ---
st.subheader("Add measurements")
cols = st.columns([2, 2, 2, 2, 1])
with cols[0]:
    m_date = st.date_input("Measurement date", date.today())
with cols[1]:
    height = st.number_input("Height/Length (cm)", min_value=30.0, max_value=200.0, step=0.1)
with cols[2]:
    weight = st.number_input("Weight (kg)", min_value=0.5, max_value=150.0, step=0.01)
with cols[3]:
    head = st.number_input("Head circ. (cm) – optional", min_value=20.0, max_value=70.0, step=0.1, value=None)
with cols[4]:
    add = st.button("Add →")

# Store measurements in session state
if "measurements" not in st.session_state:
    st.session_state.measurements = []

if add:
    st.session_state.measurements.append({
        "date": m_date,
        "height": height,
        "weight": weight,
        "head": head if head else np.nan
    })
    st.success("Measurement added!")

# Show table
if st.session_state.measurements:
    df = pd.DataFrame(st.session_state.measurements)
    df["age_years"] = (df["date"] - dob).dt.days / 365.25
    st.write("### Measurements")
    st.dataframe(df[["date", "height", "weight", "head"]], use_container_width=True)

    # --- Plot charts ---
    charts = WHOGrowthCharts(sex.lower(), measurements=df.to_dict("records"), date_of_birth=dob)

    tab1, tab2, tab3, tab4 = st.tabs(["Height", "Weight", "BMI", "Head Circumference"])

    with tab1:
        fig = charts.plot_height()
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        fig = charts.plot_weight()
        st.plotly_chart(fig, use_container_width=True)
    with tab3:
        fig = charts.plot_bmi()
        st.plotly_chart(fig, use_container_width=True)
    with tab4:
        if df["age_years"].max() < 6:
            fig = charts.plot_head_circumference()
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Head circumference chart only shown up to 5 years")

    # --- Show latest centiles ---
    latest = df.iloc[-1]
    age_days = (latest["date"] - dob).days

    st.subheader("Latest Centiles")
    col1, col2, col3 = st.columns(3)
    with col1:
        h = charts.calculate_centile("height", latest["height"], age_days)
        st.metric("Height-for-age", f"{h['percentile']:.1f}th", f"z = {h['z']:.2f}")
    with col2:
        w = charts.calculate_centile("weight", latest["weight"], age_days)
        st.metric("Weight-for-age", f"{w['percentile']:.1f}th", f"z = {w['z']:.2f}")
    with col3:
        bmi_val = latest["weight"] / ((latest["height"]/100)**2)
        b = charts.calculate_centile("bmi", bmi_val, age_days)
        st.metric("BMI-for-age", f"{b['percentile']:.1f}th", f"z = {b['z']:.2f}")

    st.download_button("Download chart as PDF", data=charts.export_pdf(), file_name=f"{name or 'child'}_growth_chart.pdf", mime="application/pdf")

else:
    st.info("Add your first measurement to see the growth chart")

st.markdown("---")
st.caption("Based on WHO Child Growth Standards (2006) and Growth Reference (2007) • For clinical use with professional judgement • Created by Dr [Your Name]")
