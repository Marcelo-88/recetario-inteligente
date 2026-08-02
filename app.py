import streamlit as st
import pandas as pd
import re

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Fridolin | Centro de Control Operativo",
    page_icon="🥐",
    layout="wide"
)

# ==========================================
# 2. FUNCIONES DE LIMPIEZA Y FORMATEO
# ==========================================
def limpiar_texto_comparar(val):
    if pd.isna(val) or val is None:
        return ""
    txt = str(val).strip().upper()
    txt = re.sub(r'\s+', ' ', txt)
    return txt

def normalizar_cod(val):
    if pd.isna(val) or val is None:
        return ""
    txt = str(val).strip().upper()
    txt = re.sub(r'^(REC-|PRODUCTO-|PRD-|REC)', '', txt)
    txt = re.sub(r'[^A-Z0-9]', '', txt)
    return txt

def limpiar_cod_mostrar(val):
    if pd.isna(val) or val is None:
        return ""
    txt = str(val).strip()
    if txt.endswith('.0'):
        txt = txt[:-2]
    return txt

def extraer_num(val):
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    txt = str(val).replace('$', '').replace('Bs', '').replace(',', '').strip()
    try:
        return float(txt)
    except:
        return 0.0

# ==========================================
# 3. EXTRAER COMPONENTES (LOGICA DE COLUMNAS EXCEL)
# ==========================================
def extraer_componentes_por_columnas(filas_receta):
    mp_list = []
    n1_list = []
    n2_list = []

    for _, row in filas_receta.iterrows():
        # --- MATERIA PRIMA DIRECTA ---
        # Col B (idx 1): Nombre MP
        # Col C (idx 2): Código ERP MP
        # Col E (idx 4): Cantidad MP
        # Col F (idx 5): Unidad MP (Toma directa sin forzar Empaque/Kg)
        if len(row) > 1 and str(row.iloc[1]).strip() not in ["", "-", "NADA", "nan"]:
            nom_mp = str(row.iloc[1]).strip()
            cod_mp = limpiar_cod_mostrar(row.iloc[2]) if len(row) > 2 else ""
            cant_mp = extraer_num(row.iloc[4]) if len(row) > 4 else 0.0
            
            unid_mp = ""
            if len(row) > 5 and str(row.iloc[5]).strip() not in ["", "-", "nan", "None"]:
                unid_mp = str(row.iloc[5]).strip()
            else:
                unid_mp = "Kg"

            if nom_mp and nom_mp.upper() != "MATERIA PRIMA":
                mp_list.append({
                    "Código ERP": cod_mp if cod_mp else "-",
                    "Nombre del Insumo": nom_mp,
                    "Cantidad": cant_mp,
                    "Unidad": unid_mp
                })

        # --- RECETAS N1 ---
        # Col G (idx 6): Nombre N1
        # Col H (idx 7): Código N1
        # Col I (idx 8): Cantidad N1
        # Col J (idx 9): Unidad N1
        if len(row) > 6 and str(row.iloc[6]).strip() not in ["", "-", "NADA", "nan"]:
            nom_n1 = str(row.iloc[6]).strip()
            cod_n1 = limpiar_cod_mostrar(row.iloc[7]) if len(row) > 7 else ""
            cant_n1 = extraer_num(row.iloc[8]) if len(row) > 8 else 0.0
            unid_n1 = str(row.iloc[9]).strip() if len(row) > 9 and str(row.iloc[9]).strip() not in ["", "-", "nan"] else "Kg"

            if nom_n1 and nom_n1.upper() != "RECETAS N1":
                n1_list.append({
                    "codigo": cod_n1 if cod_n1 else normalizar_cod(nom_n1),
                    "nombre": nom_n1,
                    "cantidad": cant_n1,
                    "unidad": unid_n1
                })

        # --- RECETAS N2 ---
        # Col K (idx 10): Nombre N2
        # Col L (idx 11): Código N2
        # Col M (idx 12): Cantidad N2
        # Col N (idx 13): Unidad N2
        if len(row) > 10 and str(row.iloc[10]).strip() not in ["", "-", "NADA", "nan"]:
            nom_n2 = str(row.iloc[10]).strip()
            cod_n2 = limpiar_cod_mostrar(row.iloc[11]) if len(row) > 11 else ""
            cant_n2 = extraer_num(row.iloc[12]) if len(row) > 12 else 0.0
            unid_n2 = str(row.iloc[13]).strip() if len(row) > 13 and str(row.iloc[13]).strip() not in ["", "-", "nan"] else "Kg"

            if nom_n2 and nom_n2.upper() != "RECETAS N2":
                n2_list.append({
                    "codigo": cod_n2 if cod_n2 else normalizar_cod(nom_n2),
                    "nombre": nom_n2,
                    "cantidad": cant_n2,
                    "unidad": unid_n2
                })

    return mp_list, n1_list, n2_list

