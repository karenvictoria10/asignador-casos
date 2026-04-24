import streamlit as st
import pandas as pd
from datetime import datetime
import os
# ----------- LOGIN -----------

st.title("🔐 Acceso")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")

if usuario != "AMCABRER" or password != "asigca26":
    st.warning("Acceso restringido")
    st.stop()

st.success("Acceso autorizado")

archivo = "casos_equipo.xlsx"

pesos = {"A": 1, "B": 2, "C": 3}
personas = ["Fany", "Paola", "Valeria"]

# ----------- FUNCIONES -----------

def inicializar():
    if not os.path.exists(archivo):
        df = pd.DataFrame(columns=["ID", "Tipo", "Puntos", "Asignado a", "Fecha", "Estado"])
        df.to_excel(archivo, index=False)

def cargar_datos():
    return pd.read_excel(archivo)

def guardar_datos(df):
    df.to_excel(archivo, index=False)

def asignar(tipo):
    df = cargar_datos()

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

    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
    guardar_datos(df)

    return asignado

def cerrar(id_caso):
    df = cargar_datos()
    df.loc[df["ID"] == id_caso, "Estado"] = "Cerrado"
    guardar_datos(df)

# ----------- UI -----------

st.set_page_config(page_title="Asignador de Casos", layout="wide")

st.title("📊 Asignador Inteligente de Casos")

inicializar()
df = cargar_datos()

# ----------- ASIGNAR -----------

st.subheader("➕ Asignar nuevo caso")
tipo = st.selectbox("Tipo de caso", ["A", "B", "C"])

if st.button("Asignar caso"):
    persona = asignar(tipo)
    st.session_state["ultimo_asignado"] = persona
    st.rerun()

# Mostrar resultado después del rerun
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
            cerrar(id_caso)
            st.session_state["cerrado"] = id_caso
            st.rerun()
    else:
        st.info("No hay casos abiertos")

# Mostrar mensaje después del rerun
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
