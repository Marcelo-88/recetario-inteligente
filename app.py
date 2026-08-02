import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Recetario Inteligente", layout="wide")

st.sidebar.title("🎮 Módulos")
modulo = st.sidebar.radio("Selecciona la función:", ["📜 Explorador de Tablas", "💥 Simulación Financiera Multinivel"])

# Carga de datos
@st.cache_data
def cargar_datos():
    try:
        df_recetas = pd.read_excel("recetas.xlsx") if pd.io.common.file_exists("recetas.xlsx") else pd.DataFrame()
        df_costos = pd.read_excel("costos.xlsx") if pd.io.common.file_exists("costos.xlsx") else pd.DataFrame()
        return df_recetas, df_costos
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_recetas, df_costos = cargar_datos()

# Base de datos de ejemplo para materias primas si aún no carga el Excel
diccionario_insumos = {
    "ACEITE VEGETAL": {"precio_base": 19.59, "participacion_default": 0.22},
    "HARINA DE TRIGO": {"precio_base": 6.50, "participacion_default": 0.45},
    "AZÚCAR REFINADA": {"precio_base": 7.20, "participacion_default": 0.30},
    "COBERTURA DE CHOCOLATE": {"precio_base": 42.00, "participacion_default": 0.15},
    "MANTEQUILLA": {"precio_base": 55.00, "participacion_default": 0.18}
}

# ---------------------------------------------------------
# MÓDULO 1: EXPLORADOR DE TABLAS
# ---------------------------------------------------------
if modulo == "📜 Explorador de Tablas":
    st.title("📜 Explorador de Tablas")
    st.info("Módulo para consultar la estructura de recetas y costos de materia prima.")
    
    tab1, tab2 = st.tabs(["📋 Lista de Recetas", "💰 Costos de Materia Prima"])
    
    with tab1:
        st.subheader("Estructura de Recetas")
        if not df_recetas.empty:
            st.dataframe(df_recetas, use_container_width=True)
        else:
            st.warning("Conecta tus URLs de Google Drive o sube recetas.xlsx para visualizar el catálogo.")
            
    with tab2:
        st.subheader("Base de Costos")
        if not df_costos.empty:
            st.dataframe(df_costos, use_container_width=True)
        else:
            st.warning("Conecta tus URLs de Google Drive o sube costos.xlsx para visualizar la tabla.")

# ---------------------------------------------------------
# MÓDULO 2: SIMULACIÓN FINANCIERA MULTINIVEL (DINÁMICO)
# ---------------------------------------------------------
elif modulo == "💥 Simulación Financiera Multinivel":
    st.title("💥 Simulación Financiera Multinivel")
    
    # SELECCIÓN DINÁMICA DE MATERIA PRIMA
    st.subheader("1️⃣ Selecciona la Materia Prima a simular")
    
    insumo_seleccionado = st.selectbox(
        "Buscar o seleccionar insumo/ingrediente:",
        options=list(diccionario_insumos.keys()),
        index=0
    )
    
    datos_insumo = diccionario_insumos[insumo_seleccionado]
    precio_base = datos_insumo["precio_base"]
    participacion_real = datos_insumo["participacion_default"]
    
    st.markdown("---")
    
    # METRICAS DEL INSUMO
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Precio Actual Base", f"Bs {precio_base:.2f}")
    
    nuevo_precio = col2.number_input(
        f"Nuevo precio simulado para {insumo_seleccionado} (Bs):", 
        value=float(precio_base * 1.20), 
        step=0.50
    )
    
    incremento = nuevo_precio - precio_base
    pct_incremento = (incremento / precio_base) * 100 if precio_base > 0 else 0
    
    col3.metric("Incremento Simulado", f"+Bs {incremento:.2f}", delta=f"{pct_incremento:.1f}%")
    
    st.markdown("---")
    st.subheader(f"📊 Productos Afectados por la variación de: {insumo_seleccionado}")
    
    # Tabla con datos corregidos
    df_n2 = pd.DataFrame({
        "Producto / Subreceta": [
            "MASA QUEQUE HUMEDA", 
            "Brownie 3,3", 
            "COBERTURA DE CHOCOLATE E", 
            "MASA DE CHOCOLATE", 
            "MASA DE CHOCOLATE HUMEDA", 
            "Masa de chocolate humeda hu"
        ],
        "Estado": ["Activo"] * 6,
        "COSTO POR KILO A USAR": [885.80, 40.75, 25.50, 30.00, 32.10, 31.80],
        "Costo Actual": [885.80, 40.75, 25.50, 30.00, 32.10, 31.80],
        "% Participacion Insumo": [0.01, participacion_real, 0.05, 0.10, 0.12, 0.12]
    })
    
    df_n2["Costo Actual"] = df_n2["Costo Actual"].fillna(df_n2["COSTO POR KILO A USAR"]).fillna(0.0)
    df_n2["Variación (Bs)"] = incremento * df_n2["% Participacion Insumo"]
    df_n2["Costo Simulado"] = df_n2["Costo Actual"] + df_n2["Variación (Bs)"]
    df_n2["Variación (%)"] = np.where(
        df_n2["Costo Actual"] > 0, 
        (df_n2["Variación (Bs)"] / df_n2["Costo Actual"]) * 100, 
        0.0
    )
    
    df_display = df_n2.copy()
    df_display["Costo Actual"] = df_display["Costo Actual"].map("Bs {:,.2f}".format)
    df_display["Costo Simulado"] = df_display["Costo Simulado"].map("Bs {:,.2f}".format)
    df_display["Variación (Bs)"] = df_display["Variación (Bs)"].map("+Bs {:,.2f}".format)
    df_display["Variación (%)"] = df_display["Variación (%)"].map("+{:,.1f}%".format)
    
    columnas_visibles = ["Producto / Subreceta", "Estado", "Costo Actual", "Costo Simulado", "Variación (Bs)", "Variación (%)"]
    
    st.dataframe(df_display[columnas_visibles], use_container_width=True)
