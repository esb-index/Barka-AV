# app.py
import os
import io
import traceback
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Bárka AV Dashboard", layout="wide", initial_sidebar_state="expanded")


# ----------------- small helper: parse whitespace table when header line is not first -----------------
def parse_whitespace_table_from_text(text):
    """
    Given a text (CSV-like but with a lead-in line), find the header row (containing 'Year' and months)
    and parse the remainder with delim_whitespace=True so columns split correctly.
    Falls back to normal read_csv if header line not found.
    """
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines[:20]):  # header is expected near the top
        # look for the typical GISTEMP header: contains 'Year' and 'Jan' or 'Dec'
        if "Year" in line and ("Jan" in line or "Dec" in line):
            header_idx = i
            break
    if header_idx is None:
        # fallback: try to find a line containing 'Year' somewhere
        for i, line in enumerate(lines[:40]):
            if "Year" in line:
                header_idx = i
                break
    if header_idx is None:
        # last fallback: try reading straightforwardly
        try:
            return pd.read_csv(io.StringIO(text))
        except Exception:
            # give up, return empty df
            return pd.DataFrame()
    # create new text starting from header line
    new_text = "\n".join(lines[header_idx:])
    return pd.read_csv(io.StringIO(new_text), delim_whitespace=True)


# ---------------- Robust fetchers with fallback and detailed error display ----------------
@st.cache_data
def fetch_f1_data(local_fallback="data/F1_gistemp.csv"):
    """
    Fetch NASA GISTEMP global monthly table (GLB.Ts+dSST.csv).
    Tries HTTP fetch; on failure uses local_fallback text file.
    Returns dataframe with columns including 'year' and 'annual' and 'scaled'.
    """
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    label = "NASA GISTEMP (F1)"
    df = None
    try:
        resp = requests.get(url, timeout=18)
        resp.raise_for_status()
        txt = resp.text
        df = parse_whitespace_table_from_text(txt)
    except Exception as e:
        err = traceback.format_exc()
        st.error(f"⚠️ Hiba az {label} letöltése közben.\nHiba: {type(e).__name__}: {e}")
        with st.expander(f"Részletes hibaüzenet ({label})"):
            st.code(err)
        # try local fallback
        if local_fallback and os.path.exists(local_fallback):
            st.info(f"Betöltés helyi fallback fájlból: {local_fallback}")
            try:
                with open(local_fallback, "r", encoding="utf-8") as f:
                    txt = f.read()
                df = parse_whitespace_table_from_text(txt)
            except Exception as e2:
                err2 = traceback.format_exc()
                st.error(f"⚠️ Nem sikerült beolvasni a helyi fallback fájlt: {local_fallback}")
                with st.expander("Hiba a fallback beolvasásakor"):
                    st.code(err2)
                return None
        else:
            st.error(f"Nincs elérhető helyi fallback az {label}-hez. Kérlek töltsd fel a '{local_fallback}' fájlt a repo 'data/' mappájába.")
            return None

    # If parse failed and df is empty -> return None
    if df is None or df.empty:
        st.error(f"⚠️ Az {label} beolvasása nem adott eredményt (üres DataFrame). Ellenőrizd a fájl formátumát.")
        return None

    # Standardize column names: Year -> year
    if "Year" in df.columns:
        df = df.rename(columns={"Year": "year"})
    # ensure numeric values in month columns
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for m in months:
        if m in df.columns:
            df[m] = pd.to_numeric(df[m], errors="coerce")
    # compute annual mean if possible
        # compute annual mean if possible
    if all(m in df.columns for m in months):
        df["annual"] = df[months].mean(axis=1)
    else:
        # if monthly columns missing, try alternative annual columns
        alt_cols = ["J-D", "J_D", "J_D.1", "J_D.0", "Annual", "Yearly"]
        found = False
        for alt in alt_cols:
            if alt in df.columns:
                df["annual"] = pd.to_numeric(df[alt], errors="coerce")
                found = True
                break
        if not found:
            # ultimate fallback: use last numeric column
            num_cols = df.select_dtypes(include=[np.number]).columns
            if len(num_cols) > 0:
                df["annual"] = pd.to_numeric(df[num_cols[-1]], errors="coerce")


    df = df.dropna(subset=["annual"])
    # convert year to int if possible
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)
    # Normalization 0..1
    minv, maxv = df["annual"].min(), df["annual"].max()
    if pd.isna(minv) or pd.isna(maxv) or (maxv - minv) == 0:
        st.error("⚠️ Nem megfelelő értékek az F1 adatban a normalizáláshoz.")
        return None
    df["scaled"] = (df["annual"] - minv) / (maxv - minv)
    return df


