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

    .st-emotion-cache-p5msec, .streamlit-expanderHeader {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
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
# 3. CARGA Y FUNCIONES AUXILIARES DE DATOS
# ==========================================
ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df.fillna("")


def normalizar_cod(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return re.sub(r"[^A-Za-z0-9]", "", v).upper()


def limpiar_texto_comparar(val):
    if pd.isna(val):
        return ""
    v = str(val).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", v)


def limpiar_cod_mostrar(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return v.upper()


def extraer_num(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA", "No Aplica"]:
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def normalizar_texto(val):
    if pd.isna(val):
        return ""
    return str(val).strip()


def buscar_columna_mermas(df_mermas):
    patrones = ["COSTO C/RENDIMIENTO", "COSTO C/ RENDIMIENTO", "RENDIMIENTO"]
    for col in df_mermas.columns:
        col_clean = str(col).strip().upper()
        for pat in patrones:
            if pat in col_clean:
                return col
    if len(df_mermas.columns) >= 8:
        return df_mermas.columns[7]
    return df_mermas.columns[-1]


def buscar_columna_costo_master(df, nivel="3"):
    for col in df.columns:
        c_u = str(col).strip().upper()
        if "COSTO POR KILO" in c_u or "COSTO POR UNIDAD" in c_u:
            return col

    patron = f"COSTO R{nivel}"
    for col in df.columns:
        if patron in str(col).strip().upper():
            return col

    for col in df.columns:
        c_u = str(col).upper()
        if "COSTO" in c_u and "TOTAL" not in c_u:
            return col

    return df.columns[-1] if len(df.columns) > 0 else ""


def buscar_valor_columna(df_row, lista_palabras_clave):
    for col in df_row.index:
        col_upper = str(col).strip().upper()
        if any(clave.upper() in col_upper for clave in lista_palabras_clave):
            val = df_row[col]
            num = extraer_num(val)
            if num > 0 or str(val).strip() in ["0", "0.0", "0,0"]:
                return num
    return 0.0


def obtener_rendimiento_total_batch(row_values):
    cantidades = []
    for val in row_values[1:]:
        num = extraer_num(val)
        if num > 0:
            cantidades.append(num)
    total = sum(cantidades)
    return total if total > 0 else 1.0


def obtener_precios_y_costo_n3(row_n3):
    costo = 0.0
    pv1, pv2, pv3 = 0.0, 0.0, 0.0

    for col in row_n3.index:
        col_u = str(col).upper().strip()
        val_num = extraer_num(row_n3[col])

        if "COSTO" in col_u and costo == 0.0:
            costo = val_num
        elif ("PRECIO 1" in col_u or "PV1" in col_u or col_u == "PRECIO DE VENTA 1" or "P. VENTA 1" in col_u) and pv1 == 0.0:
            pv1 = val_num
        elif ("PRECIO 2" in col_u or "PV2" in col_u or col_u == "PRECIO DE VENTA 2" or "P. VENTA 2" in col_u) and pv2 == 0.0:
            pv2 = val_num
        elif ("PRECIO 3" in col_u or "PV3" in col_u or col_u == "PRECIO DE VENTA 3" or "P. VENTA 3" in col_u) and pv3 == 0.0:
            pv3 = val_num

    if pv1 == 0.0 and len(row_n3) > 3:
        for val in row_n3.values[2:]:
            n = extraer_num(val)
            if n > costo and pv1 == 0.0:
                pv1 = n
            elif n > costo and pv2 == 0.0:
                pv2 = n
            elif n > costo and pv3 == 0.0:
                pv3 = n

    return costo, pv1, pv2, pv3


# 🔥 FUNCIÓN CORREGIDA PARA EXTRAER LIMPIAMENTE LOS INGREDIENTES 🔥
def extraer_componentes_receta(fila_receta):
    vals = [str(v).strip() for v in fila_receta.values]
    componentes = []
    if len(vals) <= 1:
        return componentes

    i = 1
    while i < len(vals):
        nom = vals[i]
        
        # 1. Ignorar celdas vacías o encabezados que se hayan colado en la tabla
        if not nom or nom.upper() in ["", "-", "NAN", "NO SE ENCONTRO", "NADA", "INGREDIENTE", "INSUMO", "CANTIDAD", "UNIDAD", "KG", "LTS"]:
            i += 1
            continue
            
        # 2. Ignorar si la celda es un valor monetario o puramente numérico (desfase)
        if re.match(r"^BS\.?\s*\d+", nom, re.IGNORECASE) or nom.replace(".", "", 1).replace(",", "", 1).isdigit():
            i += 1
            continue
            
        # 3. Componente válido detectado
        cant = 0.0
        unid = "Kg/U"
        
        # Buscar cantidad en la celda adyacente (i+1)
        if i + 1 < len(vals):
            cant = extraer_num(vals[i + 1])
            
        # Buscar unidad en la celda subsiguiente (i+2)
        if i + 2 < len(vals):
            unid_val = vals[i + 2]
            # Solo la tomamos si no es un número (evita otro desfase)
            if unid_val and not unid_val.replace('.', '', 1).replace(',', '', 1).isdigit() and len(unid_val) <= 12:
                unid = unid_val
        
        componentes.append({
            "componente": nom,
            "cantidad": cant,
            "unidad": unid
        })
        
        # Avanzar estrictamente de 3 en 3 (Estructura: Insumo | Cantidad | Unidad)
        i += 3
        
    return componentes


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
        df_lista_n3 = cargar_pestaña("Lista_N3")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_mermas = cargar_pestaña("Mermas_Costos")

        col_nom_n3 = df_lista_n3.columns[0]
        col_cod_n3 = df_lista_n3.columns[1] if len(df_lista_n3.columns) > 1 else col_nom_n3

        df_lista_n3["COD_RAW"] = df_lista_n3[col_cod_n3].apply(limpiar_cod_mostrar)
        df_lista_n3["COMBO_LABEL"] = (
            "[" + df_lista_n3["COD_RAW"] + "] " + df_lista_n3[col_nom_n3].astype(str).str.strip()
        )

        opciones_n3 = sorted([op for op in df_lista_n3["COMBO_LABEL"].unique() if len(op) > 4])
        prod_seleccionado = st.selectbox("🔍 Selecciona un Producto Terminado (N3):", opciones_n3)

        if prod_seleccionado:
            fila_master = df_lista_n3[df_lista_n3["COMBO_LABEL"] == prod_seleccionado].iloc[0]

            codigo_p = fila_master["COD_RAW"]
            nombre_p = str(fila_master[col_nom_n3]).strip()

            costo_r3, pv1, pv2, pv3 = obtener_precios_y_costo_n3(fila_master)

            st.divider()
            st.markdown(f"### 🎂 {nombre_p} <small style='color:#777;'>(Código ERP: {codigo_p})</small>", unsafe_allow_html=True)

            # --- MÉTRICAS ---
            st.markdown("##### 💵 Análisis de Costo & Márgenes")
            m1, m2, m3, m4 = st.columns(4)

            with m1:
                st.metric("Costo R3 (Producción)", f"Bs {costo_r3:.2f}")

            with m2:
                if pv1 > 0:
                    margen1 = ((pv1 - costo_r3) / pv1 * 100) if pv1 > 0 else 0
                    st.metric("Precio Venta 1", f"Bs {pv1:.2f}", delta=f"{margen1:.1f}% Margen")
                else:
                    st.metric("Precio Venta 1", "No Aplica")

            with m3:
                if pv2 > 0:
                    margen2 = ((pv2 - costo_r3) / pv2 * 100) if pv2 > 0 else 0
                    st.metric("Precio Venta 2", f"Bs {pv2:.2f}", delta=f"{margen2:.1f}% Margen")
                else:
                    st.metric("Precio Venta 2", "No Aplica")

            with m4:
                if pv3 > 0:
                    margen3 = ((pv3 - costo_r3) / pv3 * 100) if pv3 > 0 else 0
                    st.metric("Precio Venta 3", f"Bs {pv3:.2f}", delta=f"{margen3:.1f}% Margen")
                else:
                    st.metric("Precio Venta 3", "No Aplica")

            st.divider()

            # --- ESTRUCTURA MULTINIVEL ---
            st.markdown("##### 🌳 Estructura Multinivel Desglosada")

            match_r3 = df_recetas_n3[
                df_recetas_n3.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nombre_p)
            ]
            if match_r3.empty and len(codigo_p) > 2:
                match_r3 = df_recetas_n3[
                    df_recetas_n3.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(codigo_p)
                ]

            if not match_r3.empty:
                comp_n3 = extraer_componentes_receta(match_r3.iloc[0])

                materia_prima_list = []
                recetas_n1_list = []
                recetas_n2_list = []

                for comp in comp_n3:
                    nombre_c = comp["componente"]
                    cant_c = comp["cantidad"]
                    unid_c = comp["unidad"]

                    norm_c = normalizar_cod(nombre_c)
                    fuzzy_c = limpiar_texto_comparar(nombre_c)

                    match_sub_n2 = df_recetas_n2[
                        (df_recetas_n2.iloc[:, 0].apply(normalizar_cod) == norm_c)
                        | (df_recetas_n2.iloc[:, 0].apply(limpiar_texto_comparar) == fuzzy_c)
                    ]

                    match_sub_n1 = df_recetas_n1[
                        (df_recetas_n1.iloc[:, 0].apply(normalizar_cod) == norm_c)
                        | (df_recetas_n1.iloc[:, 0].apply(limpiar_texto_comparar) == fuzzy_c)
                    ]

                    if not match_sub_n2.empty:
                        recetas_n2_list.append((nombre_c, cant_c, unid_c, match_sub_n2.iloc[0]))
                    elif not match_sub_n1.empty:
                        recetas_n1_list.append((nombre_c, cant_c, unid_c, match_sub_n1.iloc[0]))
                    else:
                        match_mp = df_mermas[
                            (df_mermas.iloc[:, 0].apply(limpiar_texto_comparar) == fuzzy_c)
                            | (df_mermas.iloc[:, 1].apply(normalizar_cod) == norm_c)
                        ]
                        cod_mp = limpiar_cod_mostrar(match_mp.iloc[0, 1]) if not match_mp.empty else norm_c
                        materia_prima_list.append((cod_mp, nombre_c, f"{cant_c:.4f}", unid_c))

                with st.expander(f"🔹 **Materia Prima Directa** ({len(materia_prima_list)} insumos)", expanded=True):
                    if materia_prima_list:
                        df_mp = pd.DataFrame(materia_prima_list, columns=["Código ERP", "Nombre del Insumo", "Cantidad", "Unidad"])
                        st.dataframe(df_mp, use_container_width=True, hide_index=True)
                    else:
                        st.write("No contiene Materia Prima directa.")

                if recetas_n1_list:
                    st.markdown("##### 🔴 Recetas N1 (Sub-Recetas Base)")
                    for nom_n1, cant_n1, unid_n1, fila_n1 in recetas_n1_list:
                        cod_n1 = normalizar_cod(nom_n1)
                        # Formato limpio para que no queden números sueltos en el título
                        with st.expander(f"🔴 **[{cod_n1}] {nom_n1}** — {cant_n1:.4f} {unid_n1}"):
                            st.caption("Composición interna de esta Sub-Receta N1:")
                            sub_comps = extraer_componentes_receta(fila_n1)
                            if sub_comps:
                                df_sub = pd.DataFrame(sub_comps)
                                df_sub.columns = ["Componente / Insumo", "Cantidad", "Unidad"]
                                df_sub["Cantidad"] = df_sub["Cantidad"].apply(lambda x: f"{x:.4f}")
                                st.dataframe(df_sub, use_container_width=True, hide_index=True)
                            else:
                                st.write("Sin detalle registrado.")

                if recetas_n2_list:
                    st.markdown("##### 🟠 Recetas N2 (Intermedios / Rellenos)")
                    for nom_n2, cant_n2, unid_n2, fila_n2 in recetas_n2_list:
                        cod_n2 = normalizar_cod(nom_n2)
                        with st.expander(f"🟠 **[{cod_n2}] {nom_n2}** — {cant_n2:.4f} {unid_n2}"):
                            st.caption("Composición interna de esta Receta N2:")
                            sub_comps_n2 = extraer_componentes_receta(fila_n2)

                            if sub_comps_n2:
                                for sub_c in sub_comps_n2:
                                    s_nom = sub_c["componente"]
                                    s_cant = sub_c["cantidad"]
                                    s_unid = sub_c["unidad"]
                                    s_norm = normalizar_cod(s_nom)

                                    match_inner_n1 = df_recetas_n1[
                                        (df_recetas_n1.iloc[:, 0].apply(normalizar_cod) == s_norm)
                                        | (df_recetas_n1.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(s_nom))
                                    ]

                                    if not match_inner_n1.empty:
                                        with st.expander(f"🔴 **[N1 interna] [{s_norm}] {s_nom}** — {s_cant:.4f} {s_unid}"):
                                            inner_comps = extraer_componentes_receta(match_inner_n1.iloc[0])
                                            df_inner = pd.DataFrame(inner_comps)
                                            df_inner.columns = ["Componente / Insumo", "Cantidad", "Unidad"]
                                            df_inner["Cantidad"] = df_inner["Cantidad"].apply(lambda x: f"{x:.4f}")
                                            st.dataframe(df_inner, use_container_width=True, hide_index=True)
                                    else:
                                        st.markdown(f"• **[{s_norm}] {s_nom}** — {s_cant:.4f} {s_unid}")
                            else:
                                st.write("Sin detalle registrado.")

            else:
                st.warning("No se encontró el desglose de esta receta en Recetas_N3.")

    except Exception as e:
        st.error(f"Error al generar la Ficha Técnica: {e}")

# ------------------------------------------
# MODO 2: CONTROL DE MÁRGENES Y ESTADOS (N3)
# ------------------------------------------
elif modo_app == "📊 Control de Márgenes y Estados (N3)":
    st.markdown("## 📊 Tablero de Control de Márgenes por Estado")
    st.caption("Visualiza de forma rápida qué productos están dentro o fuera del objetivo de rentabilidad.")

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
# MODO 3: SIMULACIÓN FINANCIERA MULTINIVEL
# ------------------------------------------
elif modo_app == "🍰 Simulación Financiera Multinivel":
    st.markdown("## 🍰 Simulación Financiera Proporcional")
    st.caption("Simula el impacto de variaciones de precio en materia prima sobre N1, N2 y N3.")

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Lista_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        col_nom_m = df_mermas.columns[0]
        col_cod_m = df_mermas.columns[1] if len(df_mermas.columns) > 1 else col_nom_m
        col_costo_m = buscar_columna_mermas(df_mermas)

        df_mermas["COD_RAW"] = df_mermas[col_cod_m].apply(limpiar_cod_mostrar)
        df_mermas["COD_NORM"] = df_mermas[col_cod_m].apply(normalizar_cod)

        df_mermas_validos = df_mermas[df_mermas["COD_NORM"] != ""].copy()
        df_mermas_validos["COMBO_LABEL"] = (
            "[" + df_mermas_validos["COD_RAW"] + "] " + df_mermas_validos[col_nom_m].astype(str).str.strip()
        )

        lista_opciones = sorted(df_mermas_validos["COMBO_LABEL"].unique().tolist())

        st.subheader("1️⃣ Selecciona el Insumo a Simular")
        opcion_elegida = st.selectbox("Buscar por Código ERP o Nombre de Insumo:", lista_opciones)

        if opcion_elegida:
            datos_insumo = df_mermas_validos[df_mermas_validos["COMBO_LABEL"] == opcion_elegida].iloc[0]

            codigo_target_norm = datos_insumo["COD_NORM"]
            codigo_target_raw = datos_insumo["COD_RAW"]
            articulo_mostrar = str(datos_insumo[col_nom_m]).strip()

            costo_actual_unitario = extraer_num(datos_insumo[col_costo_m])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Código Insumo ERP", f"[{codigo_target_raw}]")
                st.caption(f"**Nombre:** {articulo_mostrar}")
            with c2:
                nuevo_precio_unitario = st.number_input(
                    "Nuevo precio simulado por Lt/Kg (Bs):",
                    min_value=0.0,
                    value=float(costo_actual_unitario + 1.00) if costo_actual_unitario > 0 else 20.0,
                    step=0.10,
                )
            with c3:
                dif_precio_unitario = nuevo_precio_unitario - costo_actual_unitario
                porc_inc = (
                    (dif_precio_unitario / costo_actual_unitario * 100) if costo_actual_unitario > 0 else 0.0
                )
                st.metric("Variación Directa", f"+Bs {dif_precio_unitario:.2f}", delta=f"{porc_inc:.1f}%")

            st.caption(f"📌 Costo Base Actual en Mermas: **Bs {costo_actual_unitario:.2f}**")
            st.divider()

            def consultar_master_gen(df_lista, busqueda_str, nivel="3"):
                if df_lista.empty:
                    return 0.0, "-", str(busqueda_str).strip()

                col_nom = df_lista.columns[0]
                col_cod = df_lista.columns[1] if len(df_lista.columns) > 1 else col_nom
                col_costo = buscar_columna_costo_master(df_lista, nivel)

                query_norm = normalizar_cod(busqueda_str)
                query_fuzzy = limpiar_texto_comparar(busqueda_str)

                match = df_lista[
                    (df_lista[col_cod].apply(normalizar_cod) == query_norm)
                    | (df_lista[col_nom].apply(limpiar_texto_comparar) == query_fuzzy)
                    | (df_lista[col_cod].apply(limpiar_texto_comparar) == query_fuzzy)
                ]

                if match.empty and len(query_fuzzy) > 3:
                    match = df_lista[
                        df_lista[col_nom].apply(limpiar_texto_comparar).str.contains(query_fuzzy, regex=False)
                        | df_lista[col_cod].apply(limpiar_texto_comparar).str.contains(query_fuzzy, regex=False)
                    ]

                if not match.empty:
                    fila = match.iloc[0]
                    c_base = extraer_num(fila[col_costo])

                    c_show = limpiar_cod_mostrar(fila[col_cod])
                    n_show = str(fila[col_nom]).strip()
                    return c_base, c_show, n_show

                return 0.0, "-", str(busqueda_str).strip()

            # --- RECETAS N1 ---
            impactos_n1_kilo = {}
            for _, row in df_recetas_n1.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue
                receta_padre_key = vals[0]

                row_norms = [normalizar_cod(v) for v in vals]
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant_aceite = 0.0
                    for k in range(idx + 1, len(vals)):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant_aceite = num
                            break

                    inc_batch = cant_aceite * dif_precio_unitario
                    rendimiento_batch = obtener_rendimiento_total_batch(vals)
                    var_por_kilo = inc_batch / rendimiento_batch
                    impactos_n1_kilo[receta_padre_key] = impactos_n1_kilo.get(receta_padre_key, 0.0) + var_por_kilo

            filas_n1 = []
            for key_n1, var_kilo in impactos_n1_kilo.items():
                costo_base_kg, cod_show, nom_show = consultar_master_gen(df_lista_n1, key_n1, "1")
                costo_sim_kg = costo_base_kg + var_kilo
                porc_var = (var_kilo / costo_base_kg * 100) if costo_base_kg > 0 else 0.0
                filas_n1.append({
                    "Código N1": cod_show,
                    "Nombre Sub-Receta": nom_show,
                    "Costo Actual / Kg": f"Bs {costo_base_kg:.2f}",
                    "Costo Simulado / Kg": f"Bs {costo_sim_kg:.2f}",
                    "Variación / Kg (Bs)": f"+Bs {var_kilo:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- RECETAS N2 ---
            impactos_n2_kilo = {}
            for _, row in df_recetas_n2.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue

                receta_padre_key = vals[0]
                row_norms = [normalizar_cod(v) for v in vals]
                inc_batch_n2 = 0.0

                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, len(vals)):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_batch_n2 += cant * dif_precio_unitario

                for key_n1, var_kilo_n1 in impactos_n1_kilo.items():
                    norm_n1 = normalizar_cod(key_n1)
                    fuzzy_n1 = limpiar_texto_comparar(key_n1)
                    row_fuzzies = [limpiar_texto_comparar(v) for v in vals]

                    if (norm_n1 and norm_n1 in row_norms[1:]) or (fuzzy_n1 and fuzzy_n1 in row_fuzzies[1:]):
                        idx = (
                            row_norms[1:].index(norm_n1) + 1
                            if (norm_n1 and norm_n1 in row_norms[1:])
                            else row_fuzzies[1:].index(fuzzy_n1) + 1
                        )
                        cant_n1 = 0.0
                        for k in range(idx + 1, len(vals)):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant_n1 = num
                                break
                        inc_batch_n2 += cant_n1 * var_kilo_n1

                if inc_batch_n2 > 0:
                    rendimiento_batch_n2 = obtener_rendimiento_total_batch(vals)
                    var_por_kilo_n2 = inc_batch_n2 / rendimiento_batch_n2
                    impactos_n2_kilo[receta_padre_key] = (
                        impactos_n2_kilo.get(receta_padre_key, 0.0) + var_por_kilo_n2
                    )

            filas_n2 = []
            for key_n2, var_kilo in impactos_n2_kilo.items():
                costo_base_kg, cod_show, nom_show = consultar_master_gen(df_lista_n2, key_n2, "2")
                costo_sim_kg = costo_base_kg + var_kilo
                porc_var = (var_kilo / costo_base_kg * 100) if costo_base_kg > 0 else 0.0
                filas_n2.append({
                    "Código N2": cod_show,
                    "Nombre Intermedio": nom_show,
                    "Costo Actual / Kg": f"Bs {costo_base_kg:.2f}",
                    "Costo Simulado / Kg": f"Bs {costo_sim_kg:.2f}",
                    "Variación / Kg (Bs)": f"+Bs {var_kilo:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- RECETAS N3 ---
            impactos_n3 = {}
            for _, row in df_recetas_n3.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue
                nombre_o_cod_n3 = vals[0]
                row_norms = [normalizar_cod(v) for v in vals]
                row_fuzzies = [limpiar_texto_comparar(v) for v in vals]
                inc_producto_final = 0.0

                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, len(vals)):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_producto_final += cant * dif_precio_unitario

                for key_n1, var_kilo_n1 in impactos_n1_kilo.items():
                    norm_n1 = normalizar_cod(key_n1)
                    fuzzy_n1 = limpiar_texto_comparar(key_n1)
                    if (norm_n1 and norm_n1 in row_norms[1:]) or (fuzzy_n1 and fuzzy_n1 in row_fuzzies[1:]):
                        idx = (
                            row_norms[1:].index(norm_n1) + 1
                            if (norm_n1 and norm_n1 in row_norms[1:])
                            else row_fuzzies[1:].index(fuzzy_n1) + 1
                        )
                        cant_n1 = 0.0
                        for k in range(idx + 1, len(vals)):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant_n1 = num
                                break
                        inc_producto_final += cant_n1 * var_kilo_n1

                for key_n2, var_kilo_n2 in impactos_n2_kilo.items():
                    norm_n2 = normalizar_cod(key_n2)
                    fuzzy_n2 = limpiar_texto_comparar(key_n2)
                    if (norm_n2 and norm_n2 in row_norms[1:]) or (fuzzy_n2 and fuzzy_n2 in row_fuzzies[1:]):
                        idx = (
                            row_norms[1:].index(norm_n2) + 1
                            if (norm_n2 and norm_n2 in row_norms[1:])
                            else row_fuzzies[1:].index(fuzzy_n2) + 1
                        )
                        cant_n2 = 0.0
                        for k in range(idx + 1, len(vals)):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant_n2 = num
                                break
                        inc_producto_final += cant_n2 * var_kilo_n2

                if inc_producto_final > 0:
                    impactos_n3[nombre_o_cod_n3] = impactos_n3.get(nombre_o_cod_n3, 0.0) + inc_producto_final

            filas_n3 = []
            for nom_o_cod, inc_total in impactos_n3.items():
                costo_base, cod_show, nom_show = consultar_master_gen(df_lista_n3, nom_o_cod, "3")
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0
                filas_n3.append({
                    "Código Producto N3": cod_show,
                    "Nombre Producto Final": nom_show,
                    "Costo Actual (R3)": f"Bs {costo_base:.2f}",
                    "Costo Simulado": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            resumen_l1 = pd.DataFrame(filas_n1)
            resumen_l2 = pd.DataFrame(filas_n2)
            resumen_l3 = pd.DataFrame(filas_n3)

            st.subheader(f"📊 Resultados Simulación: [{codigo_target_raw}] - {articulo_mostrar}")

            t3, t2, t1 = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Lista_N2)",
                    "🔴 Sub-Recetas Base (Lista_N1)",
                ]
            )

            with t3:
                st.write(f"**Productos Finales N3 Afectados:** {len(resumen_l3)}")
                if not resumen_l3.empty:
                    st.dataframe(resumen_l3, use_container_width=True)
                else:
                    st.info("Sin productos finales N3 afectados.")

            with t2:
                st.write(f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}")
                if not resumen_l2.empty:
                    st.dataframe(resumen_l2, use_container_width=True)
                else:
                    st.info("Sin registros N2 afectados.")

            with t1:
                st.write(f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}")
                if not resumen_l1.empty:
                    st.dataframe(resumen_l1, use_container_width=True)
                else:
                    st.info("Sin registros N1 que usen este insumo.")

    except Exception as e:
        st.error(f"Error en simulación: {e}")

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
        st.error(f"Error al cargar {pestaña_activa}: {e}")
