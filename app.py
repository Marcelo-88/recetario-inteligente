import re
import pandas as pd
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin | Ficha Técnica N3",
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

    /* Estilo para tablas de Streamlit */
    div[data-testid="stTable"] table, div[data-testid="stDataFrame"] {
        border-radius: 8px !important;
        overflow: hidden;
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
        <h1>Fridolin • Ficha Técnica de Producto Terminado (N3)</h1>
        <p>Consulta de Estructura de Receta, Precios, Márgenes y Sub-Recetas N2/N1</p>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 3. CARGA DE DATOS Y FUNCIONES AUXILIARES
# ==========================================
ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=15)
def cargar_pestana(nombre_pestana):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
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


def obtener_precios_y_costo_n3(row_n3):
    costo = 0.0
    pv1, pv2, pv3 = 0.0, 0.0, 0.0

    for col in row_n3.index:
        col_u = str(col).upper().strip()
        val_num = extraer_num(row_n3[col])

        if "COSTO" in col_u and costo == 0.0:
            costo = val_num
        elif ("PRECIO 1" in col_u or "PV1" in col_u or col_u == "PRECIO DE VENTA 1") and pv1 == 0.0:
            pv1 = val_num
        elif ("PRECIO 2" in col_u or "PV2" in col_u or col_u == "PRECIO DE VENTA 2") and pv2 == 0.0:
            pv2 = val_num
        elif ("PRECIO 3" in col_u or "PV3" in col_u or col_u == "PRECIO DE VENTA 3") and pv3 == 0.0:
            pv3 = val_num

    return costo, pv1, pv2, pv3


# ==========================================
# 4. EXTRACCIÓN DE COMPONENTES DE RECETA
# ==========================================
def extraer_componentes_por_columnas(filas_receta):
    """Extrae bloques de Materia Prima, N1 y N2 corrigiendo los índices de columna."""
    mp_list = []
    n1_list = []
    n2_list = []

    for _, row in filas_receta.iterrows():
        # --- MATERIA PRIMA DIRECTA ---
        # Col 1: Nombre, Col 2: Codigo ERP, Col 3: Cantidad, Col 4: Unidad
        if len(row) > 1 and str(row.iloc[1]).strip() not in ["", "-", "NADA", "nan", "MATERIA PRIMA"]:
            nom_mp = str(row.iloc[1]).strip()
            cod_mp = limpiar_cod_mostrar(row.iloc[2]) if len(row) > 2 else ""
            cant_mp = extraer_num(row.iloc[3]) if len(row) > 3 else 0.0
            unid_mp = str(row.iloc[4]).strip() if len(row) > 4 and str(row.iloc[4]).strip() not in ["", "-", "nan", "None"] else "-"

            if nom_mp.upper() != "MATERIA PRIMA / INSUMO":
                mp_list.append({
                    "Código ERP": cod_mp if cod_mp else "-",
                    "Nombre del Insumo": nom_mp,
                    "Cantidad": f"{cant_mp:.4f}",
                    "Unidad": unid_mp
                })

        # --- RECETAS N1 ---
        if len(row) > 5 and str(row.iloc[5]).strip() not in ["", "-", "NADA", "nan", "RECETAS N1"]:
            nom_n1 = str(row.iloc[5]).strip()
            cod_n1 = limpiar_cod_mostrar(row.iloc[6]) if len(row) > 6 else ""
            cant_n1 = extraer_num(row.iloc[7]) if len(row) > 7 else 0.0
            unid_n1 = str(row.iloc[8]).strip() if len(row) > 8 and str(row.iloc[8]).strip() not in ["", "-", "nan"] else "Kg"

            n1_list.append({
                "codigo": cod_n1 if cod_n1 else normalizar_cod(nom_n1),
                "nombre": nom_n1,
                "cantidad": cant_n1,
                "unidad": unid_n1
            })

        # --- RECETAS N2 ---
        if len(row) > 9 and str(row.iloc[9]).strip() not in ["", "-", "NADA", "nan", "RECETAS N2"]:
            nom_n2 = str(row.iloc[9]).strip()
            cod_n2 = limpiar_cod_mostrar(row.iloc[10]) if len(row) > 10 else ""
            cant_n2 = extraer_num(row.iloc[11]) if len(row) > 11 else 0.0
            unid_n2 = str(row.iloc[12]).strip() if len(row) > 12 and str(row.iloc[12]).strip() not in ["", "-", "nan"] else "Kg"

            n2_list.append({
                "codigo": cod_n2 if cod_n2 else normalizar_cod(nom_n2),
                "nombre": nom_n2,
                "cantidad": cant_n2,
                "unidad": unid_n2
            })

    return mp_list, n1_list, n2_list


