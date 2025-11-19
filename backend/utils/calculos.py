
import pandas as pd
from backend.DB.conexion import leer_tabla, top_similares_sql

#Diccionarios

# Diccionarios globales para variables categóricas
niveles_horizonte = {
    "N": 1, "Ócrico": 2, "Mólico": 3, "Fólico": 4, "Úmbrico": 5,
    "Cámbico": 6, "Árgico": 7, "Cálcico": 8, "Nítico": 9, "Vértico": 10,
    "Gípsico": 11, "Férrico": 12, "Dúrico": 13, "Petrocálcico": 14,
    "Petrodúrico": 15, "Ándico": 16, "Vítrico": 17,
    "Cálcico, Árgico": (8 + 7)/2, "Árgico, Cálcico": (7 + 8)/2,
    "Gípsico, Cálcico": (11 + 8)/2, "Vértico, Cálcico": (10 + 8)/2
}

niveles_col_seco_l = {
    "Negro": 0, "Oscuro": 2, "Marrón oscuro": 3, "Marrón": 4, "Marrón claro": 5,
    "Amarillento": 6, "Amarillo pálido": 7, "Claro": 8, "Muy claro": 9, "Blanco": 10,
    "Marrón oscuro, Marrón": (3 + 4)/2, "Marrón, Marrón claro": (4 + 5)/2
}

niveles_col_hum_l = {
    "Negro": 0, "Oscuro": 2, "Marrón oscuro": 3, "Marrón": 4, "Marrón claro": 5,
    "Amarillento": 6, "Amarillo pálido": 7, "Claro": 8, "Muy claro": 9, "Blanco": 10,
    "Marrón oscuro, Marrón": (3 + 4)/2, "Marrón, Marrón claro": (4 + 5)/2
}


# --- FUNCIONES AUXILIARES PARA CÁLCULO DE SIMILITUDES --- #
#función para sacar el promedio de alguna variable de clima
def promedio_climatico(tabla="clima", variable="TMIN"):
    """
    Calcula el promedio de una variable climática (TMIN, TMAX, PRECIP) por municipio.
    
    Retorna un DataFrame con:
    - cvegeo_muni
    - promedio_variable
    """
    # Leer la tabla completa
    df = leer_tabla(tabla)

    # Filtrar columnas que corresponden a la variable
    cols_variable = [col for col in df.columns if col.startswith(variable)]
    
    # Calcular el promedio por fila (por año, o por registro)
    df["promedio_" + variable] = df[cols_variable].mean(axis=1)
    
    # Agrupar por municipio si hay múltiples años
    df_promedio = df.groupby("cvegeo_muni")["promedio_" + variable].mean().reset_index()
    
    return df_promedio
"""
prom_tmin = promedio_climatico(variable="TMIN")
prom_tmax = promedio_climatico(variable="TMAX")
prom_precip = promedio_climatico(variable="PRECIP")

print(prom_tmin.head(20))
print(prom_tmax.head(20))
print(prom_precip.head(20))
"""
#función para pasar las variables categóricas a numéricas
def convertir_variables_categoricas_simple(df):
    df["horizonte_num"] = df["horizonte"].map(niveles_horizonte)
    df["col_seco_num"] = df["col_seco_l"].map(niveles_col_seco_l)
    df["col_hum_num"] = df["col_hum_l"].map(niveles_col_hum_l)

    # Normalizar
    for col in ["horizonte_num", "col_seco_num", "col_hum_num"]:
        min_val = df[col].min()
        max_val = df[col].max()
        df[col] = (df[col] - min_val) / (max_val - min_val) if max_val != min_val else 1.0

    return df[["horizonte_num", "col_seco_num", "col_hum_num"]]


#función para obtener el valor mínnimo y máximo globar de una variable de edafologia
def min_max_edafologia(variable: str, tabla: str = "edafologia"):
    """
    Devuelve el valor mínimo y máximo global de una variable edafológica.

    Parámetros:
    - variable: str → nombre de la columna en la tabla de edafología
    - tabla: str → nombre de la tabla en la base de datos (por defecto 'edafologia')

    Retorna:
    - (min_val, max_val)
    """
    # Leer solo la columna de interés
    df = leer_tabla(tabla, columnas=[variable])
    
    # Valores mínimo y máximo global
    min_val = df[variable].min()
    max_val = df[variable].max()
    
    return min_val, max_val


#función para obtener el valor minimo y máximo de la variables de clima
def min_max_climatico(variable="TMIN", tabla="clima"):
    """
    Devuelve el valor mínimo y máximo global de una variable climática.
    
    Parámetros:
    - variable: str → 'TMIN', 'TMAX' o 'PRECIP'
    - tabla: str → nombre de la tabla en la base de datos
    
    Retorna:
    - (min_val, max_val)
    """
    # Obtener promedio por municipio
    df_prom = promedio_climatico(tabla=tabla, variable=variable)
    
    # Valores mínimos y máximos globales
    min_val = df_prom["promedio_" + variable].min()
    max_val = df_prom["promedio_" + variable].max()
    
    return min_val, max_val

