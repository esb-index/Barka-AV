Streamlit app kódja (app.py)

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

# ---------- HELPERS ----------

def color_from_val(v):

    # v: 0..1

    if v >= 0.80:

        return "#d62728"  # red

    elif v >= 0.70:

        return "#ff7f0e"  # orange

    elif v >= 0.60:

        return "#ffbb33"  # yellow

    else:

        return "#2ca02c"  # green

def make_sparkline(y):

    fig = px.line(y=y)

    fig.update_traces(line=dict(width=2))

    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=100, xaxis=dict(visible=False), yaxis=dict(visible=False))

    return fig

# ---------- INITIAL DATA (sample / placeholder; you can replace with real CSV loads later) ----------

initial_values = {

    "F1 – Global Temperature": 0.85,

    "F2 – Food Security": 0.75,

    "F4 – Water": 0.65,

    "F6 – Pandemics": 0.90,

    "P4 – Phytoplankton": 0.70,

    "P10 – Permafrost": 0.80

}

# session state persistence (keeps values after button clicks)

if "values" not in st.session_state:

    st.session_state["values"] = initial_values.copy()

    # sample trend histories (24 time-points)

    st.session_state["trends"] = {

        k: (np.linspace(max(0,v-0.05), min(1,v+0.05), 24) + np.random.normal(0, 0.01, 24)).tolist()

        for k,v in initial_values.items()

    }

# ---------- SIDEBAR ----------

st.sidebar.header("Bárka AV (Alap Verzió) — vezérlők")

st.sidebar.markdown("Ez egy demonstrációs AV dashboard. Az értékek kezdetben minták; később beköthetők valós adatokhoz.")

if st.sidebar.button("Reset values"):

    st.session_state["values"] = initial_values.copy()

    st.sidebar.success("Visszaállítva.")

st.sidebar.markdown("**Simuláció**")

if st.sidebar.button("Simulate F1 tipping (trigger domino)"):

    # Ha F1 átbillen, rángatja a többieket

    for k in st.session_state["values"].keys():

        if k != "F1 – Global Temperature":

            newv = min(1.0, st.session_state["values"][k] + 0.20)

            st.session_state["values"][k] = newv

            # update trend with spike

            st.session_state["trends"][k] = st.session_state["trends"][k][-8:] + (np.linspace(newv-0.02, newv, 8) + np.random.normal(0,0.01,8)).tolist()

    st.sidebar.success("F1 tipping simulated: other components increased (domino).")

st.sidebar.markdown("---")

st.sidebar.info("Ha szeretnéd, később beállítjuk a valós adatok betöltését (CSV/URL/API).")

# ---------- MAIN LAYOUT ----------

st.title("🌍 Bárka AV Dashboard — Alap Verzió (Prototype)")

st.subheader("6 kritikus komponens (F1 → trigger) — demo KER visualizáció")

# Cards layout: 2 rows x 3 columns

components = list(st.session_state["values"].keys())

emojis = {

    "F1 – Global Temperature": "🌡️",

    "F2 – Food Security": "🌾",

    "F4 – Water": "💧",

    "F6 – Pandemics": "🦠",

    "P4 – Phytoplankton": "🌱",

    "P10 – Permafrost": "❄️"

}

# draw top row

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

            # colored progress-like bar using metric + colored markdown stripe

            st.metric(label="Risk level", value=f"{percent}%", delta=None)

            # small colored bar (hacky, but works visually)

            st.markdown(f"<div style='height:10px; background:{color}; border-radius:6px;'></div>", unsafe_allow_html=True)

            # sparkline

            spark = st.session_state["trends"][comp]

            fig = make_sparkline(spark)

            st.plotly_chart(fig, use_container_width=True)

            st.write("")  # spacing

# Domino note / quick controls

st.markdown("---")

left, right = st.columns([3,2])

with left:

    st.markdown("**Domino effect demo:** F1 (Global Temperature) működésbe hozhatja a láncreakciót. A bal felső gombbal kipróbálhatod a hatást.")

with right:

    if st.button("Increase F1 (manual +0.05)"):

        st.session_state["values"]["F1 – Global Temperature"] = min(1.0, st.session_state["values"]["F1 – Global Temperature"] + 0.05)

        st.session_state["trends"]["F1 – Global Temperature"] = st.session_state["trends"]["F1 – Global Temperature"][-8:] + (np.linspace(st.session_state["values"]["F1 – Global Temperature"]-0.02, st.session_state["values"]["F1 – Global Temperature"], 8) + np.random.normal(0,0.01,8)).tolist()

        st.experimental_rerun()

# small legend and explanation

st.markdown("""

**Legend:**  

• Zöld = alacsony kockázat (≤0.6) • Sárga = figyelmeztetés (0.6–0.7) • Narancs = magas (0.7–0.8) • Piros = kritikus (≥0.8)  

""")

# ---------- FOOTER: instructions for adding real data ----------

st.markdown("---")

st.header("Adatforrások és következő lépések")

st.markdown("""

Ezek a demo értékek. Később CSV/API csatlakozásokat adhatunk hozzá:

- NASA / Copernicus CSV-ek (globális hő, chlorophyll, NDVI)  

- FAO / WFP (crop yield, food security)  

- GRACE (víz készlet anomáliák)  

- ProMED / WHO (járványok)

Ha szeretnéd, elkészítem a `fetch_real_data()` függvényt és a pontos URL-eket / letöltő scriptet, amit csak bemásolsz ide.

""")

) requirements.txt (másold ezt is a repo-ba)

Feltölteni kötelező, hogy a Streamlit Cloud tudja telepíteni a csomagokat.

streamlit>=1.20.0

pandas

numpy

plotly

(ha később más csomagokat használsz, ide írd őket soronként)
     
