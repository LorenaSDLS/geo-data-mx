#comando para correrlo: streamlit run frontend/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, municipios_sin_info, municipios_secundarios
from streamlit_folium import st_folium
from backend.DB.conexion import leer_tabla, leer_geografia, estadisticas_generales_cultivos, ranking_estados, cantidad_cultivos_por_anio, leer_datos_edaficos
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
from frontend.diseño import aplicar_estilos
import plotly.graph_objects as go




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

    st.header(f"🔍 Resultados para {st.session_state['municipio_seleccionado_nombre']}")
    emb_df=pd.read_parquet("frontend/embeddings.parquet") # ---------------------> Cargar embeddings
    emb_df.index = emb_df.index.astype(str)
    import torch
    from torch.nn.functional import cosine_similarity
    cve_list = emb_df.index.tolist()
    emb_tensor = torch.tensor(emb_df.values, dtype=torch.float32)
    # 5) Obtener embedding del municipio seleccionado
    try:
        i_idx = cve_list.index(cvegeo)
    except ValueError:
        st.error("❌ Ese CVEGEO no existe en el archivo de embeddings.")
        st.stop()

    i_emb = emb_tensor[i_idx].unsqueeze(0)

    # 6) Similitud coseno contra todos
    sim_all = cosine_similarity(i_emb, emb_tensor)

    # 7) Crear DataFrame de resultados
    resultados = pd.DataFrame({
        "CVEGEO": cve_list,
        "similitud": sim_all.numpy()
    })

    # Eliminar el propio municipio
    #resultados = resultados[resultados["CVEGEO"] != cvegeo]

    # 8) Tomar TOP 10 más parecidos
    top10 = resultados.sort_values("similitud", ascending=False).head(15)

    st.subheader("🏅 Top 10 municipios más similares")

# --- Convertir similitud a porcentaje (0–100) ---
    top10["similitud_pct"] = (top10["similitud"] * 100).round(2)

# --- Traer nombres municipio y estado usando tabla_muni ---
    top10 = top10.merge(
        tabla_muni[["cvegeo", "nomgeo", "nombre_ent"]],
        how="left",
        left_on="CVEGEO",
        right_on="cvegeo"
    )

# --- Hacer layout de 3 columnas ---
    cols = st.columns(3)

    for idx, row in top10.iterrows():
        muni = row["nomgeo"]
        estado = row["nombre_ent"]
        cve = row["CVEGEO"]
        similarity = row["similitud_pct"]

        texto_boton = f"{estado} — {muni} — {similarity:.2f}%"

        col = cols[idx % 3]
        with col:
            if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
            # Recargar pantalla con el nuevo municipio seleccionado
                st.session_state["cvegeo_seleccionado"] = cve
                st.session_state["municipio_seleccionado_nombre"] = muni
                st.session_state["consulta_realizada"] = True
                st.rerun()
                st.subheader("📊 Comparación de características")
                muni_base = leer_caracteristicas_municipio(cvegeo)
                caracteristicas = muni_base.index.tolist()[1:] 
                muni_base_vals = muni_base.values[1:]
                muni_base = info_muni[info_muni["cvegeo"] == cvegeo][caracteristicas].iloc[0]
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(r=muni_base.values,
                                              theta=caracteristicas,fill='toself',name=f"{st.session_state['municipio_seleccionado_nombre']} (base)",line=dict(color='red'),opacity=0.7))
                

                
           



