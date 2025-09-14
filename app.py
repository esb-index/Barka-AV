# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Bárka AV Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- DATA FETCHERS ----------
@st.cache_data
def fetch_f1_data():
    # NASA GISTEMP: Globális felszíni hőmérséklet-anomália
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    df = pd.read_csv(url, skiprows=1)
    df = df.rename(columns={"Year": "year"})
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["annual"] = df[months].mean(axis=1)
    minv, maxv = df["annual"].min(), df["annual"].max()
    df["scaled"] = (df["annual"] - minv) / (maxv - minv)
    return df

@st.cache_data
def fetch_f4_data():
    # F4 adat a GitHub repo-ból (feltöltött CSV fájl)
    df = pd.read_csv("data/F4_water.csv")
    df["time"] = pd.to_datetime(df["time [yyyy-mm-dd]"])
    df = df.rename(columns={"global [cm]": "global_cm"})
    # Normalizálás 0-1 közé
    minv, maxv = df["global_cm"].min(), df["global_cm"].max()
    df["scaled"] = (df["global_cm"] - minv) / (maxv - minv)
    return df

# ---------- HELPERS ----------
def color_from_val(v):
    if v >= 0.80:
        return "#d62728"  # piros
    elif v >= 0.70:
        return "#ff7f0e"  # narancs
    elif v >= 0.60:
        return "#ffbb33"  # sárga
    else:
        return "#2ca02c"  # zöld

def make_sparkline(y):
    fig = px.line(y=y)
    fig.update_traces(line=dict(width=2))
    fig.update_layout(
        margin=dict(l=0,r=0,t=0,b=0),
        height=100,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig

# ---------- INITIAL DATA ----------
f1_df = fetch_f1_data()
f1_latest = f1_df.iloc[-1]["scaled"]

f4_df = fetch_f4_data()
f4_latest = f4_df.iloc[-1]["scaled"]

initial_values = {
    "F1 – Global Temperature": f1_latest,
    "F4 – Water Storage": f4_latest
}

if "values" not in st.session_state:
    st.session_state["values"] = initial_values.copy()
    st.session_state["trends"] = {
        "F1 – Global Temperature": f1_df["scaled"].tolist()[-24:],
        "F4 – Water Storage": f4_df["scaled"].tolist()[-24:]
    }

# ---------- SIDEBAR ----------
st.sidebar.header("Bárka AV (Alap Verzió) — vezérlők")
st.sidebar.markdown("Ez egy demonstrációs AV dashboard. Az F1 és F4 valós adatokból fut.")

if st.sidebar.button("Reset values"):
    st.session_state["values"] = initial_values.copy()
    st.sidebar.success("Visszaállítva.")

# ---------- MAIN LAYOUT ----------
st.title("🌍 Bárka AV Dashboard — Alap Verzió (Prototype)")
st.subheader("F1 (NASA GISTEMP) + F4 (GRACE Water Storage, GFZ RL06)")

components = list(st.session_state["values"].keys())
emojis = {
    "F1 – Global Temperature": "🌡️",
    "F4 – Water Storage": "💧"
}

cols = st.columns(2)
for i, col in enumerate(cols):
    comp = components[i]
    val = st.session_state["values"][comp]
    color = color_from_val(val)
    with col:
        st.markdown(f"### {emojis.get(comp,'')}  {comp}")
        percent = int(val * 100)
        st.metric(label="Risk level", value=f"{percent}%")
        st.markdown(
            f"<div style='height:10px; background:{color}; border-radius:6px;'></div>",
            unsafe_allow_html=True
        )
        spark = st.session_state["trends"][comp]
        fig = make_sparkline(spark)
        st.plotly_chart(fig, use_container_width=True)
        st.write("")

# ---------- DETAILED CHARTS ----------
st.markdown("---")
st.header("📊 Részletes grafikonok")

# F1 részletes
st.subheader("F1 – Global Temperature Anomaly (NASA GISTEMP)")
fig1 = px.line(f1_df, x="year", y="annual", title="Global Surface Temperature Anomaly (°C)")
st.plotly_chart(fig1, use_container_width=True)
st.caption("Source: NASA GISTEMP v4. Baseline: 1951–1980 average.")

# F4 részletes
st.subheader("F4 – Terrestrial Water Storage Anomaly (GFZ RL06, global)")
fig2 = px.line(f4_df, x="time", y="global_cm", title="Global Terrestrial Water Storage Anomaly (cm)")
st.plotly_chart(fig2, use_container_width=True)
st.caption("Source: GFZ GravIS RL06 (GRACE/GRACE-FO). Global water storage anomaly relative to long-term mean.")

# ---------- FOOTER ----------
st.markdown("---")
st.header("Adatforrások")
st.markdown("""
**F1 – Global Temperature:** NASA GISTEMP v4 (https://data.giss.nasa.gov/gistemp/)  
**F4 – Water Storage:** GFZ GravIS RL06 (https://doi.org/10.5880/GFZ.GRAVIS_06_L3_TWS)  
""")
