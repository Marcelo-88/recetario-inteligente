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


# Limpieza de strings estándar
def normalizar_texto(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan"]:
        return ""
    val_str = str(val).strip()
    # Si viene tipo '100.0', quitar decimales
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str.upper().strip()


# Extraer números
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
    st.header("💥 Simulación de Impacto en Costos (Vía Códigos / Nombres)")
    st.info(
        "Simulación con trazabilidad inteligente por código ERP y coincidencia de nombres."
    )

    try:
        # Carga de datos
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # Función para hallar columna adecuada
        def buscar_columna(df, candidatos, default_idx=0):
            for cand in candidatos:
                for c in df.columns:
                    if cand.upper() in c.upper():
                        return c
            return df.columns[default_idx] if len(df.columns) > default_idx else df.columns[0]

        col_cod_mermas = buscar_columna(df_mermas, ["CODIGO", "COD", "ID"], 0)
        col_nom_mermas = buscar_columna(df_mermas, ["ARTICULO", "NOMBRE", "DESCRIPCION", "MATERIA", "INSUMO"], 1)

        # Preparar lista de insumos
        df_mermas["COD_NORM"] = df_mermas[col_cod_mermas].apply(normalizar_texto)
        df_mermas["NOM_NORM"] = df_mermas[col_nom_mermas].apply(normalizar_texto)

        df_mermas["COMBO_MOSTRAR"] = (
            df_mermas[col_cod_mermas].astype(str).str.strip()
            + " | "
            + df_mermas[col_nom_mermas].astype(str).str.strip()
        )

        lista_opciones = sorted(
            [x for x in df_mermas["COMBO_MOSTRAR"].dropna().unique() if len(str(x).strip()) > 3]
        )

        st.subheader("1️⃣ Selecciona la Materia Prima / Empaque a Simular")
        opcion_elegida = st.selectbox(
            "Buscar Insumo por Código o Nombre:",
            lista_opciones,
        )

        if opcion_elegida:
            datos_insumo = df_mermas[df_mermas["COMBO_MOSTRAR"] == opcion_elegida].iloc[0]

            codigo_target = datos_insumo["COD_NORM"]
            nombre_target = datos_insumo["NOM_NORM"]
            articulo_mostrar = str(datos_insumo[col_nom_mermas]).strip()
            codigo_mostrar = str(datos_insumo[col_cod_mermas]).strip()

            costo_actual = 0.0
            for col in df_mermas.columns:
                if any(k in col.upper() for k in ["COSTO", "PRECIO", "VALOR"]):
                    val = extraer_num(datos_insumo[col])
                    if val > 0:
                        costo_actual = val
                        break

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Insumo Seleccionado", f"[{codigo_mostrar}]")
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

            # Mapeo de columnas para cada receta
            col_rec_n1 = buscar_columna(df_recetas_n1, ["RECETA", "COD_RECETA"], 0)
            col_ins_n1 = buscar_columna(df_recetas_n1, ["MATERIA", "INSUMO", "COD_INSUMO", "CODIGO"], 1)
            col_cant_n1 = buscar_columna(df_recetas_n1, ["CANT", "PESO", "USO"], 2)

            col_rec_n2 = buscar_columna(df_recetas_n2, ["RECETA", "COD_RECETA"], 0)
            col_ins_n2 = buscar_columna(df_recetas_n2, ["CODIGO", "INSUMO", "SUBRECETA", "MATERIA"], 1)
            col_cant_n2 = buscar_columna(df_recetas_n2, ["CANT", "PESO", "USO"], 2)

            col_rec_n3 = buscar_columna(df_recetas_n3, ["RECETA", "COD_RECETA"], 0)
            col_ins_n3 = buscar_columna(df_recetas_n3, ["MATERIA", "INSUMO", "CODIGO", "SUBRECETA"], 1)
            col_cant_n3 = buscar_columna(df_recetas_n3, ["CANT", "PESO", "USO"], 2)

            # Mapeo de listas maestras
            col_l1_cod = buscar_columna(df_lista_n1, ["COD"], 0)
            col_l1_nom = buscar_columna(df_lista_n1, ["NOMBRE", "PRODUCTO", "RECETA"], 1)
            col_l1_costo = buscar_columna(df_lista_n1, ["COSTO", "PRECIO"], 2)
            col_l1_peso = buscar_columna(df_lista_n1, ["PESO", "BATCH", "REND"], 3)

            col_l2_cod = buscar_columna(df_lista_n2, ["COD"], 0)
            col_l2_nom = buscar_columna(df_lista_n2, ["NOMBRE", "PRODUCTO", "RECETA"], 1)
            col_l2_costo = buscar_columna(df_lista_n2, ["COSTO", "PRECIO"], 2)
            col_l2_peso = buscar_columna(df_lista_n2, ["PESO", "BATCH", "REND"], 3)

            col_l3_cod = buscar_columna(df_lista_n3, ["COD"], 0)
            col_l3_nom = buscar_columna(df_lista_n3, ["NOMBRE", "PRODUCTO", "RECETA"], 1)
            col_l3_costo = buscar_columna(df_lista_n3, ["COSTO", "PRECIO"], 2)

            # Normalizar columnas de cruce
            df_recetas_n1["INS_NORM"] = df_recetas_n1[col_ins_n1].apply(normalizar_texto)
            df_recetas_n2["INS_NORM"] = df_recetas_n2[col_ins_n2].apply(normalizar_texto)
            df_recetas_n3["INS_NORM"] = df_recetas_n3[col_ins_n3].apply(normalizar_texto)

            df_lista_n1["COD_NORM"] = df_lista_n1[col_l1_cod].apply(normalizar_texto)
            df_lista_n1["NOM_NORM"] = df_lista_n1[col_l1_nom].apply(normalizar_texto)

            df_lista_n2["COD_NORM"] = df_lista_n2[col_l2_cod].apply(normalizar_texto)
            df_lista_n2["NOM_NORM"] = df_lista_n2[col_l2_nom].apply(normalizar_texto)

            df_lista_n3["COD_NORM"] = df_lista_n3[col_l3_cod].apply(normalizar_texto)
            df_lista_n3["NOM_NORM"] = df_lista_n3[col_l3_nom].apply(normalizar_texto)

            # Evaluar Coincidencia (por código O por nombre)
            def es_coincidencia(valor_tabla, cod_target, nom_target):
                if not valor_tabla:
                    return False
                if cod_target and valor_tabla == cod_target:
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

                inc_total_receta = 0.0
                cant_insumo_usada = 0.0

                for _, row in df_ing.iterrows():
                    val_ins = row["INS_NORM"]
                    if es_coincidencia(val_ins, codigo_target, nombre_target):
                        cant = extraer_num(row[col_cant_n1])
                        cant_insumo_usada += cant
                        inc_total_receta += cant * dif_precio

                if inc_total_receta > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    row_lista = df_lista_n1[(df_lista_n1["COD_NORM"] == rec_norm) | (df_lista_n1["NOM_NORM"] == rec_norm)]
                    nom_n1 = str(cod_rec).strip()
                    costo_base = 0.0
                    peso_batch = 1.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n1 = str(r0[col_l1_nom]).strip()
                        costo_base = extraer_num(r0[col_l1_costo])
                        peso_val = extraer_num(r0[col_l1_peso])
                        if peso_val > 0:
                            peso_batch = peso_val

                    inc_unitario = inc_total_receta / peso_batch
                    impactos_n1[rec_norm] = inc_unitario
                    impactos_n1[normalizar_texto(nom_n1)] = inc_unitario

                    filas_resumen_n1.append({
                        "Código / Receta": nom_n1,
                        "Cant. Insumo Usada": f"{cant_insumo_usada:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l1 = pd.DataFrame(filas_resumen_n1)

            # --- EVALUACIÓN NIVEL N2 ---
            impactos_n2 = {}
            filas_resumen_n2 = []

            for cod_rec, df_ing in df_recetas_n2.groupby(col_rec_n2):
                if not str(cod_rec).strip():
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0

                for _, row in df_ing.iterrows():
                    val_ins = row["INS_NORM"]
                    cant = extraer_num(row[col_cant_n2])

                    if es_coincidencia(val_ins, codigo_target, nombre_target):
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                    elif val_ins in impactos_n1:
                        inc_total_receta += cant * impactos_n1[val_ins]
                        cant_referencial += cant

                if inc_total_receta > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    row_lista = df_lista_n2[(df_lista_n2["COD_NORM"] == rec_norm) | (df_lista_n2["NOM_NORM"] == rec_norm)]
                    nom_n2 = str(cod_rec).strip()
                    costo_base = 0.0
                    peso_batch = 1.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n2 = str(r0[col_l2_nom]).strip()
                        costo_base = extraer_num(r0[col_l2_costo])
                        peso_val = extraer_num(r0[col_l2_peso])
                        if peso_val > 0:
                            peso_batch = peso_val

                    inc_unitario = inc_total_receta / peso_batch
                    impactos_n2[rec_norm] = inc_unitario
                    impactos_n2[normalizar_texto(nom_n2)] = inc_unitario

                    filas_resumen_n2.append({
                        "Código / Receta": nom_n2,
                        "Cant. Componente Usada": f"{cant_referencial:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l2 = pd.DataFrame(filas_resumen_n2)

            # --- EVALUACIÓN NIVEL N3 ---
            filas_resumen_n3 = []

            for cod_rec, df_ing in df_recetas_n3.groupby(col_rec_n3):
                if not str(cod_rec).strip():
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0

                for _, row in df_ing.iterrows():
                    val_ins = row["INS_NORM"]
                    cant = extraer_num(row[col_cant_n3])

                    if es_coincidencia(val_ins, codigo_target, nombre_target):
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                    elif val_ins in impactos_n1:
                        inc_total_receta += cant * impactos_n1[val_ins]
                        cant_referencial += cant
                    elif val_ins in impactos_n2:
                        inc_total_receta += cant * impactos_n2[val_ins]
                        cant_referencial += cant

                if inc_total_receta > 0:
                    rec_norm = normalizar_texto(cod_rec)
                    row_lista = df_lista_n3[(df_lista_n3["COD_NORM"] == rec_norm) | (df_lista_n3["NOM_NORM"] == rec_norm)]
                    nom_n3 = str(cod_rec).strip()
                    costo_base = 0.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n3 = str(r0[col_l3_nom]).strip()
                        costo_base = extraer_num(r0[col_l3_costo])

                    filas_resumen_n3.append({
                        "Código / Producto Final": nom_n3,
                        "Cant. Componente Usada": f"{cant_referencial:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l3 = pd.DataFrame(filas_resumen_n3)

            # --- PRESENTACIÓN VISUAL ---
            st.subheader(
                f"📊 Comparativa Ejecutiva de Productos Afectados por: [{codigo_mostrar}] {articulo_mostrar}"
            )

            resumen_tabs1, resumen_tabs2, resumen_tabs3, tab_debug = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Listas_N2)",
                    "🔴 Sub-Recetas Base (Lista_N1)",
                    "🔍 Diagnóstico de Códigos",
                ]
            )

            with resumen_tabs1:
                st.write(f"**Productos Finales N3 Afectados:** {len(resumen_l3)}")
                if not resumen_l3.empty:
                    st.dataframe(resumen_l3, use_container_width=True)
                else:
                    st.info("No se encontraron productos finales N3 afectados por este insumo o sus subrecetas.")

            with resumen_tabs2:
                st.write(f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}")
                if not resumen_l2.empty:
                    st.dataframe(resumen_l2, use_container_width=True)
                else:
                    st.info("No se encontraron productos intermedios N2 afectados por este insumo.")

            with resumen_tabs3:
                st.write(f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}")
                if not resumen_l1.empty:
                    st.dataframe(resumen_l1, use_container_width=True)
                else:
                    st.info("No se encontraron sub-recetas N1 afectadas por este insumo.")

            with tab_debug:
                st.write("### 🔍 Diagnóstico de Búsqueda Flexible")
                st.write(f"**Código Objetivo Normalizado:** `{codigo_target}`")
                st.write(f"**Nombre Objetivo Normalizado:** `{nombre_target}`")

                c1_d, c2_d, c3_d = st.columns(3)
                with c1_d:
                    st.caption("Pestaña Recetas_N1")
                    st.write(f"Columna Receta: `{col_rec_n1}`")
                    st.write(f"Columna Insumo: `{col_ins_n1}`")
                    c_n1 = df_recetas_n1[df_recetas_n1["INS_NORM"].apply(lambda x: es_coincidencia(x, codigo_target, nombre_target))]
                    st.write(f"Coincidencias: **{len(c_n1)}**")
                    if not c_n1.empty:
                        st.dataframe(c_n1[[col_rec_n1, col_ins_n1, col_cant_n1]])

                with c2_d:
                    st.caption("Pestaña Recetas_N2")
                    st.write(f"Columna Receta: `{col_rec_n2}`")
                    st.write(f"Columna Insumo: `{col_ins_n2}`")
                    c_n2 = df_recetas_n2[df_recetas_n2["INS_NORM"].apply(lambda x: es_coincidencia(x, codigo_target, nombre_target))]
                    st.write(f"Coincidencias: **{len(c_n2)}**")
                    if not c_n2.empty:
                        st.dataframe(c_n2[[col_rec_n2, col_ins_n2, col_cant_n2]])

                with c3_d:
                    st.caption("Pestaña Recetas_N3")
                    st.write(f"Columna Receta: `{col_rec_n3}`")
                    st.write(f"Columna Insumo: `{col_ins_n3}`")
                    c_n3 = df_recetas_n3[df_recetas_n3["INS_NORM"].apply(lambda x: es_coincidencia(x, codigo_target, nombre_target))]
                    st.write(f"Coincidencias: **{len(c_n3)}**")
                    if not c_n3.empty:
                        st.dataframe(c_n3[[col_rec_n3, col_ins_n3, col_cant_n3]])

    except Exception as e:
        st.error(f"Error durante el cálculo de la simulación: {e}")