@st.cache_data
def fetch_f4_data(local_fallback="data/F4_water.csv", possible_urls=None):
    """
    Read GFZ GravIS TWS global CSV. Try possible_urls (list of raw URLs) first if provided,
    otherwise load local_fallback. Return DataFrame with columns 'time' (datetime), 'global_cm', 'scaled'.
    """
    label = "GFZ GravIS F4 (TWS global)"
    df = None

    # Try provided URLs if any
    if possible_urls:
        for url in possible_urls:
            try:
                resp = requests.get(url, timeout=18)
                resp.raise_for_status()
                txt = resp.text
                df = pd.read_csv(io.StringIO(txt))
                break
            except Exception:
                df = None

    # If no df yet, try local fallback
    if df is None:
        try:
            if local_fallback and os.path.exists(local_fallback):
                df = pd.read_csv(local_fallback)
            else:
                raise FileNotFoundError(f"Local fallback not found: {local_fallback}")
        except Exception as e:
            err = traceback.format_exc()
            st.error(f"⚠️ Hiba az {label} beolvasásakor.")
            with st.expander(f"Részletes hibaüzenet ({label})"):
                st.code(err)
            st.error(f"Kérlek töltsd fel a megfelelő CSV-t a '{local_fallback}' helyre a repo 'data/' mappájába.")
            return None

    # inspect & normalize
    # Possible column names: 'time [yyyy-mm-dd]' and 'global [cm]' (as in GFZ CSV)
    if "time [yyyy-mm-dd]" in df.columns:
        df["time"] = pd.to_datetime(df["time [yyyy-mm-dd]"])
    elif "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    else:
        # try first column as date
        try:
            df["time"] = pd.to_datetime(df.iloc[:, 0])
        except Exception:
            st.warning("Figyelem: nem található egzakt 'time' oszlop. Ellenőrizd a CSV-t.")
            # keep going but may fail later

    # rename global column
    if "global [cm]" in df.columns:
        df = df.rename(columns={"global [cm]": "global_cm"})
    elif "global_cm" not in df.columns and "global" in df.columns:
        df = df.rename(columns={"global": "global_cm"})

    # ensure numeric
    if "global_cm" in df.columns:
        df["global_cm"] = pd.to_numeric(df["global_cm"], errors="coerce")
    else:
        st.error("⚠️ Nem található 'global [cm]' vagy 'global_cm' oszlop a F4 CSV-ben.")
        return None

    df = df.dropna(subset=["global_cm"])
    # Normalize
    minv, maxv = df["global_cm"].min(), df["global_cm"].max()
    if pd.isna(minv) or pd.isna(maxv) or (maxv - minv) == 0:
        st.error("⚠️ Nem megfelelő értékek az F4 adatban a normalizáláshoz.")
        return None
    df["scaled"] = (df["global_cm"] - minv) / (maxv - minv)
    return df
# --------------------------------------------------------------------------------------------


# ---------------- HELPERS FOR UI ----------------
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
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=100, xaxis=dict(visible=False),
                      yaxis=dict(visible=False))
    return fig


# ---------------- MAIN ----------------
st.title("🌍 Bárka AV Dashboard — Alap Verzió (Prototype)")

