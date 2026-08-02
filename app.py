import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Recetario Inteligente", layout="wide")

st.sidebar.title("🎮 Módulos")
modulo = st.sidebar.radio("Selecciona la función:", ["📜 Explorador de Tablas", "💥 Simulación Financiera Multinivel"])

# Carga de datos con caché
@st.cache_data
def cargar_datos():
    try:
        # Intentar cargar archivos de Excel en la raíz del proyecto
        df_recetas = pd.read_excel("recetas.xlsx") if pd.io.common.file_exists("recetas.xlsx") else pd.DataFrame()
        df_costos = pd.read_excel("costos.xlsx") if pd.io.common.file_exists("costos.xlsx") else pd.DataFrame()
        return df_recetas, df_costos
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

# Datos de prueba dinámicos si no existen archivos subidos
def generar_datos_ejemplo():
    # Insumo base (ejemplo: Aceite)
    df_insumo = pd.DataFrame({
        "CODIGO": ["INS-001"],
        "PRODUCTO": ["ACEITE VEGETAL"],
        "PRECIO_ACTUAL": [19.59]
    })
    
    # Productos N2 (Subrecetas / Intermedios)
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
        "% Participacion Insumo": [0.01, 0.22, 0.05, 0.10, 0.12, 0.12]  # El Brownie tiene 22% de aceite
    })
    return df_insumo, df_n2

df_insumo, df_n2 = generar_datos_ejemplo()

if modulo == "💥 Simulación Financiera Multinivel":
    st.title("💥 Simulación Financiera Multinivel")
    
    # Header del insumo
    col1, col2, col3 = st.columns(3)
    
    precio_base = 19.59
    col1.metric("Precio Actual Base", f"Bs {precio_base:.2f}")
    
    nuevo_precio = col2.number_input("Nuevo precio simulado (Bs):", value=30.00, step=0.50)
    
    incremento = nuevo_precio - precio_base
    pct_incremento = (incremento / precio_base) * 100
    
    col3.metric("Incremento Simulado", f"+Bs {incremento:.2f}", delta=f"{pct_incremento:.1f}%")
    
    st.markdown("---")
    st.subheader("📊 Comparativa Ejecutiva de Productos Afectados")
    
    # Asegurar que no existan valores None/NaN en los costos
    df_n2["Costo Actual"] = df_n2["Costo Actual"].fillna(df_n2["COSTO POR KILO A USAR"]).fillna(0.0)
    
    # Cálculo corregido: Variación proporcional según la participación del ingrediente (%)
    df_n2["Variación (Bs)"] = incremento * df_n2["% Participacion Insumo"]
    df_n2["Costo Simulado"] = df_n2["Costo Actual"] + df_n2["Variación (Bs)"]
    df_n2["Variación (%)"] = np.where(
        df_n2["Costo Actual"] > 0, 
        (df_n2["Variación (Bs)"] / df_n2["Costo Actual"]) * 100, 
        0.0
    )
    
    # Formateo de columnas para presentación
    df_display = df_n2.copy()
    df_display["Costo Actual"] = df_display["Costo Actual"].map("Bs {:,.2f}".format)
    df_display["Costo Simulado"] = df_display["Costo Simulado"].map("Bs {:,.2f}".format)
    df_display["Variación (Bs)"] = df_display["Variación (Bs)"].map("+Bs {:,.2f}".format)
    df_display["Variación (%)"] = df_display["Variación (%)"].map("+{:,.1f}%".format)
    
    columnas_visibles = ["Producto / Subreceta", "Estado", "Costo Actual", "Costo Simulado", "Variación (Bs)", "Variación (%)"]
    
    st.dataframe(df_display[columnas_visibles], use_container_width=True)

elif modulo == "📜 Explorador de Tablas":
    st.title("📜 Explorador de Tablas")
    st.info("Módulo para consultar la estructura de recetas y costos de materia prima.")
