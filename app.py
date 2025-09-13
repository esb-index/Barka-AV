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
    # Harvard Dataverse – GRACE Mascon Global Water Storage Anomalies
    url = "https://dataverse.harvard.edu/api/access/datafile/6153072"
    df = pd.read_csv(url)
    df = df.rename(columns={"Year": "year", "Water_Storage_Anomaly_mm": "anomaly"})
    # éves átlag
    df = df.groupby("year", as_index=False)["anomaly"].mean()
    # normalizálás
    minv, maxv = df["anomaly"].min(), df["anomaly"].max()
    df["scaled"] = (df["anomaly"] - minv) / (maxv - minv)
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

def make_sparkline(df, y_col, title):
    fig = px.line(df, x="year", y=y_col, title=title)
    fig.update_traces(line=dict(width=2))
    fig.update_layout(margin=dict(l=0,r=0,t=30,b=0), height=250)
    return fig

# ---------- INITIAL DATA ----------
f1_df = fetch_f1_data()
f1_latest = f1_df.iloc[-1]["scaled"]

f4_df = fetch_f4_data()
f4_latest = f4_df.iloc[-1]["scaled"]

initial_values = {
    "F1 – Global Temperature": f1_latest,
    "F4 – Water Storage": f4_latest,
    "F2 – Food Security": 0.75,
    "F6 – Pandemics": 0.90,
    "P4 – Phytoplankton": 0.70,
    "P10 – Permafrost": 0.80
}

if "values" not in st.session_state:
    st.session_state["values"] = initial_values.copy()
    st.session_state["trends"] = {
        "F1 – Global Temperature": f1_df,
        "F4 – Water Storage": f4_df,
        "F2 – Food Security": pd.DataFrame({"year": list(range(2000,2024)), "scaled": np.linspace(0.7,0.8,24)}),
        "F6 – Pandemics": pd.DataFrame({"year": list(range(2000,2024)), "scaled": np.linspace(0.85,0.9,24)}),
        "P4 – Phytoplankton": pd.DataFrame({"year": list(range(2000,2024)), "scaled": np.linspace(0.65,0.7,24)}),
        "P10 – Permafrost": pd.DataFrame({"year": list(range(2000,2024)), "scaled": np.linspace(0.75,0.8,24)})
    }

# ---------- SIDEBAR ----------
st.sidebar.header("Bárka AV (Alap Verzió) — vezérlők")
st.sidebar.markdown("F1 és F4 valós adatforrásból, a többi egyelőre tesztadat.")

if st.sidebar.button("Reset values"):
    st.session_state["values"] = initial_values.copy()
    st.sidebar.success("Visszaállítva.")

# ---------- MAIN LAYOUT ----------
st.title("🌍 Bárka AV Dashboard — Alap Verzió (Prototype)")
st.subheader("Valós idősor: F1 (NASA GISTEMP), F4 (GRACE/Harvard Dataverse)")

components = list(st.session_state["values"].keys())
emojis = {
    "F1 – Global Temperature": "🌡️",
    "F2 – Food Security": "🌾",
    "F4 – Water Storage": "💧",
    "F6 – Pandemics": "🦠",
    "P4 – Phytoplankton": "🌱",
    "P10 – Permafrost": "❄️"
}

for row_start in [0, 3]:
    cols = st.columns(3)
    for i, col in enumerate(cols):
        idx = row_start + i
        comp = components[idx]
        val = st.session_state["values"][comp]
        color = color_from_val(val)
        with col:
            st.markdown(f"### {emojis.get(comp,'')}  {comp}")
            percent = int(val * 100)
            st.metric(label="Risk level", value=f"{percent}%")
            st.markdown(f"<div style='height:10px; background:{color}; border-radius:6px;'></div>", unsafe_allow_html=True)
            fig = make_sparkline(st.session_state["trends"][comp], "scaled", f"{comp} (scaled 0–1)")
            st.plotly_chart(fig, use_container_width=True)

# ---------- FOOTER ----------
st.markdown("---")
st.header("Adatforrás")
st.markdown("""
**F1 – Global Temperature:** NASA GISTEMP v4 (https://data.giss.nasa.gov/gistemp/)  
**F4 – Water Storage:** GRACE Mascon Global Water Storage Anomalies, Harvard Dataverse (https://dataverse.harvard.edu/)  
""")
