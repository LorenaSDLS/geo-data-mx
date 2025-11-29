import streamlit as st
from backend.DB.conexion import obtener_lista_cultivos

import unicodedata
import string
import pandas as pd

import streamlit as st
import unicodedata
import string
from backend.DB.conexion import obtener_lista_cultivos, obtener_municipios_por_cultivo



def normalizar(texto):
    """Convierte texto a mayúsculas y elimina acentos."""
    if not isinstance(texto, str):
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


def pantalla_cultivos():
    st.subheader("Listado de cultivos registrados en la base de datos")

    df = obtener_lista_cultivos()
    if df is None or df.empty:
        st.warning("No hay cultivos registrados en la base de datos.")
        return

    # Normalizar
    df["nombre_norm"] = df["nomcultivo"].apply(normalizar)

    if "filtro_letra" not in st.session_state:
        st.session_state["filtro_letra"] = None

    st.write("### Filtrar por letra")

    if st.button("Mostrar todos"):
        st.session_state["filtro_letra"] = None


    # Botones A-Z
    letras = list(string.ascii_uppercase)
    filas = [st.columns(7), st.columns(7), st.columns(7), st.columns(5)]
    idx = 0

    for fila in filas:
        for col in fila:
            if idx >= len(letras):
                break
            letra = letras[idx]
            if col.button(letra):
                st.session_state["filtro_letra"] = letra
            idx += 1

    # aplicar filtro
    letra = st.session_state["filtro_letra"]
    df_filtrado = df[df["nombre_norm"].str.startswith(letra)] if letra else df

    st.write(f"### Total cultivos: {len(df_filtrado)}")

    st.write("### Selecciona un cultivo:")

    num_cols = 4
    cols=st.columns(num_cols)

    for start in range(0, len(df_filtrado), num_cols):
        cols = st.columns(num_cols)
        subset = df_filtrado.iloc[start : start + num_cols]
        for col, (_, fila) in zip(cols, subset.iterrows()):
            nombre = fila["nomcultivo"]
            if col.button(nombre):
                st.session_state["cultivo_seleccionado"] = nombre
                st.session_state["pantalla_actual"] = "cultivo_detalle"
                st.rerun()