def extraer_tabla_receta_n2_directa(filas_n2):
    """
    Extrae componentes de una sub-receta N2 mapeando correctamente las columnas de Google Sheets
    evitando que el nombre se traslape con la columna de código o cantidad.
    """
    componentes = []
    for _, row in filas_n2.iterrows():
        if len(row) > 1:
            val_col1 = str(row.iloc[1]).strip()
            
            # Omitir filas vacías o encabezados de la hoja
            if val_col1 in ["", "-", "NADA", "nan", "MATERIA PRIMA", "Nombre del Insumo"]:
                continue

            # Mapeo posicional corregido de la pestaña Recetas_N2:
            # Col 1 -> Nombre Insumo
            # Col 2 -> Código ERP Insumo (o Código Receta si es relación)
            # Col 3 -> Cantidad
            # Col 4 -> Unidad
            nombre = val_col1
            codigo = limpiar_cod_mostrar(row.iloc[2]) if len(row) > 2 else ""
            cantidad = extraer_num(row.iloc[3]) if len(row) > 3 else 0.0
            unidad = str(row.iloc[4]).strip() if len(row) > 4 and str(row.iloc[4]).strip() not in ["", "-", "nan", "None"] else "-"

            componentes.append({
                "Código ERP": codigo if codigo else "-",
                "Nombre del Insumo / Componente": nombre,
                "Cantidad": f"{cantidad:.4f}",
                "Unidad": unidad
            })
            
    return componentes


# ==========================================
# 5. VISTA DE FICHA TÉCNICA PRINCIPAL
# ==========================================
try:
    df_lista_n3 = cargar_pestana("Lista_N3")
    df_recetas_n3 = cargar_pestana("Recetas_N3")
    df_recetas_n2 = cargar_pestana("Recetas_N2")
    df_recetas_n1 = cargar_pestana("Recetas_N1")

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

        # --- TARJETAS DE MÉTRICAS Y MÁRGENES ---
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

        # --- ESTRUCTURA DE LA RECETA ---
        st.markdown("##### 📦 Estructura de Componentes de la Receta")

        filas_r3 = df_recetas_n3[
            df_recetas_n3.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nombre_p)
        ]
        if filas_r3.empty and len(codigo_p) > 2:
            filas_r3 = df_recetas_n3[
                df_recetas_n3.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(codigo_p)
            ]

        if not filas_r3.empty:
            materia_prima_list, recetas_n1_list, recetas_n2_list = extraer_componentes_por_columnas(filas_r3)

            # 1. MATERIA PRIMA DIRECTA
            with st.expander(f"🔹 **Materia Prima Directa** ({len(materia_prima_list)} insumos)", expanded=True):
                if materia_prima_list:
                    df_mp = pd.DataFrame(materia_prima_list)
                    st.dataframe(df_mp, use_container_width=True, hide_index=True)
                else:
                    st.write("No contiene materia prima directa asignada.")

            # 2. RECETAS N1 (SUB-RECETAS BASE)
            if recetas_n1_list:
                st.markdown("##### 🔴 Sub-Recetas N1 (Bases)")
                for item_n1 in recetas_n1_list:
                    cod_n1 = item_n1["codigo"]
                    nom_n1 = item_n1["nombre"]
                    cant_n1 = item_n1["cantidad"]
                    unid_n1 = item_n1["unidad"]

                    with st.expander(f"🔴 **[{cod_n1}] {nom_n1}** — {cant_n1:.4f} {unid_n1}"):
                        filas_sub_n1 = df_recetas_n1[
                            (df_recetas_n1.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(nom_n1))
                            | (df_recetas_n1.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nom_n1))
                        ]
                        if not filas_sub_n1.empty:
                            mp_n1, _, _ = extraer_componentes_por_columnas(filas_sub_n1)
                            if mp_n1:
                                df_sub_n1 = pd.DataFrame(mp_n1)
                                st.dataframe(df_sub_n1, use_container_width=True, hide_index=True)
                            else:
                                st.write("Sin componentes registrados.")
                        else:
                            st.write("Detalle no encontrado en la hoja Recetas_N1.")

            # 3. RECETAS N2 (INTERMEDIOS / RELLENOS) DESGLOSABLES
            if recetas_n2_list:
                st.markdown("##### 🟠 Recetas N2 (Intermedios / Rellenos)")
                for item_n2 in recetas_n2_list:
                    cod_n2 = item_n2["codigo"]
                    nom_n2 = item_n2["nombre"]
                    cant_n2 = item_n2["cantidad"]
                    unid_n2 = item_n2["unidad"]

                    with st.expander(f"🟠 **[{cod_n2}] {nom_n2}** — {cant_n2:.4f} {unid_n2}", expanded=False):
                        # Búsqueda exacta de las filas del N2 en la pestaña Recetas_N2
                        filas_sub_n2 = df_recetas_n2[
                            (df_recetas_n2.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(cod_n2))
                            | (df_recetas_n2.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(nom_n2))
                            | (df_recetas_n2.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nom_n2))
                        ]
                        
                        if not filas_sub_n2.empty:
                            comp_n2 = extraer_tabla_receta_n2_directa(filas_sub_n2)
                            if comp_n2:
                                df_comp_n2 = pd.DataFrame(comp_n2)
                                # Se renderiza la tabla alineada sin índice
                                st.dataframe(df_comp_n2, use_container_width=True, hide_index=True)
                            else:
                                st.info("No se hallaron componentes para esta receta en Recetas_N2.")
                        else:
                            st.warning(f"No se encontró el detalle del código [{cod_n2}] en la hoja Recetas_N2.")

        else:
            st.warning("No se encontró el desglose de este producto en la hoja Recetas_N3.")

except Exception as e:
    st.error(f"Error al cargar la Ficha Técnica: {e}")
