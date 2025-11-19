#comando para correrlo: streamlit run frontend/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, municipios_sin_info, municipios_secundarios
from streamlit_folium import st_folium
from backend.DB.conexion import leer_tabla, leer_geografia, estadisticas_generales_cultivos, ranking_estados, cantidad_cultivos_por_anio
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from frontend.diseño import aplicar_estilos




# -------------------- ESTILOS --------------------
aplicar_estilos()

st.title("Detección de municipios similares")

# -------------------- SIDEBAR: NAVEGACIÓN --------------------
pagina = st.sidebar.radio(
    "Navegación:",
    ["Inicio", "Buscador de municipios"]
)


# -------------------- SIDEBAR: NAVEGACIÓN --------------------
# ---------------- Pantalla "Inicio" ----------------
if pagina == "Inicio":

    st.header("📊 Panorama General Agrícola de México")
    st.markdown("Una vista rápida y visual de la producción nacional (últimos 10 años).")

    resultado = estadisticas_generales_cultivos()

    if resultado[0] is None:
        st.error("No hay datos disponibles")
        st.stop()

    # --- Datos obtenidos ---
    df_top10, df_anual, fig_top10, fig_anual = resultado

    # ===========================================
    # 1) TARJETAS BONITAS (KPI)
    # ===========================================
    col1, col2, col3 = st.columns(3)

    total_produccion = int(df_anual["produccion"].sum())
    cultivos_count = len(df_top10)
    anios = df_anual["anio"].nunique()

    col1.metric("📦 Producción total (10 años)", f"{total_produccion:,}")
    col2.metric("🌱 Cultivos analizados", cultivos_count)
    col3.metric("📅 Años considerados", anios)

    st.markdown("---")

    # ===========================================
    # 2) PIE CHART — Distribución de cultivos
    # ===========================================
    st.subheader("🍕 Distribución de la producción por cultivo")

    df_pie = df_top10.copy()
    df_pie = df_pie.sort_values("produccion", ascending=False)

    fig_pie, ax = plt.subplots(figsize=(6, 6))
    ax.pie(df_pie["produccion"], labels=df_pie["nomcultivo"], autopct="%1.1f%%")
    ax.set_title("Distribución porcentual de cultivos (10 años)")
    st.pyplot(fig_pie)

    st.markdown("---")

    # ===========================================
    # 3) Top 10 cultivos más producidos (gráfica mejorada)
    # ===========================================
    st.subheader("🏆 Top 10 cultivos más producidos (últimos 10 años)")
    #st.dataframe(df_top10)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_top10["nomcultivo"], df_top10["produccion"])
    ax.set_xticklabels(df_top10["nomcultivo"], rotation=45, ha='right')
    ax.set_ylabel("Producción total")
    ax.set_title("Top 10 cultivos más producidos")
    st.pyplot(fig)

    st.markdown("---")

    # ===========================================
    # 4) Ranking de estados por producción total
    # ===========================================
    st.subheader("🏅 Ranking de estados por producción total")

    df_estados = ranking_estados()  # <-- FUNCION QUE DEBES TENER
    #st.dataframe(df_estados)

    fig_rank, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_estados["Estado"], df_estados["Producción"])
    ax.set_xticklabels(df_estados["Estado"], rotation=45, ha='right')
    ax.set_ylabel("Producción")
    ax.set_title("Estados con mayor producción (10 años)")
    st.pyplot(fig_rank)

    st.markdown("---")

    # ===========================================
    # 5) Producción agrícola total por año
    # ===========================================
    st.subheader("📈 Producción agrícola total por año")
    df_anual = df_anual.rename(columns={"anio": "Año", "produccion": "Producción"})
    #st.dataframe(df_anual)
    st.pyplot(fig_anual)

    st.markdown("---")






# ============================================================
# ===========      PANTALLA BUSCADOR MUNICIPIOS     ===========
# ============================================================


