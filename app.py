import re
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS FRIDOLIN
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
        <h1>Fridolin • Centro de Control & Simulación Financiera</h1>
        <p>Gestión Inteligente de Recetas • Análisis de Impacto Financiero</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. CARGA Y LIMPIEZA DE DATOS
# ==========================================
ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"

@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
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
        "🍰 Simulación Financiera Multinivel",
        "📋 Ficha Técnica de Producto (N3)",
        "📊 Control de Márgenes y Estados (N3)",
        "📖 Explorador de Tablas",
    ],
)
st.sidebar.divider()

# ------------------------------------------
# MODO 1: SIMULACIÓN FINANCIERA (LÓGICA EXACTA QUE FUNCIONABA)
# ------------------------------------------
if modo_app == "🍰 Simulación Financiera Multinivel":
    st.markdown("## 🍰 Simulación Financiera Proporcional")
    st.caption("Ajusta el precio de un insumo base para evaluar el impacto en N1, N2 y el producto final N3.")

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        col_nom_m = df_mermas.columns[0]
        col_cod_m = df_mermas.columns[1] if len(df_mermas.columns) > 1 else col_nom_m

        df_mermas["COMBO_LABEL"] = (
            "[" + df_mermas[col_cod_m].astype(str).str.strip() + "] " + df_mermas[col_nom_m].astype(str).str.strip()
        )
        lista_opciones = sorted([op for op in df_mermas["COMBO_LABEL"].unique() if len(op) > 3])

        st.subheader("1️⃣ Selecciona el Insumo a Simular")
        opcion_elegida = st.selectbox("Buscar por Código ERP o Nombre de Insumo:", lista_opciones)

        if opcion_elegida:
            datos_insumo = df_mermas[df_mermas["COMBO_LABEL"] == opcion_elegida].iloc[0]
            articulo_mostrar = normalizar_texto(datos_insumo[col_nom_m])
            codigo_target = normalizar_texto(datos_insumo[col_cod_m])

            costo_actual_unitario = buscar_valor_columna(
                datos_insumo, ["Costo", "Precio", "P.U", "Unitario", "Valor", "Costo/Lt", "Costo/Kg"]
            )
            if costo_actual_unitario == 0.0:
                for col in datos_insumo.index:
                    if col not in ["COMBO_LABEL", col_nom_m, col_cod_m]:
                        val_n = extraer_num(datos_insumo[col])
                        if val_n > 0:
                            costo_actual_unitario = val_n
                            break

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Precio Actual Base", f"Bs {costo_actual_unitario:.2f}")
                st.caption(f"**Insumo:** [{codigo_target}] {articulo_mostrar}")
            with c2:
                nuevo_precio_unitario = st.number_input(
                    "Nuevo precio simulado por Lt/Kg (Bs):",
                    min_value=0.0,
                    value=float(costo_actual_unitario),
                    step=0.50,
                )
            with c3:
                dif_precio_unitario = nuevo_precio_unitario - costo_actual_unitario
                porc_inc = ((dif_precio_unitario / costo_actual_unitario) * 100) if costo_actual_unitario > 0 else 0.0
                st.metric("Variación Directa", f"+Bs {dif_precio_unitario:.2f}", delta=f"{porc_inc:.1f}%")

            st.divider()
            st.subheader("2️⃣ Impacto Proporcional en Productos N3")

            if abs(dif_precio_unitario) < 0.001:
                st.info("💡 Modifica el **'Nuevo precio simulado'** arriba para ver el impacto en costos.")
            else:
                # Cargar todas las capas de recetas
                df_recetas_n1 = cargar_pestaña("Recetas_N1")
                df_recetas_n2 = cargar_pestaña("Recetas_N2")
                df_recetas_n3 = cargar_pestaña("Recetas_N3")
                df_lista_n3 = cargar_pestaña("Lista_N3")

                cod_target_clean = codigo_target.upper().strip()
                nom_target_clean = articulo_mostrar.upper().strip()

                def es_coincidente(cod_row, nom_row):
                    if cod_target_clean and cod_target_clean == str(cod_row).upper().strip():
                        return True
                    if nom_target_clean and nom_target_clean in str(nom_row).upper().strip():
                        return True
                    return False

                # 1. Rastrear en N1
                subrecetas_n1_afectadas = {}
                for _, r in df_recetas_n1.iterrows():
                    nom_padre = normalizar_texto(r.iloc[0])
                    nom_ins = normalizar_texto(r.iloc[1])
                    cod_ins = normalizar_texto(r.iloc[2]) if len(r) > 2 else ""
                    cant = extraer_num(r.iloc[4]) if len(r) > 4 else 0.0

                    if es_coincidente(cod_ins, nom_ins) and nom_padre and cant > 0:
                        subrecetas_n1_afectadas[nom_padre.upper()] = subrecetas_n1_afectadas.get(nom_padre.upper(), 0.0) + cant

                # 2. Rastrear en N2
                subrecetas_n2_afectadas = {}
                for _, r in df_recetas_n2.iterrows():
                    nom_padre = normalizar_texto(r.iloc[0])
                    nom_ins = normalizar_texto(r.iloc[1])
                    cod_ins = normalizar_texto(r.iloc[2]) if len(r) > 2 else ""
                    cant = extraer_num(r.iloc[4]) if len(r) > 4 else 0.0

                    # Coincidencia directa del insumo o de una subreceta N1
                    if es_coincidente(cod_ins, nom_ins):
                        subrecetas_n2_afectadas[nom_padre.upper()] = subrecetas_n2_afectadas.get(nom_padre.upper(), 0.0) + cant
                    elif nom_ins.upper() in subrecetas_n1_afectadas:
                        factor_n1 = subrecetas_n1_afectadas[nom_ins.upper()]
                        subrecetas_n2_afectadas[nom_padre.upper()] = subrecetas_n2_afectadas.get(nom_padre.upper(), 0.0) + (cant * factor_n1)

                # 3. Rastrear en N3 (Productos Terminados)
                consumo_total_n3 = {}
                for _, r in df_recetas_n3.iterrows():
                    nom_padre = normalizar_texto(r.iloc[0])
                    nom_ins = normalizar_texto(r.iloc[1])
                    cod_ins = normalizar_texto(r.iloc[2]) if len(r) > 2 else ""
                    cant = extraer_num(r.iloc[4]) if len(r) > 4 else 0.0

                    if not nom_padre or cant <= 0:
                        continue

                    # Directo insumo base
                    if es_coincidente(cod_ins, nom_ins):
                        consumo_total_n3[nom_padre] = consumo_total_n3.get(nom_padre, 0.0) + cant
                    # A través de N1
                    elif nom_ins.upper() in subrecetas_n1_afectadas:
                        factor = subrecetas_n1_afectadas[nom_ins.upper()]
                        consumo_total_n3[nom_padre] = consumo_total_n3.get(nom_padre, 0.0) + (cant * factor)
                    # A través de N2
                    elif nom_ins.upper() in subrecetas_n2_afectadas:
                        factor = subrecetas_n2_afectadas[nom_ins.upper()]
                        consumo_total_n3[nom_padre] = consumo_total_n3.get(nom_padre, 0.0) + (cant * factor)

                # 4. Construir tabla final cruzando con Lista_N3
                filas_resultado = []
                col_nom_l3 = df_lista_n3.columns[0]
                col_cod_l3 = df_lista_n3.columns[1] if len(df_lista_n3.columns) > 1 else col_nom_l3

                for _, r in df_lista_n3.iterrows():
                    nom_prod = normalizar_texto(r[col_nom_l3])
                    cod_prod = normalizar_texto(r[col_cod_l3])

                    if nom_prod in consumo_total_n3:
                        cant_usada = consumo_total_n3[nom_prod]
                        incremento_costo = cant_usada * dif_precio_unitario

                        costo_orig = buscar_valor_columna(r, ["Costo Total N3", "Costo R3", "Costo Total", "Costo"])
                        pv1 = buscar_valor_columna(r, ["Precio Venta 1", "PV1", "Precio 1"])
                        pv2 = buscar_valor_columna(r, ["Precio Venta 2", "PV2", "Precio 2"])

                        costo_simulado = costo_orig + incremento_costo

                        m1_orig = ((pv1 - costo_orig) / pv1 * 100) if pv1 > 0 else 0.0
                        m1_sim = ((pv1 - costo_simulado) / pv1 * 100) if pv1 > 0 else 0.0

                        m2_orig = ((pv2 - costo_orig) / pv2 * 100) if pv2 > 0 else 0.0
                        m2_sim = ((pv2 - costo_simulado) / pv2 * 100) if pv2 > 0 else 0.0

                        filas_resultado.append({
                            "Código ERP": cod_prod,
                            "Producto Terminado (N3)": nom_prod,
                            "Cant. Insumo Base": cant_usada,
                            "Costo Orig. (Bs)": costo_orig,
                            "Costo Simul. (Bs)": costo_simulado,
                            "Incremento (Bs)": incremento_costo,
                            "Margen PV1 (Orig)": f"{m1_orig:.1f}%",
                            "Margen PV1 (Simul)": f"{m1_sim:.1f}%",
                            "Margen PV2 (Orig)": f"{m2_orig:.1f}%",
                            "Margen PV2 (Simul)": f"{m2_sim:.1f}%",
                        })

                if filas_resultado:
                    df_res = pd.DataFrame(filas_resultado)
                    st.success(f"🎯 Se encontraron **{len(df_res)}** Productos Terminados (N3) afectados por este insumo:")
                    st.dataframe(
                        df_res.style.format({
                            "Cant. Insumo Base": "{:.3f}",
                            "Costo Orig. (Bs)": "{:.2f} Bs",
                            "Costo Simul. (Bs)": "{:.2f} Bs",
                            "Incremento (Bs)": "+{:.2f} Bs",
                        }),
                        use_container_width=True,
                        height=500,
                    )
                else:
                    st.warning("No se encontraron productos N3 que utilicen este insumo ni de forma directa ni a través de subrecetas N1/N2.")

    except Exception as e:
        st.error(f"Error en la pantalla de simulación: {e}")