# función para hacer un diccionario de mínimos y máximos globales
def diccionario_min_max(climaticas: list = ["TMIN", "TMAX", "PRECIP"],
                        edafologicas: list = ["ph", "arcilla", "arena", "limo"]):
    """
    Genera un diccionario con los valores mínimos y máximos globales de variables climáticas y edafológicas.
    
    Retorna:
    {
        "TMIN": {"min": 12.3, "max": 28.4},
        "TMAX": {"min": 18.5, "max": 35.2},
        "PRECIP": {"min": 0, "max": 320},
        "ph": {"min": 4.2, "max": 8.7},
        ...
    }
    """
    min_max_dict = {}

    # Variables climáticas
    for var in climaticas:
        df_prom = promedio_climatico(variable=var)  # tu función
        min_val = df_prom["promedio_" + var].min()
        max_val = df_prom["promedio_" + var].max()
        min_max_dict[var] = {"min": min_val, "max": max_val}

    # Variables edafológicas
    for var in edafologicas:
        min_val, max_val = min_max_edafologia(var)  # tu función
        min_max_dict[var] = {"min": min_val, "max": max_val}

    return min_max_dict


#fórmula de normalización xnom=(x-xmin)/(xmax-xmin)
def normalizar_valor(x, nombre_var=None, tipo="clima", tabla_edafologia=None, xmin=None, xmax=None):
    """
    Normaliza un valor usando xnorm = (x - xmin) / (xmax - xmin)
    
    Parámetros:
    - x: float -> valor a normalizar
    - nombre_var: str -> nombre de la variable (para calcular xmin y xmax si no se pasan)
    - tipo: "clima" o "edafologia"
    - tabla_edafologia: str -> tabla de edafología (si tipo="edafologia")
    - xmin, xmax: float -> mínimo y máximo global de la variable (opcional)
    
    Retorna:
    - valor normalizado entre 0 y 1
    """
    if xmin is None or xmax is None:
        if tipo == "clima":
            df = promedio_climatico(variable=nombre_var)
            col_prom = "promedio_" + nombre_var
            xmin = df[col_prom].min()
            xmax = df[col_prom].max()
        elif tipo == "edafologia":
            if tabla_edafologia is None:
                raise ValueError("Se debe indicar la tabla de edafología")
            df = leer_tabla(tabla_edafologia, columnas=[nombre_var])
            xmin = df[nombre_var].min()
            xmax = df[nombre_var].max()
        else:
            raise ValueError("tipo debe ser 'clima' o 'edafologia'")

    if xmax == xmin:
        return 0.0  # evitar división por cero
    return (x - xmin) / (xmax - xmin)


# formula de similitud y escala: similitud=1-abs(xnom1 - xnom2)
def similitud_escala(x, y):
    import math
    # si x o y es NaN, devolvemos 0.0
    if x is None or y is None or math.isnan(x) or math.isnan(y):
        return 0.0
    return 1 - abs(x - y)  # x e y normalizados entre 0 y 1



