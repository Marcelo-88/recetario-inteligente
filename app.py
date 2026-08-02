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
    # Limpieza estándar de encabezados de columna
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df.fillna("")

def extraer_num(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA", "No Aplica"]:
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

def buscar_valor_columna(df_row, lista_palabras_clave):
    """Busca dinámicamente un valor en la fila según los nombres de columna."""
    for col in df_row.index:
        col_upper = str(col).strip().upper()
        if any(clave.upper() in col_upper for clave in lista_palabras_clave):
            val = df_row[col]
            num = extraer_num(val)
            if num > 0 or str(val).strip() in ["0", "0.0", "0,0"]:
                return num
    return 0.0

# ==========================================
# 4. MENÚ LATERAL Y NAVEGACIÓN
# ==========================================
st.sidebar.markdown("### 🥧 Menú Principal")
modo_app = st.sidebar.radio(
    "Selecciona la función:",
    [
        "📋 Ficha Técnica de Producto (N3)",
        "📊 Control de Márgenes y Estados (N3)",
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

            costo_r3 = buscar_valor_columna(fila_master, ["Costo Total N3", "Costo R3", "Costo Total", "Costo"])
            pv1 = buscar_valor_columna(fila_master, ["Precio Venta 1", "PV1", "Precio 1"])
            pv2 = buscar_valor_columna(fila_master, ["Precio Venta 2", "PV2", "Precio 2"])
            pv3 = buscar_valor_columna(fila_master, ["Precio Venta 3", "PV3", "Precio 3"])

            st.divider()
            st.markdown(f"### 🎂 {nombre_producto} <small style='color:#777;'>(Código ERP: {codigo_producto})</small>", unsafe_allow_html=True)

            # --- MÉTRICAS FINANCIERAS ---
            st.markdown("##### 💵 Análisis de Costo & Márgenes")
            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.metric("Costo R3 (Producción)", f"Bs {costo_r3:.2f}")

            with m2:
                if pv1 > 0:
                    margen1 = ((pv1 - costo_r3) / pv1 * 100)
                    st.metric("Precio Venta 1", f"Bs {pv1:.2f}", delta=f"{margen1:.1f}% Margen")
                else:
                    st.metric("Precio Venta 1", "No Aplica")

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

            # --- DESGLOSE ESTRUCTURAL MULTINIVEL ---
            st.markdown("##### 🌳 Estructura Multinivel Desglosada")

            col_receta_padre = df_recetas_n3.columns[0]
            sub_df = df_recetas_n3[df_recetas_n3[col_receta_padre].astype(str).str.strip().str.upper() == nombre_producto.upper()]

            if sub_df.empty:
                sub_df = df_recetas_n3[df_recetas_n3.iloc[:, 2].astype(str).str.strip().str.upper() == codigo_producto.upper()]

            if not sub_df.empty:
                # 1. MATERIA PRIMA DIRECTA
                mp_rows = []
                for _, row in sub_df.iterrows():
                    nom_mp = normalizar_texto(row.iloc[1])
                    cod_mp = normalizar_texto(row.iloc[2])
                    cat_mp = normalizar_texto(row.iloc[3])
                    cant_mp = extraer_num(row.iloc[4])
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

                # 2. RECETAS N1
                n1_rows = []
                for _, row in sub_df.iterrows():
                    if len(row) > 9:
                        nom_n1 = normalizar_texto(row.iloc[6])
                        cod_n1 = normalizar_texto(row.iloc[7])
                        cant_n1 = extraer_num(row.iloc[8])
                        unid_n1 = normalizar_texto(row.iloc[9])

                        if nom_n1 and cant_n1 > 0 and nom_n1 not in ["NO SE ENCONTRO", "NADA", "-"]:
                            n1_rows.append({
                                "Código Sub-Receta": cod_n1 if cod_n1 else "-",
                                "Nombre Sub-Receta (N1)": nom_n1,
                                "Cantidad": cant_n1,
                                "Unidad": unid_n1
                            })

                df_n1_final = pd.DataFrame(n1_rows).drop_duplicates()

                # 3. RECETAS N2
                n2_rows = []
                for _, row in sub_df.iterrows():
                    if len(row) > 13:
                        nom_n2 = normalizar_texto(row.iloc[10])
                        cod_n2 = normalizar_texto(row.iloc[11])
                        cant_n2 = extraer_num(row.iloc[12])
                        unid_n2 = normalizar_texto(row.iloc[13])

                        if nom_n2 and cant_n2 > 0 and nom_n2 not in ["NO SE ENCONTRO", "NADA", "-"]:
                            n2_rows.append({
                                "Código Sub-Receta": cod_n2 if cod_n2 else "-",
                                "Nombre Intermedio / Relleno (N2)": nom_n2,
                                "Cantidad": cant_n2,
                                "Unidad": unid_n2
                            })

                df_n2_final = pd.DataFrame(n2_rows).drop_duplicates()

                # MOSTRAR EN ACORDEONES
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
# MODO 2: CONTROL DE MÁRGENES Y ESTADOS (N3)
# ------------------------------------------
elif modo_app == "📊 Control de Márgenes y Estados (N3)":
    st.markdown("## 📊 Tablero de Control de Márgenes por Estado")
    st.caption("Visualiza de forma rápida qué productos están dentro o fuera del objetivo de rentabilidad.")

    try:
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # Intentar detectar la columna Estado
        col_estado = None
        for col in df_lista_n3.columns:
            if "ESTADO" in str(col).upper() or "STATUS" in str(col).upper():
                col_estado = col
                break

        if not col_estado:
            col_estado = df_lista_n3.columns[-1]

        # Obtener valores únicos de Estado
        estados_disponibles = sorted([str(e).strip() for e in df_lista_n3[col_estado].unique() if str(e).strip()])
        
        # Filtros superiores
        f1, f2 = st.columns([1, 2])
        with f1:
            estado_sel = st.multiselect("📌 Filtrar por Estado:", estados_disponibles, default=estados_disponibles)
        with f2:
            busqueda_prod = st.text_input("🔍 Buscar por Nombre o Código:")

        # Procesar filas para calcular métricas de la tabla
        datos_procesados = []
        for _, row in df_lista_n3.iterrows():
            est_val = str(row[col_estado]).strip()
            
            # Aplicar filtro de estado
            if estado_sel and est_val not in estado_sel:
                continue

            nombre = normalizar_texto(row.iloc[0])
            codigo = normalizar_texto(row.iloc[1]) if len(row) > 1 else "-"
            
            # Aplicar filtro de texto
            if busqueda_prod:
                if busqueda_prod.lower() not in nombre.lower() and busqueda_prod.lower() not in codigo.lower():
                    continue

            costo = buscar_valor_columna(row, ["Costo Total N3", "Costo R3", "Costo Total", "Costo"])
            pv1 = buscar_valor_columna(row, ["Precio Venta 1", "PV1", "Precio 1"])
            pv2 = buscar_valor_columna(row, ["Precio Venta 2", "PV2", "Precio 2"])

            margen1 = ((pv1 - costo) / pv1 * 100) if pv1 > 0 else 0.0
            margen2 = ((pv2 - costo) / pv2 * 100) if pv2 > 0 else 0.0

            datos_procesados.append({
                "Código ERP": codigo,
                "Producto Terminado": nombre,
                "Estado": est_val if est_val else "Sin Estado",
                "Costo R3 (Bs)": costo,
                "Precio Venta 1 (Bs)": pv1,
                "% Margen PV1": margen1,
                "Precio Venta 2 (Bs)": pv2,
                "% Margen PV2": margen2,
            })

        df_tabla_margenes = pd.DataFrame(datos_procesados)

        if not df_tabla_margenes.empty:
            st.markdown(f"**Mostrando `{len(df_tabla_margenes)}` productos**")

            # --- LÓGICA DE COLORES SEGÚN REGLAS DE NEGOCIO ---
            def colorear_pv1(val):
                if val <= 0:
                    return ""
                if val >= 60.0:
                    return "background-color: #D4EDDA; color: #155724; font-weight: bold;"  # Verde
                elif 55.0 <= val <= 59.99:
                    return "background-color: #FFF3CD; color: #856404; font-weight: bold;"  # Amarillo
                else:
                    return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"  # Rojo

            def colorear_pv2(val):
                if val <= 0:
                    return ""
                if val > 55.0:
                    return "background-color: #D4EDDA; color: #155724; font-weight: bold;"  # Verde
                elif 46.0 <= val <= 54.99:
                    return "background-color: #FFF3CD; color: #856404; font-weight: bold;"  # Amarillo
                else:
                    return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"  # Rojo

            # Aplicar estilos utilizando .map() (compatible con Pandas >= 2.1)
            # con fallback a .applymap por si el entorno usara una versión muy antigua de Pandas
            styler = df_tabla_margenes.style
            
            if hasattr(styler, "map"):
                styler = styler.map(colorear_pv1, subset=["% Margen PV1"]).map(colorear_pv2, subset=["% Margen PV2"])
            else:
                styler = styler.applymap(colorear_pv1, subset=["% Margen PV1"]).applymap(colorear_pv2, subset=["% Margen PV2"])

            tabla_estilizada = styler.format({
                "Costo R3 (Bs)": "{:.2f} Bs",
                "Precio Venta 1 (Bs)": "{:.2f} Bs",
                "% Margen PV1": "{:.1f}%",
                "Precio Venta 2 (Bs)": "{:.2f} Bs",
                "% Margen PV2": "{:.1f}%",
            })

            # Leyenda explicativa
            st.markdown("""
                <div style="display:flex; gap:15px; margin-bottom:10px; font-size:0.85rem;">
                    <span><b>Leyenda PV1:</b> 🟢 $\ge$ 60% | 🟡 55% - 59% | 🔴 < 55%</span>
                    <span>|</span>
                    <span><b>Leyenda PV2:</b> 🟢 > 55% | 🟡 46% - 54% | 🔴 < 45%</span>
                </div>
            """, unsafe_allow_html=True)

            st.dataframe(tabla_estilizada, use_container_width=True, height=550)

        else:
            st.warning("No se encontraron productos que coincidan con los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error al cargar el Control de Márgenes: {e}")

# ------------------------------------------
# MODO 3: SIMULACIÓN FINANCIERA MULTINIVEL
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
# MODO 4: EXPLORADOR DE TABLAS
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
