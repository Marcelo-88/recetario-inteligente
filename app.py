import re
import pandas as pd
import streamlit as st

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(
    page_title="Fridolin | Simulación de Costos & Recetario",
    page_icon="🍰",
    layout="wide",
)

# 2. ESTILOS, TIPOGRAFÍA GLOBAL Y COLORES FRIDOLIN (CSS LIMPIO)
CSS_FRIDOLIN = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    /* Aplicar Poppins SOLO a elementos de texto para no romper iconos ni menús del sistema */
    html, body, .main, section[data-testid="stSidebar"] {
        font-family: 'Poppins', sans-serif !important;
    }

    p, span, label, input, button, select {
        font-family: 'Poppins', sans-serif !important;
    }

    /* Fondo General (Crema Soft) */
    .stApp {
        background-color: #FAF8F5;
    }

    /* BANNER PRINCIPAL (Fondo Guindo + Texto Blanco Puro) */
    .header-fridolin {
        background-color: #8B1D2C !important;
        padding: 1.8rem 2rem !important;
        border-radius: 12px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(139, 29, 44, 0.2) !important;
    }
    
    .header-fridolin h1 {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        margin: 0 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        line-height: 1.2 !important;
    }

    .header-fridolin p {
        color: #F3E5E8 !important;
        font-family: 'Poppins', sans-serif !important;
        margin-top: 6px !important;
        margin-bottom: 0 !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
    }

    /* Barra Lateral */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EBE5DF;
    }

    /* Títulos fuera del banner (Títulos de Secciones) */
    .main h1, .main h2, .main h3 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: #8B1D2C !important;
    }

    /* Pestañas / Tabs Activas */
    button[data-baseweb="tab"] {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        color: #555555 !important;
    }
    
    button[aria-selected="true"] {
        color: #8B1D2C !important;
        border-bottom-color: #8B1D2C !important;
    }

    /* Color de Métricas y Valores Destacados */
    [data-testid="stMetricValue"] {
        color: #8B1D2C !important;
        font-weight: 700 !important;
        font-family: 'Poppins', sans-serif !important;
    }
</style>
"""
st.markdown(CSS_FRIDOLIN, unsafe_allow_html=True)

# 3. ENCABEZADO PRINCIPAL (BANNER)
st.markdown(
    """
    <div class="header-fridolin">
        <h1>Fridolin • Centro de Control & Simulación Multinivel</h1>
        <p>Gestión Inteligente de Recetas N1, N2 y N3 • Análisis de Impacto Financiero</p>
    </div>
""",
    unsafe_allow_html=True,
)
