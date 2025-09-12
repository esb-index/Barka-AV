
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
    # Csak a hónapok oszlopai
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    df["annual"] = df[months].mean(axis=1)
    # Normalizálás 0-1 közé
    minv, maxv = df["annual"].min(), df["annual"].max()
    df["scaled"] = (df["annual"] - minv) / (maxv - minv)
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
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=100, xaxis=dict(visible=False), yaxis=dict(visible=False))
    return fig

# ---------- INITIAL DATA ----------
f1_df = fetch_f1_data()
f1_latest = f1_df.iloc[-1]["scaled"]

initial_values = {
    "F1 – Global Temperature": f1_latest,
    "F2 – Food Security": 0.75,
    "F4 – Water": 0.65,
    "F6 – Pandemics": 0.90,
    "P4 – Phytoplankton": 0.70,
    "P10 – Permafrost": 0.80
}

# Session state tárolás
if "values" not in st.session_state:
    st.session_state["values"] = initial_values.copy()
    # Trendek: F1 valós NASA-adat, többi dummy
    st.session_state["trends"] = {
        "F1 – Global Temperature": f1_df["scaled"].tolist()[-24:],
        "F2 – Food Security": (np.linspace(0.7,0.8,24) + np.random.normal(0,0.01,24)).tolist(),
        "F4 – Water": (np.linspace(0.6,0.7,24) + np.random.normal(0,0.01,24)).tolist(),
        "F6 – Pandemics": (np.linspace(0.85,0.9,24) + np.random.normal(0,0.01,24)).tolist(),
        "P4 – Phytoplankton": (np.linspace(0.65,0.7,24) + np.random.normal(0,0.01,24)).tolist(),
        "P10 – Permafrost": (np.linspace(0.75,0.8,24) + np.random.normal(0,0.01,24)).tolist()
    }

# ---------- SIDEBAR ----------
st.sidebar.header("Bárka AV (Alap Verzió) — vezérlők")
st.sidebar.markdown("Ez egy demonstrációs AV dashboard. Az F1 valós NASA-adat, a többi tesztadat (dummy).")

if st.sidebar.button("Reset values"):
    st.session_state["values"] = initial_values.copy()
    st.sidebar.success("Visszaállítva.")

st.sidebar.markdown("**Simuláció**")
if st.sidebar.button("Simulate F1 tipping (trigger domino)"):
    for k in st.session_state["values"].keys():
        if k != "F1 – Global Temperature":
            newv = min(1.0, st.session_state["values"][k] + 0.20)
            st.session_state["values"][k] = newv
            st.session_state["trends"][k] = st.session_state["trends"][k][-8:] + (np.linspace(newv-0.02,newv,8) + np.random.normal(0,0.01,8)).tolist()
    st.sidebar.success("F1 tipping simulated: other components increased (domino).")

st.sidebar.markdown("---")
st.sidebar.info("Következő lépés: további valós adatok bekötése (FAO, GRACE, WHO).")

# ---------- MAIN LAYOUT ----------
st.title("🌍 Bárka AV Dashboard — Alap Verzió (Prototype)")
st.subheader("6 kritikus komponens (F1 → trigger) — F1 valós NASA GISTEMP adatból")

components = list(st.session_state["values"].keys())
emojis = {
    "F1 – Global Temperature": "🌡️",
    "F2 – Food Security": "🌾",
    "F4 – Water": "💧",
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
            spark = st.session_state["trends"][comp]
            fig = make_sparkline(spark)
            st.plotly_chart(fig, use_container_width=True)
            st.write("")

# Domino hatás magyarázat
st.markdown("---")
left, right = st.columns([3,2])
with left:
    st.markdown("**Domino effect demo:** F1 (Global Temperature) átbillenése láncreakciót indíthat. A bal felső gombbal kipróbálhatod.")
with right:
    if st.button("Increase F1 (manual +0.05)"):
        st.session_state["values"]["F1 – Global Temperature"] = min(1.0, st.session_state["values"]["F1 – Global Temperature"] + 0.05)
        st.session_state["trends"]["F1 – Global Temperature"] = st.session_state["trends"]["F1 – Global Temperature"][-8:] + (np.linspace(st.session_state["values"]["F1 – Global Temperature"]-0.02, st.session_state["values"]["F1 – Global Temperature"], 8) + np.random.normal(0,0.01,8)).tolist()
        st.experimental_rerun()

# Jelmagyarázat
st.markdown("""
**Legend:**  
• Zöld = alacsony kockázat (≤0.6) • Sárga = figyelmeztetés (0.6–0.7) • Narancs = magas (0.7–0.8) • Piros = kritikus (≥0.8)  
""")

# ---------- FOOTER ----------
st.markdown("---")
st.header("Adatforrás")
st.markdown("""
**F1 – Global Temperature:** NASA GISTEMP v4 (https://data.giss.nasa.gov/gistemp/)  
Minden más komponens jelenleg tesztadat, hamarosan valós forrásra cseréljük.  
""")