# ------------------------------------------
# MODO 2: FICHA TÉCNICA DE PRODUCTO (N3)
# ------------------------------------------
elif modo_app == "📋 Ficha Técnica de Producto (N3)":
    st.markdown("## 📋 Ficha Técnica Interactiva de Producto Terminado")
    st.caption("Consulta costo, precios de venta, márgenes y la lista completa de ingredientes del producto.")

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
            st.markdown("##### 🌳 Componentes / Ingredientes de Receta")

            col_receta_padre = df_recetas_n3.columns[0]
            sub_df = df_recetas_n3[df_recetas_n3[col_receta_padre].astype(str).str.strip().str.upper() == nombre_producto.upper()]

            if sub_df.empty and len(df_recetas_n3.columns) > 2:
                sub_df = df_recetas_n3[df_recetas_n3.iloc[:, 2].astype(str).str.strip().str.upper() == codigo_producto.upper()]

            if not sub_df.empty:
                mp_rows = []
                for _, row in sub_df.iterrows():
                    nom_mp = normalizar_texto(row.iloc[1])
                    cod_mp = normalizar_texto(row.iloc[2]) if len(row) > 2 else "-"
                    cat_mp = normalizar_texto(row.iloc[3]) if len(row) > 3 else "-"
                    cant_mp = extraer_num(row.iloc[4]) if len(row) > 4 else 0.0
                    unid_mp = normalizar_texto(row.iloc[5]) if len(row) > 5 else "Kg/U"

                    if nom_mp and nom_mp not in ["NO SE ENCONTRO", "NADA", "-"]:
                        mp_rows.append({
                            "Código ERP": cod_mp if cod_mp else "-",
                            "Nombre del Insumo / Subreceta": nom_mp,
                            "Categoría": cat_mp,
                            "Cantidad": cant_mp,
                            "Unidad": unid_mp
                        })

                df_mp_final = pd.DataFrame(mp_rows).drop_duplicates()
                st.dataframe(df_mp_final, use_container_width=True)
            else:
                st.warning("No se encontraron registros detallados para este producto en 'Recetas_N3'.")

    except Exception as e:
        st.error(f"Error al procesar la Ficha Técnica: {e}")

