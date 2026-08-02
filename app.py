import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Ejecutiva y Efecto Dominó Exacto (Lista N1 ➔ N2 ➔ N3)")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=60)
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
            f"🔍 Buscar en {pestaña_activa} (receta, código, ingrediente):"
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
    st.header("💥 Simulación de Impacto en Costos (Vista Ejecutiva)")
    st.info(
        "Visualiza el Costo Actual vs. Costo Simulado y su variación proporcional real en Productos Finales e Intermedios."
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

        col_recetario = df_mermas.columns[0]
        col_codigo = df_mermas.columns[1]
        col_articulo = df_mermas.columns[2]

        df_mermas["COMBO_MOSTRAR"] = (
            df_mermas[col_codigo].astype(str).str.strip()
            + " | "
            + df_mermas[col_articulo].astype(str).str.strip()
            + " ("
            + df_mermas[col_recetario].astype(str).str.strip()
            + ")"
        )

        lista_opciones = sorted(
            [x for x in df_mermas["COMBO_MOSTRAR"].dropna().unique() if len(str(x).strip()) > 5]
        )

        st.subheader("1️⃣ Selecciona la Materia Prima / Empaque")
        opcion_elegida = st.selectbox(
            "Buscar Insumo [ Código ERP | Artículo ERP (Recetario) ]:",
            lista_opciones,
        )

        if opcion_elegida:
            datos_insumo = df_mermas[
                df_mermas["COMBO_MOSTRAR"] == opcion_elegida
            ].iloc[0]

            codigo_val = str(datos_insumo[col_codigo]).strip()
            articulo_val = str(datos_insumo[col_articulo]).strip()
            recetario_val = str(datos_insumo[col_recetario]).strip()

            costo_actual = 0.0
            for col in df_mermas.columns:
                if "COSTO" in col.upper() or "PRECIO" in col.upper():
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
                st.metric("Precio Actual Base", f"Bs {costo_actual:.2f}")
            with c2:
                nuevo_precio = st.number_input(
                    "Nuevo precio simulado (Bs):",
                    min_value=0.0,
                    value=float(costo_actual * 1.20) if costo_actual > 0 else 10.0,
                    step=1.0,
                )
            with c3:
                dif_precio = nuevo_precio - costo_actual
                porc_inc = (
                    (dif_precio / costo_actual) * 100 if costo_actual > 0 else 0
                )
                st.metric(
                    "Incremento Simulado / Unidad Base",
                    f"+Bs {dif_precio:.2f}",
                    delta=f"{porc_inc:.1f}%",
                )

            st.divider()

            # --- FUNCIONES AUXILIARES ---
            def extraer_num(val):
                if pd.isna(val) or val == "":
                    return 0.0
                try:
                    cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
                    return float(cleaned) if cleaned else 0.0
                except:
                    return 0.0

            def obtener_col_cantidad(df):
                for c in df.columns:
                    c_up = c.upper()
                    if any(k in c_up for k in ["CANT", "PESO", "NETO", "BRUTO", "KG", "GR"]) and not any(k in c_up for k in ["COSTO", "PRECIO", "TOTAL", "IMPORTE", "UNIDAD"]):
                        return c
                return df.columns[2] if len(df.columns) > 2 else df.columns[-1]

            def match_ingrediente(row_str, codigo_erp, nombre_exacto):
                texto = str(row_str).lower()
                if codigo_erp and len(codigo_erp) > 2 and re.search(rf"\b{re.escape(codigo_erp.lower())}\b", texto):
                    return True
                if nombre_exacto and len(nombre_exacto) > 3 and nombre_exacto.lower() in texto:
                    return True
                return False

            # --- N1: SUBRECETAS BASE ---
            col_prod_n1 = df_recetas_n1.columns[0]
            col_cant_n1 = obtener_col_cantidad(df_recetas_n1)

            impactos_n1_unitario = {} # {nombre_subreceta: incremento_bs_unitario}
            filas_resumen_n1 = []

            for nombre_receta, df_ing in df_recetas_n1.groupby(col_prod_n1):
                nom_n1 = str(nombre_receta).strip()
                if not nom_n1:
                    continue

                inc_total_receta = 0.0
                cant_insumo_usada = 0.0
                contiene_insumo = False

                for _, row in df_ing.iterrows():
                    fila_txt = " ".join([str(v) for v in row.values if pd.notna(v)])
                    if match_ingrediente(fila_txt, codigo_val, recetario_val) or match_ingrediente(fila_txt, codigo_val, articulo_val):
                        cant = extraer_num(row[col_cant_n1])
                        cant_insumo_usada += cant
                        inc_total_receta += cant * dif_precio
                        contiene_insumo = True

                if contiene_insumo and inc_total_receta > 0:
                    row_lista = df_lista_n1[df_lista_n1[df_lista_n1.columns[0]].astype(str).str.strip() == nom_n1]
                    costo_base = 0.0
                    peso_batch = 1.0
                    estado = "Activo"

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        col_peso = next((c for c in row_lista.columns if any(k in c.upper() for k in ["PESO", "RND", "REND", "BATCH"])), None)

                        if col_costo: costo_base = extraer_num(r0[col_costo])
                        if col_est: estado = str(r0[col_est])
                        if col_peso and extraer_num(r0[col_peso]) > 0: peso_batch = extraer_num(r0[col_peso])

                    # Incremento unitario por kg/unidad de subreceta
                    inc_unitario = inc_total_receta / peso_batch if peso_batch > 0 else inc_total_receta
                    impactos_n1_unitario[nom_n1] = inc_unitario

                    filas_resumen_n1.append({
                        "Producto / Subreceta": nom_n1,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_insumo_usada:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l1 = pd.DataFrame(filas_resumen_n1)

            # --- N2: INTERMEDIOS / RELLENOS ---
            col_prod_n2 = df_recetas_n2.columns[0]
            col_cant_n2 = obtener_col_cantidad(df_recetas_n2)

            impactos_n2_unitario = {}
            filas_resumen_n2 = []

            for nombre_receta, df_ing in df_recetas_n2.groupby(col_prod_n2):
                nom_n2 = str(nombre_receta).strip()
                if not nom_n2:
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0
                es_afectado = False

                for _, row in df_ing.iterrows():
                    fila_txt = " ".join([str(v) for v in row.values if pd.notna(v)])
                    cant = extraer_num(row[col_cant_n2])

                    # 1. Insumo directo
                    if match_ingrediente(fila_txt, codigo_val, recetario_val) or match_ingrediente(fila_txt, codigo_val, articulo_val):
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                        es_afectado = True
                    else:
                        # 2. Subreceta N1
                        for n1_nom, n1_inc_u in impactos_n1_unitario.items():
                            if n1_nom.lower() in fila_txt.lower():
                                inc_total_receta += cant * n1_inc_u
                                cant_referencial += cant
                                es_afectado = True
                                break

                if es_afectado and inc_total_receta > 0:
                    row_lista = df_lista_n2[df_lista_n2[df_lista_n2.columns[0]].astype(str).str.strip() == nom_n2]
                    costo_base = 0.0
                    peso_batch = 1.0
                    estado = "Activo"

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        col_peso = next((c for c in row_lista.columns if any(k in c.upper() for k in ["PESO", "RND", "REND", "BATCH"])), None)

                        if col_costo: costo_base = extraer_num(r0[col_costo])
                        if col_est: estado = str(r0[col_est])
                        if col_peso and extraer_num(r0[col_peso]) > 0: peso_batch = extraer_num(r0[col_peso])

                    inc_unitario = inc_total_receta / peso_batch if peso_batch > 0 else inc_total_receta
                    impactos_n2_unitario[nom_n2] = inc_unitario

                    filas_resumen_n2.append({
                        "Producto / Subreceta": nom_n2,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_referencial:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l2 = pd.DataFrame(filas_resumen_n2)

            # --- N3: PRODUCTOS FINALES ---
            col_prod_n3 = df_recetas_n3.columns[0]
            col_cant_n3 = obtener_col_cantidad(df_recetas_n3)

            filas_resumen_n3 = []

            for nombre_receta, df_ing in df_recetas_n3.groupby(col_prod_n3):
                nom_n3 = str(nombre_receta).strip()
                if not nom_n3:
                    continue

                inc_total_receta = 0.0
                cant_referencial = 0.0
                es_afectado = False

                for _, row in df_ing.iterrows():
                    fila_txt = " ".join([str(v) for v in row.values if pd.notna(v)])
                    cant = extraer_num(row[col_cant_n3])

                    # 1. Insumo directo
                    if match_ingrediente(fila_txt, codigo_val, recetario_val) or match_ingrediente(fila_txt, codigo_val, articulo_val):
                        inc_total_receta += cant * dif_precio
                        cant_referencial += cant
                        es_afectado = True
                    else:
                        # 2. Subreceta N1
                        match_n1 = False
                        for n1_nom, n1_inc_u in impactos_n1_unitario.items():
                            if n1_nom.lower() in fila_txt.lower():
                                inc_total_receta += cant * n1_inc_u
                                cant_referencial += cant
                                es_afectado = True
                                match_n1 = True
                                break

                        # 3. Subreceta N2 (solo si no matcheó N1)
                        if not match_n1:
                            for n2_nom, n2_inc_u in impactos_n2_unitario.items():
                                if n2_nom.lower() in fila_txt.lower():
                                    inc_total_receta += cant * n2_inc_u
                                    cant_referencial += cant
                                    es_afectado = True
                                    break

                if es_afectado and inc_total_receta > 0:
                    row_lista = df_lista_n3[df_lista_n3[df_lista_n3.columns[0]].astype(str).str.strip() == nom_n3]
                    costo_base = 0.0
                    estado = "Activo"

                    if not row_lista.empty:
                        r0 = row_lista.iloc[0]
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        if col_costo: costo_base = extraer_num(r0[col_costo])
                        if col_est: estado = str(r0[col_est])

                    filas_resumen_n3.append({
                        "Producto / Subreceta": nom_n3,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_referencial:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_total_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_total_receta:.2f}",
                        "Variación (%)": f"+{(inc_total_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l3 = pd.DataFrame(filas_resumen_n3)

            # --- PRESENTACIÓN VISUAL ---
            st.subheader(
                f"📊 Comparativa Ejecutiva de Productos Afectados por: **{recetario_val}** ({codigo_val})"
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
                    st.info("No se encontraron productos finales afectados.")

            with resumen_tabs2:
                st.write(f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}")
                if not resumen_l2.empty:
                    st.dataframe(resumen_l2, use_container_width=True)
                else:
                    st.info("No se encontraron productos intermedios N2 afectados.")

            with resumen_tabs3:
                st.write(f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}")
                if not resumen_l1.empty:
                    st.dataframe(resumen_l1, use_container_width=True)
                else:
                    st.info("No se encontraron sub-recetas N1 afectadas.")

    except Exception as e:
        st.error(f"Error durante el cálculo de la simulación: {e}")
