import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera por Códigos ERP Únicos (Lista N1 ➔ N2 ➔ N3)")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=30)  # TTL corto para refrescar cambios rápidos del Drive
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url)
    df.columns = df.columns.str.strip()
    return df.fillna("")


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
# MÓDULO 2: SIMULACIÓN FINANCIERA MULTINIVEL (POR CÓDIGOS ERP)
# -------------------------------------------------------------
elif modo_app == "💥 Simulación Financiera Multinivel":
    st.header("💥 Simulación de Impacto en Costos (Vía Códigos ERP)")
    st.info(
        "Simulación con trazabilidad exacta basada en códigos unificados de insumos y subrecetas."
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

        # Identificar columnas en Mermas/Materia Prima
        col_codigo = next((c for c in df_mermas.columns if "COD" in c.upper()), df_mermas.columns[1])
        col_articulo = next((c for c in df_mermas.columns if any(k in c.upper() for k in ["ARTICULO", "NOMBRE", "DESCRIPCION", "RECETARIO"])), df_mermas.columns[2])

        df_mermas["COMBO_MOSTRAR"] = (
            df_mermas[col_codigo].astype(str).str.strip()
            + " | "
            + df_mermas[col_articulo].astype(str).str.strip()
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

            codigo_target = str(datos_insumo[col_codigo]).strip()
            articulo_target = str(datos_insumo[col_articulo]).strip()

            costo_actual = 0.0
            for col in df_mermas.columns:
                if any(k in col.upper() for k in ["COSTO", "PRECIO", "VALOR"]):
                    try:
                        val_str = str(datos_insumo[col]).replace("Bs", "").replace("$", "").replace(",", ".").strip()
                        val = float(val_str)
                        if val > 0:
                            costo_actual = val
                            break
                    except:
                        pass

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Insumo Seleccionado", f"[{codigo_target}]")
                st.caption(articulo_target)
            with c2:
                nuevo_precio = st.number_input(
                    "Nuevo precio simulado (Bs):",
                    min_value=0.0,
                    value=float(costo_actual * 1.20) if costo_actual > 0 else 10.0,
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

            # --- FUNCIONES AUXILIARES DE EXTRACCIÓN ---
            def extraer_num(val):
                if pd.isna(val) or val == "":
                    return 0.0
                try:
                    cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
                    return float(cleaned) if cleaned else 0.0
                except:
                    return 0.0

            def obtener_col_por_patron(df, palabras_clave, default_idx=0):
                for c in df.columns:
                    c_up = c.upper()
                    if any(k in c_up for k in palabras_clave):
                        return c
                return df.columns[default_idx] if len(df.columns) > default_idx else df.columns[0]

            # Detectar columnas clave en recetas
            col_cod_receta_n1 = obtener_col_por_patron(df_recetas_n1, ["COD_RECETA", "CODIGO_RECETA", "RECETA_COD"], 0)
            col_cod_insumo_n1 = obtener_col_por_patron(df_recetas_n1, ["COD_INSUMO", "COD_MATERIA", "CODIGO_INSUMO", "COD_COMPONENTE"], 1)
            col_cant_n1 = obtener_col_por_patron(df_recetas_n1, ["CANT", "PESO", "USO"], 2)

            col_cod_receta_n2 = obtener_col_por_patron(df_recetas_n2, ["COD_RECETA", "CODIGO_RECETA", "RECETA_COD"], 0)
            col_cod_insumo_n2 = obtener_col_por_patron(df_recetas_n2, ["COD_INSUMO", "COD_SUBRECETA", "COD_COMPONENTE"], 1)
            col_cant_n2 = obtener_col_por_patron(df_recetas_n2, ["CANT", "PESO", "USO"], 2)

            col_cod_receta_n3 = obtener_col_por_patron(df_recetas_n3, ["COD_RECETA", "CODIGO_RECETA", "RECETA_COD"], 0)
            col_cod_insumo_n3 = obtener_col_por_patron(df_recetas_n3, ["COD_INSUMO", "COD_SUBRECETA", "COD_COMPONENTE"], 1)
            col_cant_n3 = obtener_col_por_patron(df_recetas_n3, ["CANT", "PESO", "USO"], 2)

            # Detectar columnas clave en maestras/listas
            col_lista_cod_n1 = obtener_col_por_patron(df_lista_n1, ["COD"], 0)
            col_lista_nom_n1 = obtener_col_por_patron(df_lista_n1, ["NOMBRE", "PRODUCTO", "RECETA", "DESCRIPCION"], 1)
            col_lista_costo_n1 = obtener_col_por_patron(df_lista_n1, ["COSTO", "PRECIO"], 2)
            col_lista_peso_n1 = obtener_col_por_patron(df_lista_n1, ["PESO", "BATCH", "REND", "RND"], 3)

            col_lista_cod_n2 = obtener_col_por_patron(df_lista_n2, ["COD"], 0)
            col_lista_nom_n2 = obtener_col_por_patron(df_lista_n2, ["NOMBRE", "PRODUCTO", "RECETA", "DESCRIPCION"], 1)
            col_lista_costo_n2 = obtener_col_por_patron(df_lista_n2, ["COSTO", "PRECIO"], 2)
            col_lista_peso_n2 = obtener_col_por_patron(df_lista_n2, ["PESO", "BATCH", "REND", "RND"], 3)

            col_lista_cod_n3 = obtener_col_por_patron(df_lista_n3, ["COD"], 0)
            col_lista_nom_n3 = obtener_col_por_patron(df_lista_n3, ["NOMBRE", "PRODUCTO", "RECETA", "DESCRIPCION"], 1)
            col_lista_costo_n3 = obtener_col_por_patron(df_lista_n3, ["COSTO", "PRECIO"], 2)

            # -------------------------------------------------------------
            # EVALUACIÓN NIVEL N1 (SUBRECETAS BASE)
            # -------------------------------------------------------------
            impactos_n1 = {}  # {cod_n1: incremento_unitario_por_kg_o_unidad}
            filas_resumen_n1 = []

            for cod_receta, df_ing in df_recetas_n1.groupby(col_cod_receta_n1):
                cod_n1 = str(cod_receta).strip()
                if not cod_n1:
                    continue

                inc_total_receta = 0.0
                cant_insumo_usada = 0.0

                for _, row in df_ing.iterrows():
                    cod_insumo_row = str(row[col_cod_insumo_n1]).strip()
                    if cod_insumo_row == codigo_target:
                        cant = extraer_num(row[col_cant_n1])
                        cant_insumo_usada += cant
                        inc_total_receta += cant * dif_precio

                if inc_total_receta > 0:
                    row_lista = df_lista_n1[df_lista_n1[col_lista_cod_n1].astype(str).str.strip() == cod_n1]
                    nom_n1 = cod_n1
                    costo_base = 0.0
                    peso_batch = 1.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n1 = str(r0[col_lista_nom_n1]).strip()
                        costo_base = extraer_num(r0[col_lista_costo_n1])
                        peso_val = extraer_num(r0[col_lista_peso_n1])
                        if peso_val > 0:
                            peso_batch = peso_val

                    inc_unitario = inc_total_receta / peso_batch
                    impactos_n1[cod_n1] = inc_unitario

                    filas_resumen_n1.append({
                        "Código": cod_n1,
                        "Producto / Subreceta": nom_n1,
                        "Cant. Insumo Usada": f"{cant_insumo_usada:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l1 = pd.DataFrame(filas_resumen_n1)

            # -------------------------------------------------------------
            # EVALUACIÓN NIVEL N2 (RELLENOS / INTERMEDIOS)
            # -------------------------------------------------------------
            impactos_n2 = {}
            filas_resumen_n2 = []

            for cod_receta, df_ing in df_recetas_n2.groupby(col_cod_receta_n2):
                cod_n2 = str(cod_receta).strip()
                if not cod_n2:
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0

                for _, row in df_ing.iterrows():
                    cod_comp = str(row[col_cod_insumo_n2]).strip()
                    cant = extraer_num(row[col_cant_n2])

                    # Directo por Materia Prima
                    if cod_comp == codigo_target:
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                    # A través de Subreceta N1
                    elif cod_comp in impactos_n1:
                        inc_total_receta += cant * impactos_n1[cod_comp]
                        cant_referencial += cant

                if inc_total_receta > 0:
                    row_lista = df_lista_n2[df_lista_n2[col_lista_cod_n2].astype(str).str.strip() == cod_n2]
                    nom_n2 = cod_n2
                    costo_base = 0.0
                    peso_batch = 1.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n2 = str(r0[col_lista_nom_n2]).strip()
                        costo_base = extraer_num(r0[col_lista_costo_n2])
                        peso_val = extraer_num(r0[col_lista_peso_n2])
                        if peso_val > 0:
                            peso_batch = peso_val

                    inc_unitario = inc_total_receta / peso_batch
                    impactos_n2[cod_n2] = inc_unitario

                    filas_resumen_n2.append({
                        "Código": cod_n2,
                        "Producto / Subreceta": nom_n2,
                        "Cant. Componente Usada": f"{cant_referencial:.3f}",
                        "Costo Actual Batch": f"Bs {costo_base:.2f}",
                        "Costo Simulado Batch": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l2 = pd.DataFrame(filas_resumen_n2)

            # -------------------------------------------------------------
            # EVALUACIÓN NIVEL N3 (PRODUCTOS FINALES)
            # -------------------------------------------------------------
            filas_resumen_n3 = []

            for cod_receta, df_ing in df_recetas_n3.groupby(col_cod_receta_n3):
                cod_n3 = str(cod_receta).strip()
                if not cod_n3:
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0

                for _, row in df_ing.iterrows():
                    cod_comp = str(row[col_cod_insumo_n3]).strip()
                    cant = extraer_num(row[col_cant_n3])

                    # Directo por Materia Prima / Empaque
                    if cod_comp == codigo_target:
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                    # Vía Subreceta N1
                    elif cod_comp in impactos_n1:
                        inc_total_receta += cant * impactos_n1[cod_comp]
                        cant_referencial += cant
                    # Vía Subreceta N2
                    elif cod_comp in impactos_n2:
                        inc_total_receta += cant * impactos_n2[cod_comp]
                        cant_referencial += cant

                if inc_total_receta > 0:
                    row_lista = df_lista_n3[df_lista_n3[col_lista_cod_n3].astype(str).str.strip() == cod_n3]
                    nom_n3 = cod_n3
                    costo_base = 0.0

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        nom_n3 = str(r0[col_lista_nom_n3]).strip()
                        costo_base = extraer_num(r0[col_lista_costo_n3])

                    filas_resumen_n3.append({
                        "Código": cod_n3,
                        "Producto Final": nom_n3,
                        "Cant. Componente Usada": f"{cant_referencial:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l3 = pd.DataFrame(filas_resumen_n3)

            # -------------------------------------------------------------
            # PRESENTACIÓN VISUAL
            # -------------------------------------------------------------
            st.subheader(
                f"📊 Comparativa Ejecutiva de Productos Afectados por: [{codigo_target}] {articulo_target}"
            )

            resumen_tabs1, resumen_tabs2, resumen_tabs3 = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Listas_N2)",
                    "🔴 Sub-Recetas Base (Lista_N1)",
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

    except Exception as e:
        st.error(f"Error durante el cálculo de la simulación: {e}")
