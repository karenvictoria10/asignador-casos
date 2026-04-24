import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ----------- CONFIG -----------

pesos = {"A": 1, "B": 2, "C": 3}
personas = ["Fany", "Paola", "Valeria"]

# ----------- CONEXIÓN GOOGLE SHEETS -----------

def conectar_sheets():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/15oJHLXONtcGoudA2LcmFi4bNMwGK8Dm2zGyV8fv5V-4/edit").sheet1
    return sheet

def leer_sheets():
    sheet = conectar_sheets()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def guardar_en_sheets(nuevo):
    sheet = conectar_sheets()
    sheet.append_row([
        nuevo["ID"],
        nuevo["Tipo"],
        nuevo["Puntos"],
        nuevo["Asignado a"],
        str(nuevo["Fecha"]),
        nuevo["Estado"]
    ])

def cerrar_caso(id_caso):
    sheet = conectar_sheets()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    fila = df[df["ID"] == id_caso].index

    if not fila.empty:
        sheet.update_cell(fila[0] + 2, 6, "Cerrado")

# ----------- LOGIN -----------

st.title("🔐 Acceso")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if usuario != "AMCABRER" or password != "asigca26":
    st.warning("Acceso restringido")
    st.stop()

st.success("Acceso autorizado")
st.write("Correo en uso:")
st.write(st.secrets["gcp_service_account"]["client_email"])
# ----------- APP -----------

st.set_page_config(page_title="Asignador de Casos", layout="wide")
st.title("📊 Asignador Inteligente de Casos")

# ----------- DATOS -----------

df = leer_sheets()

if df.empty:
    df = pd.DataFrame(columns=["ID", "Tipo", "Puntos", "Asignado a", "Fecha", "Estado"])

# ----------- ASIGNAR -----------

st.subheader("➕ Asignar nuevo caso")
tipo = st.selectbox("Tipo de caso", ["A", "B", "C"])

if st.button("Asignar caso"):

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

    st.session_state["ultimo_asignado"] = asignado
    st.rerun()

# Mostrar resultado
if "ultimo_asignado" in st.session_state:
    st.success(f"✅ Caso asignado a: {st.session_state['ultimo_asignado']}")
    del st.session_state["ultimo_asignado"]

st.divider()

# ----------- CERRAR -----------

st.subheader("🔒 Cerrar caso")

if not df.empty:
    abiertos = df[df["Estado"] == "Abierto"]

    if not abiertos.empty:
        id_caso = st.selectbox("Selecciona ID", abiertos["ID"])

        if st.button("Cerrar caso"):
            cerrar_caso(id_caso)
            st.session_state["cerrado"] = id_caso
            st.rerun()
    else:
        st.info("No hay casos abiertos")

if "cerrado" in st.session_state:
    st.success(f"🔒 Caso {st.session_state['cerrado']} cerrado")
    del st.session_state["cerrado"]

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
