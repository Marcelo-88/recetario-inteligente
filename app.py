import streamlit as st
import pandas as pd

st.set_page_config(page_title="Recetario Inteligente Completo", page_icon="🍰", layout="wide")

SHEET_ID = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"

# URLs de las 8 Pestañas
GIDS = {
    "Lista_N1": "157973715",
    "Lista_N2": "2109865181",
    "Lista_N3": "557327778",
    "Recetas_N1": "1773641771",
    "Recetas_N2": "874558223",
    "Recetas_N3": "563862181",
    "Materia_Prima": "0",
    "Mermas_Costos": "2105746899"
}

@st.cache_data(ttl=60)
def cargar_todas_las_hojas():
    datos = {}
    for nombre, gid in GIDS.items():
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            datos[nombre] = df
        except Exception:
            datos[nombre] = pd.DataFrame()
    return datos

data = cargar_todas_las_hojas()

st.title("🍰 Recetario Inteligente - Control General y Simulación")

# --- NAVEGACIÓN POR PESTAÑAS PRINCIPALES ---
tab_simulador, tab_recetas_n3, tab_recetas_n2, tab_recetas_n1, tab_mermas = st.tabs([
    "📊 Simulador Multinivel N3", 
    "📖 Recetas N3", 
    "📖 Recetas N2", 
    "📖 Recetas N1", 
    "📋 Mermas y Costos Insumos"
])

# ==========================================
# PESTAÑA 1: SIMULADOR DE COSTOS MULTINIVEL
# ==========================================
with tab_simulador:
    st.subheader("Simulador de Impacto de Costos en Productos Finales (N3)")
    
    df_m = data.get("Mermas_Costos", pd.DataFrame())
    df_r1 = data.get("Recetas_N1", pd.DataFrame())
    df_r2 = data.get("Recetas_N2", pd.DataFrame())
    df_r3 = data.get("Recetas_N3", pd.DataFrame())
    df_l3 = data.get("Lista_N3", pd.DataFrame())

    if not df_m.empty and not df_r3.empty:
        col1, col2 = st.columns(2)
        with col1:
            col_insumo = 'Insumo Recetario' if 'Insumo Recetario' in df_m.columns else df_m.columns[0]
            lista_insumos = sorted(df_m[col_insumo].dropna().astype(str).unique())
            insumo_sel = st.selectbox("Selecciona el Insumo o Empaque:", options=[""] + lista_insumos)

        with col2:
            incremento = st.number_input("Aumento en el costo del Insumo (Bs):", min_value=0.0, value=1.0, step=0.5)

        if insumo_sel:
            target = insumo_sel.strip().lower()

            # 1. Encontrar en qué Subrecetas N1 se usa directamente el insumo
            subrecetas_n1_afectadas = []
            if not df_r1.empty and 'Materia Prima' in df_r1.columns:
                m1 = df_r1[df_r1['Materia Prima'].astype(str).str.strip().str.lower() == target]
                subrecetas_n1_afectadas = m1['Recetas N1'].dropna().unique().tolist()

            # 2. Encontrar en qué Subrecetas N2 se usa directamente el insumo O mediante N1
            subrecetas_n2_afectadas = []
            if not df_r2.empty:
                cond_mp2 = df_r2['Materia Prima'].astype(str).str.strip().str.lower() == target
                cond_n1 = df_r2['Recetas N1'].astype(str).str.strip().isin(subrecetas_n1_afectadas) if 'Recetas N1' in df_r2.columns else False
                m2 = df_r2[cond_mp2 | cond_n1]
                subrecetas_n2_afectadas = m2['Recetas N2'].dropna().unique().tolist()

            # 3. Encontrar qué Recetas N3 se ven afectadas (por MP directa, por N1 o por N2)
            cond_mp3 = df_r3['Materia Prima'].astype(str).str.strip().str.lower() == target
            cond_r1_in_3 = df_r3['Recetas N1'].astype(str).str.strip().isin(subrecetas_n1_afectadas) if 'Recetas N1' in df_r3.columns else False
            cond_r2_in_3 = df_r3['Recetas N2'].astype(str).str.strip().isin(subrecetas_n2_afectadas) if 'Recetas N2' in df_r3.columns else False

            df_r3_afectadas = df_r3[cond_mp3 | cond_r1_in_3 | cond_r2_in_3].copy()

            if not df_r3_afectadas.empty:
                # Sumar cantidades totales
                df_r3_afectadas['Cant_MP'] = pd.to_numeric(df_r3_afectadas.get('Cantidad MP', 0), errors='coerce').fillna(0)
                df_r3_afectadas['Cant_N1'] = pd.to_numeric(df_r3_afectadas.get('Cantidad N1', 0), errors='coerce').fillna(0)
                df_r3_afectadas['Cant_N2'] = pd.to_numeric(df_r3_afectadas.get('Cantidad N2', 0), errors='coerce').fillna(0)
                df_r3_afectadas['Cant_Total'] = df_r3_afectadas['Cant_MP'] + df_r3_afectadas['Cant_N1'] + df_r3_afectadas['Cant_N2']

                resumen = df_r3_afectadas.groupby('Recetas 3')['Cant_Total'].sum().reset_index()

                df_res = pd.merge(df_l3, resumen, on='Recetas 3', how='inner')
                df_res['Costo R3'] = pd.to_numeric(df_res['Costo R3'], errors='coerce').fillna(0)
                df_res['Impacto_Bs'] = df_res['Cant_Total'] * incremento
                df_res['Costo_Nuevo'] = df_res['Costo R3'] + df_res['Impacto_Bs']
                df_res['Var_%'] = (df_res['Impacto_Bs'] / df_res['Costo R3'] * 100).fillna(0)

                tabla = pd.DataFrame({
                    'Producto N3': df_res['Recetas 3'],
                    'Estado': df_res.get('Estado', 'Activo'),
                    'Cantidad Usada en N3': df_res['Cant_Total'].apply(lambda x: f"{x:.3f}"),
                    'Costo Actual': df_res['Costo R3'].apply(lambda x: f"Bs {x:.2f}"),
                    'Costo Nuevo': df_res['Costo_Nuevo'].apply(lambda x: f"Bs {x:.2f}"),
                    'Aumento (Bs)': df_res['Impacto_Bs'].apply(lambda x: f"+Bs {x:.2f}"),
                    'Aumento (%)': df_res['Var_%'].apply(lambda x: f"+{x:.1f}%")
                })

                st.success(f"Resultados encontrados para: {insumo_sel}")
                st.dataframe(tabla, use_container_width=True)
            else:
                st.warning(f"No se encontraron productos N3 afectados por '{insumo_sel}'.")

# ==========================================
# PESTAÑAS VISUALIZADORAS DE RECETAS
# ==========================================
with tab_recetas_n3:
    st.subheader("Estructura de Recetas N3")
    st.dataframe(data.get("Recetas_N3", pd.DataFrame()), use_container_width=True)

with tab_recetas_n2:
    st.subheader("Estructura de Recetas N2 (Subrecetas)")
    st.dataframe(data.get("Recetas_N2", pd.DataFrame()), use_container_width=True)

with tab_recetas_n1:
    st.subheader("Estructura de Recetas N1 (Básicas)")
    st.dataframe(data.get("Recetas_N1", pd.DataFrame()), use_container_width=True)

with tab_mermas:
    st.subheader("Maestro de Mermas y Costos de Insumos")
    st.dataframe(data.get("Mermas_Costos", pd.DataFrame()), use_container_width=True)