if pagina == "Buscador de municipios":
    # Cargar tablas necesarias
    tabla_muni = leer_tabla("municipios")
    info_muni = leer_tabla("info_municipios")

    # ------------- Selección de estado y municipio -------------
    estado_sel = st.sidebar.selectbox(
        "Selecciona un estado",
        sorted(tabla_muni["nombre_ent"].unique())
    )

    municipios_estado = tabla_muni[tabla_muni["nombre_ent"] == estado_sel]["nomgeo"].unique()

    municipio_sel = st.sidebar.selectbox(
        "Selecciona un municipio",
        sorted(municipios_estado)
    )

    # ------------------ Botón: consultar info ------------------
    if st.sidebar.button("Consultar información del municipio"):

        fila = tabla_muni[
            (tabla_muni["nombre_ent"] == estado_sel) &
            (tabla_muni["nomgeo"] == municipio_sel)
        ]

        cvegeo = fila.iloc[0]["cvegeo"]

        # Guardar en session_state
        st.session_state["cvegeo_seleccionado"] = cvegeo
        st.session_state["municipio_seleccionado_nombre"] = municipio_sel
        st.session_state["consulta_realizada"] = True



# ============================================================
# ==========       MOSTRAR RESULTADOS DEL MUNICIPIO      =====
# ============================================================

if st.session_state.get("consulta_realizada", False):

    cvegeo = st.session_state["cvegeo_seleccionado"]
    fila_info = info_muni[info_muni["cvegeo"] == cvegeo]

    # =====================================================
    # Caso 1: Municipio sin información
    # =====================================================
    if fila_info.empty or not bool(fila_info.iloc[0].get("tiene_info", False)):

        st.error("Este municipio no cuenta con información disponible.")

        cercanos, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_sin_info(cvegeo)
        municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)

        st.subheader(f"Municipios cercanos a {municipio_actual}:")

        cols = st.columns(3)
        for idx, row in cercanos.iterrows():
            muni = row["Municipio"]
            estado = row["Estado"]
            cve = row["cvegeo"]
            distancia = round(row["Distancia (km)"], 2)
            texto_boton = f"{estado} — {muni} — {distancia} km"

            col = cols[idx % 3]
            with col:
                if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                    st.session_state["cvegeo_seleccionado"] = cve
                    st.session_state["municipio_seleccionado_nombre"] = muni
                    st.session_state["consulta_realizada"] = True
                    st.rerun()

        st.subheader("Mapa de municipios cercanos con información disponible:")
        st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")

        # Cultivos
        st.subheader("Producción total por cultivo")
        st.dataframe(cult_gen)
        st.pyplot(graf1)

        st.subheader("Producción anual")
        st.dataframe(cult_anual)
        st.pyplot(graf2)

    else:

        # =====================================================
        # Caso 2: Municipio con información principal
        # =====================================================
        es_principal = bool(fila_info.iloc[0].get("es_principal", False))

        if es_principal:
            st.success("🌾 Municipio con información y cultivo.")

            top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = principales_similares(cvegeo, top_n=10)
            municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)

            st.subheader(f"Municipios similares a {municipio_actual}:")

            cols = st.columns(3)
            for idx, row in top_similares.iterrows():
                muni = row["Municipio"]
                estado = row["Estado"]
                cve = row["cvegeo"]
                similarity = round(row["Similitud"], 2)
                texto_boton = f"{estado} — {muni} — {similarity}%"

                col = cols[idx % 3]
                with col:
                    if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                        st.session_state["cvegeo_seleccionado"] = cve
                        st.session_state["municipio_seleccionado_nombre"] = muni
                        st.session_state["consulta_realizada"] = True
                        st.rerun()

            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")

            # Cultivos
            st.subheader("Producción total por cultivo")
            st.dataframe(cult_gen)
            st.pyplot(graf1)

            st.subheader("Producción anual")
            st.dataframe(cult_anual)
            st.pyplot(graf2)

        else:

            # =====================================================
            # Caso 3: Municipio con información secundaria
            # =====================================================
            st.info("Municipio con información.")

            top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_secundarios(cvegeo, top_n=10)
            municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)

            st.subheader(f"Municipios similares a {municipio_actual}:")

            cols = st.columns(3)
            for idx, row in top_similares.iterrows():
                muni = row["Municipio"]
                estado = row["Estado"]
                cve = row["cvegeo"]
                similarity = round(row["Similitud"], 2)
                texto_boton = f"{estado} — {muni} — {similarity}%"

                col = cols[idx % 3]
                with col:
                    if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                        st.session_state["cvegeo_seleccionado"] = cve
                        st.session_state["municipio_seleccionado_nombre"] = muni
                        st.session_state["consulta_realizada"] = True
                        st.rerun()

            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")

            # Cultivos
            st.subheader("Producción total por cultivo")
            st.dataframe(cult_gen)
            st.pyplot(graf1)

            st.subheader("Producción anual")
            st.dataframe(cult_anual)
            st.pyplot(graf2)
