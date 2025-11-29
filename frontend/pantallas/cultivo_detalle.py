from backend.DB.conexion import obtener_lista_cultivos, obtener_municipios_por_cultivo
import streamlit as st
import unicodedata
import string


import plotly.express as px

def pantalla_detalle_cultivo():
    cultivo = st.session_state.get("cultivo_seleccionado")

    if not cultivo or not isinstance(cultivo, str):
        st.error("Error: cultivo_seleccionado no es un string.")
        st.write("DEBUG:", cultivo, type(cultivo))
        return

    st.header(f"Información del cultivo: {cultivo}")

    df_muni = obtener_municipios_por_cultivo(cultivo)

    if df_muni is None or df_muni.empty:
        st.warning("Este cultivo no tiene municipios registrados en la base.")
        return

    # 1️⃣ AGRUPAR para eliminar repetidos
    df_muni = (
        df_muni.groupby(["cvegeo", "nomgeo"], as_index=False)["produccion"]
        .sum()
    )

    # 2️⃣ QUITAR MUNICIPIOS CON PRODUCCIÓN 0
    df_muni = df_muni[df_muni["produccion"] > 0]


    if df_muni.empty:
        st.warning("Todos los municipios tienen producción cero.")
        return
    
    df_muni["produccion"] = df_muni["produccion"].astype(float).round(2)
    df_muni["produccion_fmt"] = df_muni["produccion"].map(lambda x: f"{x:.2f}")

    # 3️⃣ ORDENAR DESCENDENTE
    df_ord = df_muni.sort_values("produccion", ascending=False)

    st.write(f"### Total municipios productores: {len(df_ord)}")
    # Mostrar con 2 decimales exactos
    st.dataframe(
        df_ord[["cvegeo", "nomgeo", "produccion_fmt"]],
        use_container_width=True
        )

    # ----------------------------------------------
    # 4️⃣ GRÁFICA TOP 10
    # ----------------------------------------------
    st.subheader("Top 10 municipios con mayor producción")
    fig_top = px.bar(
        df_ord.head(10),
        x="nomgeo",
        y="produccion",
        title="Top 10 productores",
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # ----------------------------------------------
    # 5️⃣ GRÁFICA MENORES (pero >0)
    # ----------------------------------------------
    st.subheader("Municipios con menor producción")
    fig_bottom = px.bar(
        df_ord.tail(10),
        x="nomgeo",
        y="produccion",
        title="Menores productores",
    )
    st.plotly_chart(fig_bottom, use_container_width=True)

    # ----------------------------------------------
    if st.button("Volver a cultivos"):
        st.session_state["pantalla_actual"] = "cultivos"
        st.rerun()

