import re
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin | Centro de Control",
    page_icon="🍰",
    layout="wide",
)

CSS_FRIDOLIN = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Poppins', sans-serif !important;
    }

    .stApp {
        background-color: #FAF8F5;
    }

    .header-fridolin {
        background-color: #8B1D2C !important;
        padding: 1.5rem 2rem !important;
        border-radius: 12px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(139, 29, 44, 0.15) !important;
    }
    
    .header-fridolin h1 {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        margin: 0 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }

    .header-fridolin p {
        color: #F3E5E8 !important;
        font-family: 'Poppins', sans-serif !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
        font-size: 0.95rem !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EBE5DF;
    }

    .main h1, .main h2, .main h3, .main h4 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: #8B1D2C !important;
    }

    [data-testid="stMetricValue"] {
        color: #8B1D2C !important;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(CSS_FRIDOLIN, unsafe_allow_html=True)

# ==========================================
# 2. ENCABEZADO PRINCIPAL (BANNER)
# ==========================================
st.markdown(
    """
    <div class="header-fridolin">
        <h1>Fridolin • Centro de Control & Simulación Multinivel</h1>
        <p>Gestión Inteligente de Recetas N1, N2 y N3 • Análisis de Impacto Financiero</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. CARGA Y LIMPIEZA DE DATOS DESDE GOOGLE SHEETS
# ==========================================
ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"

@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    # Limpieza estándar de encabezados
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df.fillna("")

def extraer_num(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return 0.0
    try:
        s = str(val).strip()
        cleaned = re.sub(r"[^\d.,-]", "", s).replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0

def normalizar_texto(val):
    if pd.isna(val):
        return ""
    return str(val).strip()

# ==========================================
# 4. MENÚ LATERAL Y NAVEGACIÓN
# ==========================================
st.sidebar.markdown("### 🥧 Menú Principal")
modo_app = st.sidebar.radio(
    "Selecciona la función:",
    [
        "📋 Ficha Técnica de Producto (N3)",
        "🍰 Simulación Financiera Multinivel",
        "📖 Explorador de Tablas",
    ],
)
st.sidebar.divider()

# ------------------------------------------
# MODO 1: FICHA TÉCNICA DE PRODUCTO (N3)
# ------------------------------------------
if modo_app == "📋 Ficha Técnica de Producto (N3)":
    st.markdown("## 📋 Ficha Técnica Interactiva de Producto Terminado")
    st.caption("Consulta el costo, precios de venta, márgenes y desglosa la estructura multinivel de recetas.")

    try:
        df_recetas_n3 = cargar_pestaña("Recetas_N3")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # Mapeo flexible de columnas para Lista_N3
        col_nom_l3 = df_lista_n3.columns[0]
        col_cod_l3 = df_lista_n3.columns[1] if len(df_lista_n3.columns) > 1 else col_nom_l3

        df_lista_n3["COMBO_LABEL"] = (
            "[" + df_lista_n3[col_cod_l3].astype(str).str.strip() + "] " + df_lista_n3[col_nom_l3].astype(str).str.strip()
        )

        opciones_n3 = sorted([op for op in df_lista_n3["COMBO_LABEL"].unique() if len(op) > 3])
        prod_seleccionado = st.selectbox("🔍 Selecciona un Producto Terminado (N3):", opciones_n3)

        if prod_seleccionado:
            fila_master = df_lista_n3[df_lista_n3["COMBO_LABEL"] == prod_seleccionado].iloc[0]
            nombre_producto = normalizar_texto(fila_master[col_nom_l3])
            codigo_producto = normalizar_texto(fila_master[col_cod_l3])

            # Lectura de Costo y Precios
            costo_r3 = extraer_num(fila_master.iloc[2]) if len(fila_master) > 2 else 0.0
            pv1 = extraer_num(fila_master.iloc[3]) if len(fila_master) > 3 else 0.0
            pv2 = extraer_num(fila_master.iloc[4]) if len(fila_master) > 4 else 0.0
            pv3 = extraer_num(fila_master.iloc[5]) if len(fila_master) > 5 else 0.0

            st.divider()
            st.markdown(f"### 🎂 {nombre_producto} <small style='color:#777;'>(Código ERP: {codigo_producto})</small>", unsafe_allow_html=True)

            # --- MÉTRICAS DE FINANCIERAS ---
            st.markdown("##### 💵 Análisis de Costo & Márgenes")
            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.metric("Costo R3 (Producción)", f"Bs {costo_r3:.2f}")

            with m2:
                if pv1 > 0:
                    margen1 = ((pv1 - costo_r3) / pv1 * 100)
                    st.metric("Precio Venta 1", f"Bs {pv1:.2f}", delta=f"{margen1:.1f}% Margen")
                else:
                    st.metric("Precio Venta 1", "N/A")

            with m3:
                if pv2 > 0:
                    margen2 = ((pv2 - costo_r3) / pv2 * 100)
                    st.metric("Precio Venta 2", f"Bs {pv2:.2f}", delta=f"{margen2:.1f}% Margen")
                else:
                    st.metric("Precio Venta 2", "No Aplica")

            with m4:
                if pv3 > 0:
                    margen3 = ((pv3 - costo_r3) / pv3 * 100)
                    st.metric("Precio Venta 3", f"Bs {pv3:.2f}", delta=f"{margen3:.1f}% Margen")
                else:
                    st.metric("Precio Venta 3", "No Aplica")

            st.divider()

            # --- DESGLOSE ESTRUCTURAL DE LA HOJA RECETAS_N3 ---
            st.markdown("##### 🌳 Estructura Multinivel Desglosada")

            # Filtrar todas las filas correspondientes a la Receta N3 seleccionada
            col_receta_padre = df_recetas_n3.columns[0]
            sub_df = df_recetas_n3[df_recetas_n3[col_receta_padre].astype(str).str.strip().str.upper() == nombre_producto.upper()]

            if sub_df.empty:
                # Búsqueda secundaria por código si el nombre no coincide exactamente
                sub_df = df_recetas_n3[df_recetas_n3.iloc[:, 2].astype(str).str.strip().str.upper() == codigo_producto.upper()]

            if not sub_df.empty:
                # 1. PROCESAR MATERIA PRIMA (Cols B a E aprox en tu Google Sheet)
                # Seleccionar por índice o nombre de columna según la captura
                cols = list(sub_df.columns)
                
                # Materia Prima Directa
                mp_rows = []
                for _, row in sub_df.iterrows():
                    nom_mp = normalizar_texto(row.iloc[1]) # Col B: Materia Prima
                    cod_mp = normalizar_texto(row.iloc[2]) # Col C: Código ERP
                    cat_mp = normalizar_texto(row.iloc[3]) # Col D: Categoría
                    cant_mp = extraer_num(row.iloc[4])     # Col E: Cantidad MP
                    unid_mp = normalizar_texto(row.iloc[5]) if len(row) > 5 else "Kg/U"

                    if nom_mp and nom_mp not in ["NO SE ENCONTRO", "NADA", "-"]:
                        mp_rows.append({
                            "Código ERP": cod_mp if cod_mp else "-",
                            "Nombre del Insumo": nom_mp,
                            "Categoría": cat_mp,
                            "Cantidad": cant_mp,
                            "Unidad": unid_mp
                        })

                df_mp_final = pd.DataFrame(mp_rows).drop_duplicates()

                # 2. PROCESAR RECETAS N1
                n1_rows = []
                for _, row in sub_df.iterrows():
                    if len(row) > 9:
                        nom_n1 = normalizar_texto(row.iloc[6])  # Col G: Recetas N1
                        cod_n1 = normalizar_texto(row.iloc[7])  # Col H: Código N1
                        cant_n1 = extraer_num(row.iloc[8])     # Col I: Cantidad N1
                        unid_n1 = normalizar_texto(row.iloc[9]) # Col J: Unidad N1

                        if nom_n1 and cant_n1 > 0 and nom_n1 not in ["NO SE ENCONTRO", "NADA", "-"]:
                            n1_rows.append({
                                "Código Sub-Receta": cod_n1 if cod_n1 else "-",
                                "Nombre Sub-Receta (N1)": nom_n1,
                                "Cantidad": cant_n1,
                                "Unidad": unid_n1
                            })

                df_n1_final = pd.DataFrame(n1_rows).drop_duplicates()

                # 3. PROCESAR RECETAS N2
                n2_rows = []
                for _, row in sub_df.iterrows():
                    if len(row) > 13:
                        nom_n2 = normalizar_texto(row.iloc[10]) # Col K: Recetas N2
                        cod_n2 = normalizar_texto(row.iloc[11]) # Col L: Código N2
                        cant_n2 = extraer_num(row.iloc[12])     # Col M: Cantidad N2
                        unid_n2 = normalizar_texto(row.iloc[13]) # Col N: Unidad N2

                        if nom_n2 and cant_n2 > 0 and nom_n2 not in ["NO SE ENCONTRO", "NADA", "-"]:
                            n2_rows.append({
                                "Código Sub-Receta": cod_n2 if cod_n2 else "-",
                                "Nombre Intermedio / Relleno (N2)": nom_n2,
                                "Cantidad": cant_n2,
                                "Unidad": unid_n2
                            })

                df_n2_final = pd.DataFrame(n2_rows).drop_duplicates()

                # --- MOSTRAR TABLAS SEPARADAS EN DESPLEGABLES ---
                with st.expander(f"🔹 **Materia Prima Directa** ({len(df_mp_final)} insumos)", expanded=True):
                    if not df_mp_final.empty:
                        st.dataframe(df_mp_final, use_container_width=True)
                    else:
                        st.info("Esta receta no requiere materia prima directa.")

                with st.expander(f"🔴 **Recetas N1 - Pre-elaborados / Base** ({len(df_n1_final)} sub-recetas)", expanded=True):
                    if not df_n1_final.empty:
                        st.dataframe(df_n1_final, use_container_width=True)
                    else:
                        st.caption("Esta receta no incluye sub-recetas de Nivel 1.")

                with st.expander(f"🟠 **Recetas N2 - Intermedios / Rellenos** ({len(df_n2_final)} sub-recetas)", expanded=True):
                    if not df_n2_final.empty:
                        st.dataframe(df_n2_final, use_container_width=True)
                    else:
                        st.caption("Esta receta no incluye sub-recetas de Nivel 2.")

            else:
                st.warning("No se encontraron registros detallados para este producto en la pestaña 'Recetas_N3'.")

    except Exception as e:
        st.error(f"Error al procesar la Ficha Técnica: {e}")

# ------------------------------------------
# MODO 2: SIMULACIÓN FINANCIERA MULTINIVEL
# ------------------------------------------
elif modo_app == "🍰 Simulación Financiera Multinivel":
    st.markdown("## 🍰 Simulación Financiera Proporcional")
    st.caption("Ajusta el precio de un insumo base para evaluar el impacto en N1, N2 y el producto final N3.")

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        col_nom_m = df_mermas.columns[0]
        col_cod_m = df_mermas.columns[1] if len(df_mermas.columns) > 1 else col_nom_m
        col_costo_m = df_mermas.columns[-1]

        df_mermas["COMBO_LABEL"] = (
            "[" + df_mermas[col_cod_m].astype(str).str.strip() + "] " + df_mermas[col_nom_m].astype(str).str.strip()
        )
        lista_opciones = sorted([op for op in df_mermas["COMBO_LABEL"].unique() if len(op) > 3])

        st.subheader("1️⃣ Selecciona el Insumo a Simular")
        opcion_elegida = st.selectbox("Buscar por Código ERP o Nombre de Insumo:", lista_opciones)

        if opcion_elegida:
            datos_insumo = df_mermas[df_mermas["COMBO_LABEL"] == opcion_elegida].iloc[0]
            articulo_mostrar = normalizar_texto(datos_insumo[col_nom_m])
            codigo_target_raw = normalizar_texto(datos_insumo[col_cod_m])
            costo_actual_unitario = extraer_num(datos_insumo[col_costo_m])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Código Insumo ERP", f"[{codigo_target_raw}]")
                st.caption(f"**Nombre:** {articulo_mostrar}")
            with c2:
                nuevo_precio_unitario = st.number_input(
                    "Nuevo precio simulado por Lt/Kg (Bs):",
                    min_value=0.0,
                    value=float(costo_actual_unitario + 1.00) if costo_actual_unitario > 0 else 10.0,
                    step=0.10,
                )
            with c3:
                dif_precio_unitario = nuevo_precio_unitario - costo_actual_unitario
                porc_inc = ((dif_precio_unitario / costo_actual_unitario) * 100) if costo_actual_unitario > 0 else 0.0
                st.metric("Variación Directa", f"+Bs {dif_precio_unitario:.2f}", delta=f"{porc_inc:.1f}%")

            st.info("Simulador listo para calcular la cascada multinivel.")

    except Exception as e:
        st.error(f"Error en la pantalla de simulación: {e}")

# ------------------------------------------
# MODO 3: EXPLORADOR DE TABLAS
# ------------------------------------------
elif modo_app == "📖 Explorador de Tablas":
    st.sidebar.header("📋 Pestañas del Recetario")
    pestaña_activa = st.sidebar.radio(
        "Selecciona la vista:",
        [
            "Recetas_N3",
            "Lista_N3",
            "Recetas_N2",
            "Lista_N2",
            "Recetas_N1",
            "Lista_N1",
            "Materia_Prima",
            "Mermas_Costos",
        ],
    )
    try:
        with st.spinner(f"Cargando {pestaña_activa}..."):
            df = cargar_pestaña(pestaña_activa)

        st.subheader(f"📖 Vista de Datos: {pestaña_activa}")
        busqueda = st.text_input(f"🔍 Buscar en {pestaña_activa}:")

        if busqueda:
            mascara = df.apply(
                lambda row: row.astype(str).str.contains(busqueda, case=False, na=False).any(),
                axis=1,
            )
            df_filtrado = df[mascara]
            st.success(f"Se encontraron **{len(df_filtrado)}** resultados")
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error al cargar la pestaña {pestaña_activa}: {e}")