"""
#comando para correrlo: streamlit run frontend/app.py
#comando para correrlo: streamlit run frontend/app.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from backend.utils.analysis import principales_similares, municipios_sin_info, municipios_secundarios
from streamlit_folium import st_folium
from backend.DB.conexion import leer_tabla, leer_geografia, estadisticas_generales_cultivos
import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

from frontend.diseño import aplicar_estilos

# Aplicar los estilos
aplicar_estilos()

st.title("Detección de municipios similares")



# ---------------- Pantalla "Inicio" ----------------
if pagina == "Inicio":
    st.header("Resumen agrícola nacional")

    resultado = estadisticas_generales_cultivos()

    if resultado[0] is None:
        st.error("No hay datos disponibles")
    else:
        df_top10, df_anual, fig_top10, fig_anual = resultado

        st.subheader("Top 10 cultivos más producidos (10 años)")
        st.dataframe(df_top10)
        st.pyplot(fig_top10)

        st.subheader("Producción agrícola total por año")
        st.dataframe(df_anual)
        st.pyplot(fig_anual)

    st.stop()  # ⛔ NO SIGUE A LA OTRA PANTALLA


tabla_muni = leer_tabla("municipios")
info_muni = leer_tabla("info_municipios")

# ---- Sidebar: Selección de estado y municipio ----
pagina = st.sidebar.radio(
    "Navegación:",
    ["Inicio", "Buscador de municipios"]
)
estado_sel = st.sidebar.selectbox("Selecciona un estado", sorted(tabla_muni["nombre_ent"].unique()))
municipios_estado = tabla_muni[tabla_muni["nombre_ent"] == estado_sel]["nomgeo"].unique()
municipio_sel = st.sidebar.selectbox("Selecciona un municipio", sorted(municipios_estado))

# ---- Botón: Buscar información del municipio ----
if st.sidebar.button("Consultar información del municipio"):
    # Buscar el CVEGEO del municipio seleccionado
    fila = tabla_muni[
        (tabla_muni["nombre_ent"] == estado_sel) &
        (tabla_muni["nomgeo"] == municipio_sel)
    ]

    cvegeo = fila.iloc[0]["cvegeo"]
        # Guardar en session_state
    st.session_state["cvegeo_seleccionado"] = cvegeo
    st.session_state["municipio_seleccionado_nombre"] = municipio_sel
    st.session_state["consulta_realizada"] = True


    # Buscar si el municipio tiene info
# ---- Renderizar resultados si ya se hizo una consulta ----
if st.session_state.get("consulta_realizada", False):
    cvegeo = st.session_state["cvegeo_seleccionado"]
    fila_info = info_muni[info_muni["cvegeo"] == cvegeo]

    if fila_info.empty or not bool(fila_info.iloc[0].get("tiene_info", False)):
        st.error("Este municipio no cuenta con información disponible.")
        #st.subheader("Municipios cercanos con información disponible:")
        cercanos, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_sin_info(cvegeo)
        municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)
        st.subheader(f"Municipios cercanos a {municipio_actual}:")
      
        #st.dataframe(cercanos)
        cols = st.columns(3)
        for idx, row in cercanos.iterrows():
            muni = row["Municipio"]
            estado = row["Estado"]
            cve = row["cvegeo"]
            distancia = round(row["Distancia (km)"], 2)
            texto_boton = f"{estado} — {muni} — {distancia}"

            col = cols[idx % 3]   # 👉 coloca los botones en filas de 3
            with col:

                if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                    st.session_state["cvegeo_seleccionado"] = cve
                    st.session_state["municipio_seleccionado_nombre"] = muni
                    st.session_state["consulta_realizada"] = True
                    st.rerun()

        st.subheader("Mapa de municipios cercanos con información disponible:")
        st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")
                                #cosas de cultivos
        st.subheader("Producción total por cultivo")
        st.dataframe(cult_gen)
        st.pyplot(graf1)

        st.subheader("Producción anual")
        st.dataframe(cult_anual)
        st.pyplot(graf2)

    else:
        es_principal = bool(fila_info.iloc[0].get("es_principal", False))

        if es_principal:
            st.success("🌾 Municipio con información y cultivo.")
            #top_similares, mapa = principales_similares(cvegeo, top_n=10)
            top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = principales_similares(cvegeo, top_n=10)
            municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)
            st.subheader(f"Municipios similares a {municipio_actual}:")


            #st.subheader("Municipios similares:")
            #st.dataframe(top_similares)
            cols = st.columns(3)
            for idx, row in top_similares.iterrows():
                muni = row["Municipio"]
                estado = row["Estado"]
                cve = row["cvegeo"]
                similarity = round(row["Similitud"], 2)
                texto_boton = f"{estado} — {muni} — {similarity}%"
                col = cols[idx % 3]   # 👉 coloca los botones en filas de 3
                with col:

                    if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                        st.session_state["cvegeo_seleccionado"] = cve
                        st.session_state["municipio_seleccionado_nombre"] = muni
                        st.session_state["consulta_realizada"] = True
                        st.rerun()

            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")
            #cosas de cultivos
            st.subheader("Producción total por cultivo")
            st.dataframe(cult_gen)
            st.pyplot(graf1)

            st.subheader("Producción anual")
            st.dataframe(cult_anual)
            st.pyplot(graf2)


        else:
            st.info("Municipio con información.")
            top_similares, mapa, cult_gen, cult_anual, graf1, graf2 = municipios_secundarios(cvegeo, top_n=10)
            municipio_actual = st.session_state.get("municipio_seleccionado_nombre", municipio_sel)
            st.subheader(f"Municipios similares a {municipio_actual}:")
            #st.dataframe(top_similares)
            cols = st.columns(3)
            for idx, row in top_similares.iterrows():
                muni = row["Municipio"]
                estado = row["Estado"]
                cve = row["cvegeo"]
                similarity = round(row["Similitud"], 2)
                texto_boton = f"{estado} — {muni} — {similarity}%"
                col = cols[idx % 3]   # 👉 coloca los botones en filas de 3
                with col:

                    if st.button(texto_boton, key=f"sim_{cve}_{idx}"):
                        st.session_state["cvegeo_seleccionado"] = cve
                        st.session_state["municipio_seleccionado_nombre"] = muni
                        st.session_state["consulta_realizada"] = True
                        st.rerun()
              

            st.subheader("Mapa de municipios similares:")
            st_folium(mapa, width=600, height=400, key=f"mapa_{cvegeo}")
                        #cosas de cultivos
            st.subheader("Producción total por cultivo")
            st.dataframe(cult_gen)
            st.pyplot(graf1)

            st.subheader("Producción anual")
            st.dataframe(cult_anual)
            st.pyplot(graf2)



"""
