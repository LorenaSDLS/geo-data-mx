import streamlit as st
from backend.DB.conexion import leer_tabla
from backend.utils.analysis import (
    principales_similares,
    municipios_sin_info,
    municipios_secundarios
)
from streamlit_folium import st_folium

def pantalla_municipios():
    tabla_muni = leer_tabla("municipios")
    info_muni = leer_tabla("info_municipios")

    #st.title("Buscador de Municipios")

    # --- SECCIÓN SUPERIOR: SELECTORES EN PANTALLA ---
    col1, col2 = st.columns(2)

    with col1:
        estado_sel = st.selectbox(
            "Selecciona un estado",
            sorted(tabla_muni["nombre_ent"].unique()),
            key="estado_sel"
        )

    municipios_estado = tabla_muni[
        tabla_muni["nombre_ent"] == estado_sel
    ]["nomgeo"].unique()

    with col2:
        municipio_sel = st.selectbox(
            "Selecciona un municipio",
            sorted(municipios_estado),
            key="municipio_sel"
        )

    # Botón para consultar
    consultar = st.button("Consultar información del municipio")



    # Guarda la selección en session_state
    if consultar:
        fila = tabla_muni[
            (tabla_muni["nombre_ent"] == estado_sel) &
            (tabla_muni["nomgeo"] == municipio_sel)
        ]
        cvegeo = fila.iloc[0]["cvegeo"]

        st.session_state["cvegeo_seleccionado"] = cvegeo
        st.session_state["municipio_seleccionado_nombre"] = municipio_sel
        st.session_state["consulta_realizada"] = True

    # --- SECCIÓN INFERIOR: RESULTADOS ---
    if st.session_state.get("consulta_realizada", False):
        st.markdown("---")
        st.subheader(f"Resultados para: {st.session_state['municipio_seleccionado_nombre']}")
        mostrar_resultados(info_muni)



# ============================================================
# =============  MOSTRAR RESULTADOS DEL MUNICIPIO  ============
# ============================================================

def mostrar_resultados(info_muni):

    cvegeo = st.session_state["cvegeo_seleccionado"]
    fila_info = info_muni[info_muni["cvegeo"] == cvegeo]

    if fila_info.empty or not bool(fila_info.iloc[0].get("tiene_info", False)):
        mostrar_municipio_sin_info(cvegeo)
        return

    if bool(fila_info.iloc[0].get("es_principal", False)):
        mostrar_municipio_principal(cvegeo)
    else:
        mostrar_municipio_secundario(cvegeo)



# ============================================================
# ==========       CASO 1: SIN INFORMACIÓN       =============
# ============================================================

def mostrar_municipio_sin_info(cvegeo):
    st.error("Este municipio no cuenta con información disponible.")

    cercanos, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_sin_info(cvegeo)
    municipio_actual = st.session_state.get("municipio_seleccionado_nombre")

    st.subheader(f"Municipios cercanos a {municipio_actual}:")

    cols = st.columns(3)
    for idx, row in cercanos.iterrows():
        muni = row["Municipio"]
        estado = row["Estado"]
        cve = row["cvegeo"]
        distancia = row["Distancia (km)"]
        texto_boton = f"{estado} — {muni} — {distancia:.2f} km"

        col = cols[idx % 3]
        with col:
            if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                st.session_state["cvegeo_seleccionado"] = cve
                st.session_state["municipio_seleccionado_nombre"] = muni
                st.session_state["consulta_realizada"] = True
                st.rerun()

    st.subheader("Mapa de municipios cercanos con información disponible:")
    st_folium(mapa, width=600, height=400)

    st.subheader("Producción total por cultivo")
    st.dataframe(cult_gen)
    st.pyplot(graf1)

    st.subheader("Producción anual")
    st.dataframe(cult_anual)
    st.pyplot(graf2)



# ============================================================
# ==========       CASO 2: PRINCIPAL       ===================
# ============================================================

def mostrar_municipio_principal(cvegeo):
    st.success("🌾 Municipio con información y cultivo.")

    top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = principales_similares(cvegeo, top_n=10)
    municipio_actual = st.session_state.get("municipio_seleccionado_nombre")

    st.subheader(f"Municipios similares a {municipio_actual}:")

    cols = st.columns(3)
    for idx, row in top_similares.iterrows():
        muni = row["Municipio"]
        estado = row["Estado"]
        cve = row["cvegeo"]
        similarity = row["Similitud"]
        texto_boton = f"{estado} — {muni} — {similarity:.2f}%"

        col = cols[idx % 3]
        with col:
            if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                st.session_state["cvegeo_seleccionado"] = cve
                st.session_state["municipio_seleccionado_nombre"] = muni
                st.session_state["consulta_realizada"] = True
                st.rerun()

    st.subheader("Mapa de municipios similares:")
    st_folium(mapa, width=600, height=400)

    st.subheader("Producción total por cultivo")
    st.dataframe(cult_gen)
    st.pyplot(graf1)

    st.subheader("Producción anual")
    st.dataframe(cult_anual)
    st.pyplot(graf2)



# ============================================================
# ==========       CASO 3: SECUNDARIO       ==================
# ============================================================

def mostrar_municipio_secundario(cvegeo):
    st.info("Municipio con información.")

    top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_secundarios(cvegeo, top_n=10)
    municipio_actual = st.session_state.get("municipio_seleccionado_nombre")

    st.subheader(f"Municipios similares a {municipio_actual}:")

    cols = st.columns(3)
    for idx, row in top_similares.iterrows():
        muni = row["Municipio"]
        estado = row["Estado"]
        cve = row["cvegeo"]
        similarity = row["Similitud"]
        texto_boton = f"{estado} — {muni} — {similarity:.2f}%"

        col = cols[idx % 3]
        with col:
            if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                st.session_state["cvegeo_seleccionado"] = cve
                st.session_state["municipio_seleccionado_nombre"] = muni
                st.session_state["consulta_realizada"] = True
                st.rerun()

    st.subheader("Mapa de municipios similares")
    st_folium(mapa, width=600, height=400)

    st.subheader("Producción total por cultivo")
    st.dataframe(cult_gen)
    st.pyplot(graf1)

    st.subheader("Producción anual")
    st.dataframe(cult_anual)
    st.pyplot(graf2)
