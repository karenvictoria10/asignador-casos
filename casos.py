import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# ----------- CONFIG -----------

API_URL = "https://script.google.com/macros/s/AKfycbyTomfrK8h4C3TKMFGrFWxrsdw7uQIVkXt_NT6s-AKhto_ZD_WfaPM1COe0TlEjj_huaQ/exec"

SHEET_URL = "https://docs.google.com/spreadsheets/d/15oJHLXONtcGoudA2LcmFi4bNMwGK8Dm2zGyV8fv5V-4/export?format=csv"

pesos = {"A": 1, "B": 2, "C": 3}
personas = ["Fany", "Paola", "Valeria"]

# ----------- FUNCIONES -----------

def cargar_datos():
    try:
        df = pd.read_csv(SHEET_URL)
        return df
    except:
        return pd.DataFrame(columns=["ID", "Tipo", "Puntos", "Asignado a", "Fecha", "Estado"])

def guardar_en_sheets(nuevo):
    requests.post(API_URL, json={
        "ID": nuevo["ID"],
        "Tipo": nuevo["Tipo"],
        "Puntos": nuevo["Puntos"],
        "Asignado a": nuevo["Asignado a"],
        "Fecha": str(nuevo["Fecha"]),
        "Estado": nuevo["Estado"]
    })

def asignar(tipo, df):

    df_abiertos = df[df["Estado"] == "Abierto"]
    carga = df_abiertos.groupby("Asignado a")["Puntos"].sum().to_dict()

    for p in personas:
        if p not in carga:
            carga[p] = 0

    asignado = min(carga, key=carga.get)

    nuevo = {
        "ID": len(df) + 1,
        "Tipo": tipo,
        "Puntos": pesos[tipo],
        "Asignado a": asignado,
        "Fecha": datetime.now(),
        "Estado": "Abierto"
    }

    guardar_en_sheets(nuevo)

    return asignado

# ----------- LOGIN -----------

st.title("🔐 Acceso")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if usuario != "ASIGNADOR" or password != "Telmex.123":
    st.warning("Acceso restringido")
    st.stop()

st.success("Acceso autorizado")

# ----------- APP -----------

st.set_page_config(page_title="Asignador de Casos", layout="wide")
st.title("📊 Asignador Inteligente de Casos")

df = cargar_datos()

# ----------- ASIGNAR -----------

st.subheader("➕ Asignar nuevo caso")
tipo = st.selectbox("Tipo de caso", ["A", "B", "C"])

if st.button("Asignar caso"):
    persona = asignar(tipo, df)
    st.session_state["ultimo_asignado"] = persona
    st.rerun()

if "ultimo_asignado" in st.session_state:
    st.success(f"✅ Caso asignado a: {st.session_state['ultimo_asignado']}")
    del st.session_state["ultimo_asignado"]

st.divider()

# ----------- RESUMEN -----------

st.subheader("⚖️ Carga actual (puntos abiertos)")

if not df.empty:
    df_abiertos = df[df["Estado"] == "Abierto"]
    resumen = df_abiertos.groupby("Asignado a")["Puntos"].sum().to_dict()

    for p in personas:
        if p not in resumen:
            resumen[p] = 0

    promedio = sum(resumen.values()) / len(personas) if personas else 0

    def semaforo(valor):
        if valor <= promedio * 1.1:
            return "🟢"
        elif valor <= promedio * 1.3:
            return "🟡"
        else:
            return "🔴"

    col1, col2, col3 = st.columns(3)

    col1.metric("Fany", resumen["Fany"], semaforo(resumen["Fany"]))
    col2.metric("Paola", resumen["Paola"], semaforo(resumen["Paola"]))
    col3.metric("Valeria", resumen["Valeria"], semaforo(resumen["Valeria"]))

    st.caption(f"Promedio actual: {round(promedio,2)} puntos")

    st.bar_chart(pd.Series(resumen))

st.divider()

# ----------- TABLA -----------

st.subheader("📋 Historial de casos")

if not df.empty:
    st.dataframe(df.sort_values("ID", ascending=False), use_container_width=True)
else:
    st.info("No hay datos aún")
