
import streamlit as st

def aplicar_estilos():
    """
    Aplica CSS personalizado a la app de Streamlit.

    """
    BG_COLOR = "#D19739"
    BTN_BG = "#314528"
    BTN_COLOR = "#586E86"
    HEADER_COLOR = "#2C3E50"
    # Configuración de la página (título, icono, layout)
    st.set_page_config(
        page_title="AgroAnalytics",
        page_icon="🌾",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Título en el sidebar
    st.sidebar.markdown("""
        <style> 
        @import url('https://fonts.googleapis.com/css2?family=Jersey+10&display=swap');
        </style>
        <div style="
            font-size:45px; 
            font-weight:bold; 
            color: """ + BG_COLOR + """;
            text-align:center;
            margin-bottom:20px;
            font-family: 'Jersey 10', sans-serif;
        ">
            AgroAnalytics

        </div>
    """, unsafe_allow_html=True)
    



    # CSS personalizado


    st.markdown("""
    <style>
    /* Fondo de la app */
    [data-testid="stAppViewContainer"] {
        background-color: """ + BG_COLOR + """;
    }

    /* Botones */
    div.stButton > button:first-child {
        background-color: """ + BG_COLOR + """;
        color: """ + HEADER_COLOR + """;
        border-radius: 25px;
        height: 7em;
        width: 165px;
        font-size: 16px;
    }
    div.stButton > button:hover {
    background-color: """ + BTN_COLOR + """;
    
    }

    /* Headers */
    h1, h2, h3 {
        color: """ + BTN_COLOR + """;
        font-family: 'Jersey 10', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: """ + BTN_BG + """;
    }


    /* Tablas */
    .stDataFrame table {
        width: 100%;
        border-collapse: collapse;
    }
    .stDataFrame td {
        text-align: center !important;
        vertical-align: middle !important;
    }
    .stDataFrame th {
        text-align: center !important;
        font-weight: bold !important;
        background-color: """ + BTN_BG + """;
    }
    </style>
    """, unsafe_allow_html=True)
