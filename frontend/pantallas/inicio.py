import streamlit as st
import matplotlib.pyplot as plt
from backend.DB.conexion import estadisticas_generales_cultivos, ranking_estados

def pantalla_inicio():
    st.header("📊 Panorama General Agrícola de México")
    st.markdown("Una vista rápida y visual de la producción nacional (últimos 10 años).")

    resultado = estadisticas_generales_cultivos()

    if resultado[0] is None:
        st.error("No hay datos disponibles")
        return

    df_top10, df_anual, fig_top10, fig_anual = resultado

    col1, col2, col3 = st.columns(3)

    total_produccion = int(df_anual["produccion"].sum())
    cultivos_count = len(df_top10)
    anios = df_anual["anio"].nunique()

    col1.metric("📦 Producción total (10 años)", f"{total_produccion:,}")
    col2.metric("🌱 Cultivos analizados", cultivos_count)
    col3.metric("📅 Años considerados", anios)

    st.markdown("---")

    # Pie
    st.subheader("🍕 Distribución de la producción por cultivo")
    st.pyplot(fig_top10)

    st.markdown("---")

    # Ranking estados
    st.subheader("🏅 Ranking de estados por producción total")
    df_estados = ranking_estados()
    fig_estados, ax = plt.subplots(figsize=(10, 5))
    ax.bar(df_estados["Estado"], df_estados["Producción"])
    st.pyplot(fig_estados)

    st.markdown("---")

    # Producción anual
    st.subheader("📈 Producción agrícola total por año")
    st.pyplot(fig_anual)
