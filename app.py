import streamlit as st
import pandas as pd

st.set_page_config(page_title="Recetario e Impacto de Costos", page_icon="🍰", layout="wide")

st.title("🍰 Simulador de Impacto de Costos N3")

# --- CONEXIÓN CON GOOGLE DRIVE ---
SHEET_ID = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"

URL_LISTA_N3 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=557327778"
URL_RECETAS_N3 = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=563862181"
URL_MERMAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=2105746899"

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        df_l3 = pd.read_csv(URL_LISTA_N3)
        df_r3 = pd.read_csv(URL_RECETAS_N3)
        df_m = pd.read_csv(URL_MERMAS)
        
        # Limpiar espacios en los nombres de las columnas
        df_l3.columns = df_l3.columns.str.strip()
        df_r3.columns = df_r3.columns.str.strip()
        df_m.columns = df_m.columns.str.strip()
        
        return df_l3, df_r3, df_m
    except Exception as e:
        st.error(f"Error al cargar datos desde Google Drive: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_l3, df_r3, df_m = cargar_datos()

if not df_m.empty and not df_l3.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        # Columna de insumos
        col_insumo = 'Insumo Recetario' if 'Insumo Recetario' in df_m.columns else df_m.columns[0]
        lista_insumos = sorted(df_m[col_insumo].dropna().astype(str).unique())
        insumo_sel = st.selectbox("Selecciona el Insumo o Empaque:", options=[""] + lista_insumos)

    with col2:
        incremento = st.number_input("Aumento en el costo del Insumo (Bs):", min_value=0.0, value=1.0, step=0.5)

    if insumo_sel:
        insumo_busqueda = insumo_sel.strip().lower()
        
        # Filtrar las filas de Recetas_N3 donde aparezca el insumo
        filas_afectadas = df_r3[
            df_r3['Materia Prima'].astype(str).str.strip().str.lower() == insumo_busqueda
        ].copy()

        if not filas_afectadas.empty:
            # Calcular la cantidad total usada por receta
            filas_afectadas['Cant_MP'] = pd.to_numeric(filas_afectadas['Cantidad MP'], errors='coerce').fillna(0)
            filas_afectadas['Cant_N1'] = pd.to_numeric(filas_afectadas['Cantidad N1'], errors='coerce').fillna(0)
            filas_afectadas['Cant_N2'] = pd.to_numeric(filas_afectadas['Cantidad N2'], errors='coerce').fillna(0)
            filas_afectadas['Cantidad_Total'] = filas_afectadas['Cant_MP'] + filas_afectadas['Cant_N1'] + filas_afectadas['Cant_N2']

            # Agrupar por producto final
            resumen_insumo = filas_afectadas.groupby('Recetas 3')['Cantidad_Total'].sum().reset_index()

            # Cruzar con Lista_N3
            df_resultado = pd.merge(df_l3, resumen_insumo, on='Recetas 3', how='inner')
            
            # Limpiar columna de Costo R3
            df_resultado['Costo R3'] = pd.to_numeric(df_resultado['Costo R3'], errors='coerce').fillna(0)
            
            # Cálculo directo estilo V5/V8
            df_resultado['Impacto_Bs'] = df_resultado['Cantidad_Total'] * incremento
            df_resultado['Costo_Nuevo'] = df_resultado['Costo R3'] + df_resultado['Impacto_Bs']
            df_resultado['Var_%'] = (df_resultado['Impacto_Bs'] / df_resultado['Costo R3'] * 100).fillna(0)

            # Formatear la tabla final
            tabla_final = pd.DataFrame({
                'Producto N3': df_resultado['Recetas 3'],
                'Estado': df_resultado.get('Estado', 'Activo'),
                'Cantidad Usada': df_resultado['Cantidad_Total'].apply(lambda x: f"{x:.3f}"),
                'Costo Actual': df_resultado['Costo R3'].apply(lambda x: f"Bs {x:.2f}"),
                'Costo Nuevo': df_resultado['Costo_Nuevo'].apply(lambda x: f"Bs {x:.2f}"),
                'Aumento (Bs)': df_resultado['Impacto_Bs'].apply(lambda x: f"+Bs {x:.2f}"),
                'Aumento (%)': df_resultado['Var_%'].apply(lambda x: f"+{x:.1f}%")
            })

            st.subheader(f"Resultados para: {insumo_sel}")
            st.dataframe(tabla_final, use_container_width=True)
        else:
            st.warning(f"No se encontraron recetas N3 que usen directamente '{insumo_sel}'.")