# ==========================================
# 4. CARGA DE DATOS DESDE GOOGLE SHEETS
# ==========================================
SHEET_ID = "15i803Mms20T32_jLChK8326eCq_A6eMhG6kUoP-_H6U"

@st.cache_data(ttl=120)
def cargar_hoja_por_gid(gid):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    return pd.read_csv(url)

@st.cache_data(ttl=120)
def cargar_todas_las_hojas():
    try:
        # Intenta cargar por gids estándar de Google Sheets
        df_n3 = cargar_hoja_por_gid("0")
        df_n2 = cargar_hoja_por_gid("1835334704") # Asume primer y segundo gid
        df_n1 = cargar_hoja_por_gid("1231718018")
        df_mp = cargar_hoja_por_gid("9876543210")
        return df_n3, df_n2, df_n1, df_mp
    except:
        # Fallback con pubhtml si los gids cambian
        try:
            url_base = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/pub?output=csv"
            df = pd.read_csv(url_base)
            return df, df, df, df
        except Exception as e:
            st.error(f"Error al conectar con Google Sheets: {e}")
            return None, None, None, None

df_recetas_n3, df_recetas_n2, df_recetas_n1, df_insumos_mp = cargar_todas_las_hojas()

if df_recetas_n3 is None:
    st.stop()

# ==========================================
# 5. MENÚ LATERAL Y NAVEGACIÓN
# ==========================================
st.sidebar.title("🥐 Menú Principal")

opcion = st.sidebar.radio(
    "Selecciona la función:",
    [
        "📋 Ficha Técnica de Producto (N3)",
        "📊 Control de Márgenes y Estados (N3)",
        "💵 Simulación Financiera Multinivel",
        "🗂 Explorador de Tablas"
    ]
)

productos_n3 = df_recetas_n3.iloc[:, 0].dropna().unique().tolist()
productos_n3 = [p for p in productos_n3 if str(p).strip() not in ["", "-", "CODIGO", "PRODUCTO"]]

