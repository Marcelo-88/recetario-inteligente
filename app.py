import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Multinivel (Vía Códigos y Nombres)")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.str.strip()
    return df.fillna("")


def normalizar_texto(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan"]:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str.upper().strip()


def extraer_num(val):
    if pd.isna(val) or val == "":
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0


# 1. Menú Principal
st.sidebar.header("🕹️ Módulos")
modo_app = st.sidebar.radio(
    "Selecciona la función:",
    ["📋 Explorador de Tablas", "💥 Simulación Financiera Multinivel"],
)
st.sidebar.divider()

# -------------------------------------------------------------
# MÓDULO 1: EXPLORADOR DE TABLAS
# -------------------------------------------------------------
if modo_app == "📋 Explorador de Tablas":
    st.sidebar.header("📁 Pestañas del Recetario")
    pestaña_activa = st.sidebar.radio(
        "Selecciona la vista:",
        [
            "Recetas_N3",
            "Lista_N3",
            "Recetas_N2",
            "Listas_N2",
            "Recetas_N1",
            "Lista_N1",
            "Materia_Prima",
            "Mermas_Costos",
        ],
    )

    try:
        with st.spinner(f"Cargando {pestaña_activa}..."):
            df = cargar_pestaña(pestaña_activa)

        st.subheader(f"📊 Vista de Datos: {pestaña_activa}")
        busqueda = st.text_input(
            f"🔍 Buscar en {pestaña_activa} (código, nombre, ingrediente):"
        )

        if busqueda:
            mascara = df.apply(
                lambda row: row.astype(str)
                .str.contains(busqueda, case=False, na=False)
                .any(),
                axis=1,
            )
            df_filtrado = df[mascara]
            st.success(f"Se encontraron **{len(df_filtrado)}** resultados")
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar {pestaña_activa}: {e}")

# -------------------------------------------------------------
# MÓDULO 2: SIMULACIÓN FINANCIERA MULTINIVEL
# -------------------------------------------------------------
elif modo_app == "💥 Simulación Financiera Multinivel":
    st.header("💥 Simulación de Impacto en Costos")
    st.info("Simulación con trazabilidad inteligente multinivel.")

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # BÚSQUEDA ESPECÍFICA DE COLUMNAS EN MERMAS_COSTOS
        col_cod_mermas = None
        col_nom_mermas = None

        for c in df_mermas.columns:
            if "CÓDIGO ERP" in c.upper() or "CODIGO ERP" in c.upper():
                col_cod_mermas = c
            elif "INSUMO RECETARIO" in c.upper() or "INSUMO" in c.upper():
                col_nom_mermas = c

        if not col_cod_mermas:
            col_cod_mermas = df_mermas.columns[1]  # Columna B por defecto
        if not col_nom_mermas:
            col_nom_mermas = df_mermas.columns[0]  # Columna A por defecto

        def buscar_columna_costo(df):
            for c in df.columns:
                c_up = c.upper()
                if any(k in c_up for k in ["COSTO", "PRECIO", "VALOR"]):
                    return c
            return df.columns[-1]

        def buscar_columna_nombre(df):
            for c in df.columns:
                c_up = c.upper()
                if any(k in c_up for k in ["NOMBRE", "PRODUCTO", "RECETA", "ARTICULO", "DESCRIPCION"]):
                    return c
            return df.columns[1] if len(df.columns) > 1 else df.columns[0]

        df_mermas["COD_NORM"] = df_mermas[col_cod_mermas].apply(normalizar_texto)
        df_mermas["NOM_NORM"] = df_mermas[col_nom_mermas].apply(normalizar_texto)

        # Construcción limpia para el desplegable: Nombre [Código ERP]
        df_mermas["COMBO_MOSTRAR"] = (
            df_mermas[col_nom_mermas].astype(str).str.strip()
            + " ["
            + df_mermas[col_cod_mermas].astype(str).str.strip()
            + "]"
        )

        lista_opciones = sorted(
            [x for x in df_mermas["COMBO_MOSTRAR"].dropna().unique() if len(str(x).strip()) > 3]
        )

        st.subheader("1️⃣ Selecciona la Materia Prima / Empaque a Simular")
        opcion_elegida = st.selectbox("Buscar Insumo por Nombre o Código ERP:", lista_opciones)

        if opcion_elegida:
            datos_insumo = df_mermas[df_mermas["COMBO_MOSTRAR"] == opcion_elegida].iloc[0]

            codigo_target = datos_insumo["COD_NORM"]
            nombre_target = datos_insumo["NOM_NORM"]
            articulo_mostrar = str(datos_insumo[col_nom_mermas]).strip()
            codigo_mostrar = str(datos_insumo[col_cod_mermas]).strip()

            col_costo_mermas = buscar_columna_costo(df_mermas)
            costo_actual = extraer_num(datos_insumo[col_costo_mermas])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Insumo Seleccionado", f"[{codigo_mostrar if codigo_mostrar else 'S/C'}]")
                st.caption(articulo_mostrar)
            with c2:
                nuevo_precio = st.number_input(
                    "Nuevo precio simulado (Bs):",
                    min_value=0.0,
                    value=float(costo_actual * 1.20) if costo_actual > 0 else 25.0,
                    step=1.0,
                )
            with c3:
                dif_precio = nuevo_precio - costo_actual
                porc_inc = (dif_precio / costo_actual * 100) if costo_actual > 0 else 0
                st.metric(
                    "Incremento Unitario Insumo",
                    f"+Bs {dif_precio:.2f}",
                    delta=f"{porc_inc:.1f}%",
                )

            st.divider()

            # Columnas de recetas
            col_rec_n1 = df_recetas_n1.columns[0]
            col_ins_n1 = df_recetas_n1.columns[1]
            col_cant_n1 = df_recetas_n1.columns[2]

            col_rec_n2 = df_recetas_n2.columns[0]
            col_ins_n2 = df_recetas_n2.columns[1]
            col_cant_n2 = df_recetas_n2.columns[2]

            col_rec_n3 = df_recetas_n3.columns[0]
            col_ins_n3 = df_recetas_n3.columns[1]
            col_cant_n3 = df_recetas_n3.columns[2]

            col_l1_nom = buscar_columna_nombre(df_lista_n1)
            col_l1_costo = buscar_columna_costo(df_lista_n1)

            col_l2_nom = buscar_columna_nombre(df_lista_n2)
            col_l2_costo = buscar_columna_costo(df_lista_n2)

            col_l3_nom = buscar_columna_nombre(df_lista_n3)
            col_l3_costo = buscar_columna_costo(df_lista_n3)

            # Normalización
            df_recetas_n1["INS_NORM"] = df_recetas_n1[col_ins_n1].apply(normalizar_texto)
            df_recetas_n2["INS_NORM"] = df_recetas_n2[col_ins_n2].apply(normalizar_texto)
            df_recetas_n3["INS_NORM"] = df_recetas_n3[col_ins_n3].apply(normalizar_texto)

            df_lista_n1["NOM_NORM"] = df_lista_n1[col_l1_nom].apply(normalizar_texto)
            df_lista_n2["NOM_NORM"] = df_lista_n2[col_l2_nom].apply(normalizar_texto)
            df_lista_n3["NOM_NORM"] = df_lista_n3[col_l3_nom].apply(normalizar_texto)

            def es_coincidencia(valor_tabla, cod_target, nom_target):
                if not valor_tabla:
                    return False
                if cod_target and (valor_tabla == cod_target):
                    return True
                if nom_target and (nom_target in valor_tabla or valor_tabla in nom_target):
                    return True
                return False

            # --- EVALUACIÓN NIVEL N1 ---
            impactos_n1 = {}
            filas_resumen_n1 = []

            for cod_rec, df_ing in df_recetas_n1.groupby(col_rec_n1):
                if not str(cod_rec).strip():
                    continue

                inc_total = 0.0
                cant_usada = 0.0

                for _, row in df_ing.iterrows():
                    if es_coincidencia(row["INS_NORM"], codigo_target, nombre_target):
                        cant = extraer_num(row[col_cant_n1])
                        cant_usada += cant
                        inc_total += cant * dif_precio

                if inc_total > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    impactos_n1[rec_norm] = inc_total

                    # Búsqueda de costo base
                    row_lista = df_lista_n1[
                        df_lista_n1["NOM_NORM"].apply(lambda x: rec_norm in x or x in rec_norm if x else False)
                    ]
                    costo_base = extraer_num(row_lista.iloc[0][col_l1_costo]) if not row_lista.empty else 0.0

                    filas_resumen_n1.append({
                        "Código / Receta": cod_rec,
                        "Cant. Insumo Usada": f"{cant_usada:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total:.2f}",
                        "Variación (%)": f"+{(inc_total / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            # --- EVALUACIÓN NIVEL N2 ---
            impactos_n2 = {}
            filas_resumen_n2 = []

            for cod_rec, df_ing in df_recetas_n2.groupby(col_rec_n2):
                if not str(cod_rec).strip():
                    continue

                inc_total = 0.0
                cant_usada = 0.0

                for _, row in df_ing.iterrows():
                    val_ins = row["INS_NORM"]
                    cant = extraer_num(row[col_cant_n2])

                    if es_coincidencia(val_ins, codigo_target, nombre_target):
                        inc_total += cant * dif_precio
                        cant_usada += cant
                    elif val_ins in impactos_n1:
                        inc_total += cant * impactos_n1[val_ins]
                        cant_usada += cant

                if inc_total > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    impactos_n2[rec_norm] = inc_total

                    # Búsqueda inteligente de costo base en Listas_N2 (compara todas las columnas si es necesario)
                    row_lista = df_lista_n2[
                        df_lista_n2.apply(
                            lambda r: any(rec_norm in normalizar_texto(val) for val in r if val), axis=1
                        )
                    ]
                    
                    costo_base = 0.0
                    if not row_lista.empty:
                        costo_base = extraer_num(row_lista.iloc[0][col_l2_costo])

                    filas_resumen_n2.append({
                        "Código / Receta": cod_rec,
                        "Cant. Componente Usada": f"{cant_usada:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total:.2f}",
                        "Variación (%)": f"+{(inc_total / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            # --- EVALUACIÓN NIVEL N3 ---
            filas_resumen_n3 = []

            for cod_rec, df_ing in df_recetas_n3.groupby(col_rec_n3):
                if not str(cod_rec).strip():
                    continue

                inc_total = 0.0
                cant_usada = 0.0

                for _, row in df_ing.iterrows():
                    val_ins = row["INS_NORM"]
                    cant = extraer_num(row[col_cant_n3])

                    if es_coincidencia(val_ins, codigo_target, nombre_target):
                        inc_total += cant * dif_precio
                        cant_usada += cant
                    elif val_ins in impactos_n1:
                        inc_total += cant * impactos_n1[val_ins]
                        cant_usada += cant
                    elif val_ins in impactos_n2:
                        inc_total += cant * impactos_n2[val_ins]
                        cant_usada += cant

                if inc_total > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    row_lista = df_lista_n3[
                        df_lista_n3.apply(
                            lambda r: any(rec_norm in normalizar_texto(val) for val in r if val), axis=1
                        )
                    ]
                    costo_base = 0.0
                    if not row_lista.empty:
                        costo_base = extraer_num(row_lista.iloc[0][col_l3_costo])

                    filas_resumen_n3.append({
                        "Código / Producto Final": cod_rec,
                        "Cant. Componente Usada": f"{cant_usada:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total:.2f}",
                        "Variación (%)": f"+{(inc_total / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            # DataFrames
            resumen_l1 = pd.DataFrame(filas_resumen_n1)
            resumen_l2 = pd.DataFrame(filas_resumen_n2)
            resumen_l3 = pd.DataFrame(filas_resumen_n3)

            # Renders
            st.subheader(f"📊 Comparativa Ejecutiva de Productos Afectados por: {articulo_mostrar} [{codigo_mostrar}]")

            t1, t2, t3 = st.tabs([
                "🟢 Productos Finales (Lista_N3)",
                "🟠 Rellenos / Intermedios (Listas_N2)",
                "🔴 Sub-Recetas Base (Lista_N1)"
            ])

            with t1:
                st.write(f"**Productos Finales N3 Afectados:** {len(resumen_l3)}")
                st.dataframe(resumen_l3, use_container_width=True) if not resumen_l3.empty else st.info("Sin registros N3.")

            with t2:
                st.write(f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}")
                st.dataframe(resumen_l2, use_container_width=True) if not resumen_l2.empty else st.info("Sin registros N2.")

            with t3:
                st.write(f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}")
                st.dataframe(resumen_l1, use_container_width=True) if not resumen_l1.empty else st.info("Sin registros N1.")

    except Exception as e:
        st.error(f"Error en simulación: {e}")