# Fetch data (robust)
f1_df = fetch_f1_data(local_fallback="data/F1_gistemp.csv")
f4_df = fetch_f4_data(local_fallback="data/F4_water.csv", possible_urls=None)

if f1_df is None:
    st.error("F1 adatok hiányoznak — töltsd fel a data/F1_gistemp.csv fájlt és próbáld újra.")
    st.stop()

if f4_df is None:
    st.error("F4 adatok hiányoznak — töltsd fel a data/F4_water.csv fájlt és próbáld újra.")
    st.stop()

# prepare initial values
try:
    f1_latest = float(f1_df["scaled"].iloc[-1])
except Exception:
    st.error("F1 adat feldolgozás sikertelen: ellenőrizd a F1_gistemp.csv formátumát.")
    st.stop()

try:
    f4_latest = float(f4_df["scaled"].iloc[-1])
except Exception:
    st.error("F4 adat feldolgozás sikertelen: ellenőrizd a F4_water.csv formátumát.")
    st.stop()

initial_values = {
    "F1 – Global Temperature": f1_latest,
    "F4 – Water Storage": f4_latest,
    "F2 – Food Security (dummy)": 0.5,
    "F6 – Pandemics (dummy)": 0.5
}

if "values" not in st.session_state:
    st.session_state["values"] = initial_values.copy()
    st.session_state["trends"] = {
        "F1 – Global Temperature": f1_df["scaled"].tolist()[-36:],
        "F4 – Water Storage": f4_df["scaled"].tolist()[-36:]
    }

# Sidebar
st.sidebar.header("Bárka AV — vezérlők")
if st.sidebar.button("Reset values"):
    st.session_state["values"] = initial_values.copy()
    st.sidebar.success("Visszaállítva.")

# Dashboard cards
components = list(st.session_state["values"].keys())
emojis = {"F1 – Global Temperature": "🌡️", "F4 – Water Storage": "💧"}

cols = st.columns(2)
for i, col in enumerate(cols):
    comp = components[i]
    val = float(st.session_state["values"][comp])
    color = color_from_val(val)
    with col:
        st.markdown(f"### {emojis.get(comp,'')} {comp}")
        percent = int(val * 100)
        st.metric(label="Risk level", value=f"{percent}%")
        st.markdown(f"<div style='height:10px; background:{color}; border-radius:6px;'></div>",
                    unsafe_allow_html=True)
        spark = st.session_state["trends"][comp]
        fig = make_sparkline(spark)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.header("📊 Részletes idősorok")

# F1
st.subheader("F1 – Global Surface Temperature Anomaly (NASA GISTEMP, relative to 1951–1980 baseline)")
fig1 = px.line(f1_df, x="year", y="annual", title="Global Surface Temperature Anomaly (°C)")
fig1.update_traces(line=dict(color="firebrick", width=2))
st.plotly_chart(fig1, use_container_width=True)
st.caption("Source: NASA GISTEMP v4. Baseline: 1951–1980 average.")

# F4
st.subheader("F4 – Global Terrestrial Water Storage Anomaly (GFZ GravIS RL06, global)")
# try to pick a friendly x column name
xcol = "time" if "time" in f4_df.columns else f4_df.columns[0]
ycol = "global_cm"
fig2 = px.line(f4_df, x=xcol, y=ycol, title="Global Terrestrial Water Storage Anomaly (cm)")
fig2.update_traces(line=dict(color="royalblue", width=2))
st.plotly_chart(fig2, use_container_width=True)
st.caption("Source: GFZ GravIS RL06 (GRACE/GRACE-FO) — global anomaly (cm).")

st.markdown("---")
st.header("Adatforrások")
st.markdown("""
**F1 – Global Temperature:** NASA GISTEMP v4 (https://data.giss.nasa.gov/gistemp/)  
**F4 – Water Storage:** GFZ GravIS RL06 (https://doi.org/10.5880/GFZ.GRAVIS_06_L3_TWS)  
""")