# ==========================================
# VISTA 1: FICHA TÉCNICA DE PRODUCTO (N3)
# ==========================================
if opcion == "📋 Ficha Técnica de Producto (N3)":
    st.title("📋 Ficha Técnica de Producto (N3)")
    st.caption("Estructura jerárquica de insumos, masas/bizcochuelos (N1) y rellenos/coberturas (N2).")

    prod_sel = st.selectbox("Selecciona un Producto terminado (N3):", productos_n3)

    if prod_sel:
        filas_prod = df_recetas_n3[df_recetas_n3.iloc[:, 0] == prod_sel]

        mp_list, n1_list, n2_list = extraer_componentes_por_columnas(filas_prod)

        st.subheader(f"🍰 {prod_sel}")
        st.divider()

        # MATERIA PRIMA DIRECTA
        with st.expander(f"🔹 Materia Prima Directa ({len(mp_list)} insumos)", expanded=True):
            if mp_list:
                df_mp_disp = pd.DataFrame(mp_list)
                st.dataframe(
                    df_mp_disp,
                    column_config={
                        "Cantidad": st.column_config.NumberColumn("Cantidad", format="%.4f")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay Materias Primas directas registradas para este producto.")

        # RECETAS N1 (MASAS / BIZCOCHUELOS)
        if n1_list:
            st.markdown("##### 🟡 Recetas N1 (Masas / Bizcochuelos)")
            for item_n1 in n1_list:
                cod_n1 = item_n1["codigo"]
                nom_n1 = item_n1["nombre"]
                cant_n1 = item_n1["cantidad"]
                unid_n1 = item_n1["unidad"]

                with st.expander(f"🟡 **[{cod_n1}] {nom_n1}** — {cant_n1:.4f} {unid_n1}"):
                    filas_sub_n1 = df_recetas_n1[
                        (df_recetas_n1.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(nom_n1))
                        | (df_recetas_n1.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nom_n1))
                    ]
                    if not filas_sub_n1.empty:
                        mp_sub1, _, _ = extraer_componentes_por_columnas(filas_sub_n1)
                        if mp_sub1:
                            st.caption("Insumos de esta Masa/Bizcochuelo:")
                            st.dataframe(pd.DataFrame(mp_sub1), use_container_width=True, hide_index=True)
                        else:
                            st.write("Sin insumos directos registrados.")
                    else:
                        st.write("Detalle no encontrado en la hoja Recetas_N1.")

        # RECETAS N2 (INTERMEDIOS / RELLENOS)
        if n2_list:
            st.markdown("##### 🟠 Recetas N2 (Intermedios / Rellenos)")
            for item_n2 in n2_list:
                cod_n2 = item_n2["codigo"]
                nom_n2 = item_n2["nombre"]
                cant_n2 = item_n2["cantidad"]
                unid_n2 = item_n2["unidad"]

                with st.expander(f"🟠 **[{cod_n2}] {nom_n2}** — {cant_n2:.4f} {unid_n2}"):
                    filas_sub_n2 = df_recetas_n2[
                        (df_recetas_n2.iloc[:, 0].apply(normalizar_cod) == normalizar_cod(nom_n2))
                        | (df_recetas_n2.iloc[:, 0].apply(limpiar_texto_comparar) == limpiar_texto_comparar(nom_n2))
                    ]
                    if not filas_sub_n2.empty:
                        mp_sub2, _, _ = extraer_componentes_por_columnas(filas_sub_n2)
                        if mp_sub2:
                            st.caption("Insumos de este Relleno/Intermedio:")
                            st.dataframe(pd.DataFrame(mp_sub2), use_container_width=True, hide_index=True)
                        else:
                            st.write("Sin insumos directos registrados.")
                    else:
                        st.write("Detalle no encontrado en la hoja Recetas_N2.")

# ==========================================
# VISTA 2: CONTROL DE MÁRGENES Y ESTADOS
# ==========================================
elif opcion == "📊 Control de Márgenes y Estados (N3)":
    st.title("📊 Control de Márgenes y Estados de Productos (N3)")
    st.caption("Resumen consolidado del catálogo.")

    resumen_data = []
    for prod in productos_n3:
        filas = df_recetas_n3[df_recetas_n3.iloc[:, 0] == prod]
        mp, n1, n2 = extraer_componentes_por_columnas(filas)
        resumen_data.append({
            "Producto N3": prod,
            "Insumos Directos": len(mp),
            "Recetas N1": len(n1),
            "Recetas N2": len(n2),
            "Estado Receta": "Completa" if (mp or n1 or n2) else "Incompleta"
        })

    df_res = pd.DataFrame(resumen_data)
    st.dataframe(df_res, use_container_width=True, hide_index=True)

# ==========================================
# VISTA 3: SIMULACIÓN FINANCIERA
# ==========================================
elif opcion == "💵 Simulación Financiera Multinivel":
    st.title("💵 Simulación Financiera Multinivel")
    st.info("Módulo de proyección de costos según precios de lista MP.")

# ==========================================
# VISTA 4: EXPLORADOR DE TABLAS
# ==========================================
elif opcion == "🗂 Explorador de Tablas":
    st.title("🗂 Explorador de Tablas Raw")
    st.dataframe(df_recetas_n3)