# ------------------------------------------
# MODO 3: CONTROL DE MÁRGENES Y ESTADOS (N3)
# ------------------------------------------
elif modo_app == "📊 Control de Márgenes y Estados (N3)":
    st.markdown("## 📊 Tablero de Control de Márgenes por Estado")
    st.caption("Visualiza el semáforo de salud financiera por producto según tus objetivos de rentabilidad.")

    try:
        df_lista_n3 = cargar_pestaña("Lista_N3")

        col_estado = None
        for col in df_lista_n3.columns:
            if "ESTADO" in str(col).upper() or "STATUS" in str(col).upper():
                col_estado = col
                break

        if not col_estado:
            col_estado = df_lista_n3.columns[-1]

        estados_disponibles = sorted([str(e).strip() for e in df_lista_n3[col_estado].unique() if str(e).strip()])
        
        f1, f2 = st.columns([1, 2])
        with f1:
            estado_sel = st.multiselect("📌 Filtrar por Estado:", estados_disponibles, default=estados_disponibles)
        with f2:
            busqueda_prod = st.text_input("🔍 Buscar por Nombre o Código:")

        datos_procesados = []
        for _, row in df_lista_n3.iterrows():
            est_val = str(row[col_estado]).strip()
            
            if estado_sel and est_val not in estado_sel:
                continue

            nombre = normalizar_texto(row.iloc[0])
            codigo = normalizar_texto(row.iloc[1]) if len(row) > 1 else "-"
            
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

            def colorear_pv1(val):
                if val <= 0:
                    return ""
                if val >= 60.0:
                    return "background-color: #D4EDDA; color: #155724; font-weight: bold;"
                elif 55.0 <= val <= 59.99:
                    return "background-color: #FFF3CD; color: #856404; font-weight: bold;"
                else:
                    return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"

            def colorear_pv2(val):
                if val <= 0:
                    return ""
                if val > 55.0:
                    return "background-color: #D4EDDA; color: #155724; font-weight: bold;"
                elif 46.0 <= val <= 54.99:
                    return "background-color: #FFF3CD; color: #856404; font-weight: bold;"
                else:
                    return "background-color: #F8D7DA; color: #721C24; font-weight: bold;"

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
