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
    return df


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
        "Visualiza de manera limpia el Costo Actual vs. Costo Simulado y su variación proporcional real en Productos Finales e Intermedios."
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
            df_mermas[col_codigo].astype(str)
            + " | "
            + df_mermas[col_articulo].astype(str)
            + " ("
            + df_mermas[col_recetario].astype(str)
            + ")"
        )

        lista_opciones = sorted(
            df_mermas["COMBO_MOSTRAR"].dropna().unique().tolist()
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
                        val = float(
                            str(datos_insumo[col])
                            .replace("Bs", "")
                            .replace(",", ".")
                            .strip()
                        )
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

            # --- FUNCIONES AUXILIARES DE LIMPIEZA Y CÁLCULO ---
            def extraer_num(val):
                try:
                    if pd.isna(val):
                        return 0.0
                    return float(
                        str(val)
                        .replace("Bs", "")
                        .replace(",", ".")
                        .strip()
                    )
                except:
                    return 0.0

            def obtener_columna_cantidad(df_receta):
                for col in df_receta.columns:
                    c_up = col.upper()
                    if any(k in c_up for k in ["CANT", "PESO", "NETO", "BRUTO", "KG", "GR"]) and not any(k in c_up for k in ["COSTO", "PRECIO", "TOTAL", "IMPORTE"]):
                        return col
                return df_receta.columns[2] if len(df_receta.columns) > 2 else df_receta.columns[-1]

            def verificar_ingrediente(row_str, busquedas):
                row_clean = str(row_str).lower()
                for b in busquedas:
                    b_clean = str(b).strip().lower()
                    if len(b_clean) > 2 and b_clean in row_clean:
                        return True
                return False

            claves_insumo = [codigo_val, recetario_val, articulo_val]

            # --- RASTREO Y CÁLCULO EN NIVEL 1 (Subrecetas Base) ---
            col_cant_n1 = obtener_columna_cantidad(df_recetas_n1)
            col_prod_n1 = df_recetas_n1.columns[0]

            impactos_n1 = {} # {nombre_subreceta: incremento_bs_unitario}
            filas_resumen_n1 = []

            for nombre_receta, df_ing in df_recetas_n1.groupby(col_prod_n1):
                inc_receta = 0.0
                cant_total_insumo = 0.0
                es_afectado = False

                for _, ing in df_ing.iterrows():
                    ing_texto = " ".join(ing.astype(str))
                    if verificar_ingrediente(ing_texto, claves_insumo):
                        cant = extraer_num(ing[col_cant_n1])
                        cant_total_insumo += cant
                        inc_receta += cant * dif_precio
                        es_afectado = True

                if es_afectado and inc_receta > 0:
                    impactos_n1[str(nombre_receta).strip()] = inc_receta
                    
                    # Buscar costo base en Lista_N1
                    row_lista = df_lista_n1[df_lista_n1[df_lista_n1.columns[0]].astype(str).str.strip() == str(nombre_receta).strip()]
                    costo_base = 0.0
                    estado = "Activo"
                    if not row_lista.empty:
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        if col_costo: costo_base = extraer_num(row_lista.iloc[0][col_costo])
                        if col_est: estado = row_lista.iloc[0][col_est]

                    filas_resumen_n1.append({
                        "Producto / Subreceta": nombre_receta,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_total_insumo:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_receta:.2f}",
                        "Variación (%)": f"+{(inc_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l1 = pd.DataFrame(filas_resumen_n1)

            # --- RASTREO Y CÁLCULO EN NIVEL 2 (Intermedios) ---
            col_cant_n2 = obtener_columna_cantidad(df_recetas_n2)
            col_prod_n2 = df_recetas_n2.columns[0]

            impactos_n2 = {}
            filas_resumen_n2 = []

            for nombre_receta, df_ing in df_recetas_n2.groupby(col_prod_n2):
                inc_receta = 0.0
                cant_usada_ref = 0.0
                es_afectado = False

                for _, ing in df_ing.iterrows():
                    ing_texto = " ".join(ing.astype(str))
                    cant = extraer_num(ing[col_cant_n2])

                    # 1. ¿Lleva el insumo directo?
                    if verificar_ingrediente(ing_texto, claves_insumo):
                        inc_receta += cant * dif_precio
                        cant_usada_ref += cant
                        es_afectado = True

                    # 2. ¿Lleva alguna subreceta N1 afectada?
                    for n1_nombre, n1_inc in impactos_n1.items():
                        if verificar_ingrediente(ing_texto, [n1_nombre]):
                            inc_receta += cant * n1_inc
                            cant_usada_ref += cant
                            es_afectado = True

                if es_afectado and inc_receta > 0:
                    impactos_n2[str(nombre_receta).strip()] = inc_receta

                    row_lista = df_lista_n2[df_lista_n2[df_lista_n2.columns[0]].astype(str).str.strip() == str(nombre_receta).strip()]
                    costo_base = 0.0
                    estado = "Activo"
                    if not row_lista.empty:
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        if col_costo: costo_base = extraer_num(row_lista.iloc[0][col_costo])
                        if col_est: estado = row_lista.iloc[0][col_est]

                    filas_resumen_n2.append({
                        "Producto / Subreceta": nombre_receta,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_usada_ref:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_receta:.2f}",
                        "Variación (%)": f"+{(inc_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
                    })

            resumen_l2 = pd.DataFrame(filas_resumen_n2)

            # --- RASTREO Y CÁLCULO EN NIVEL 3 (Productos Finales) ---
            col_cant_n3 = obtener_columna_cantidad(df_recetas_n3)
            col_prod_n3 = df_recetas_n3.columns[0]

            filas_resumen_n3 = []

            for nombre_receta, df_ing in df_recetas_n3.groupby(col_prod_n3):
                inc_receta = 0.0
                cant_usada_ref = 0.0
                es_afectado = False

                for _, ing in df_ing.iterrows():
                    ing_texto = " ".join(ing.astype(str))
                    cant = extraer_num(ing[col_cant_n3])

                    # 1. ¿Lleva el insumo directo?
                    if verificar_ingrediente(ing_texto, claves_insumo):
                        inc_receta += cant * dif_precio
                        cant_usada_ref += cant
                        es_afectado = True

                    # 2. ¿Lleva alguna subreceta N1 afectada?
                    for n1_nombre, n1_inc in impactos_n1.items():
                        if verificar_ingrediente(ing_texto, [n1_nombre]):
                            inc_receta += cant * n1_inc
                            cant_usada_ref += cant
                            es_afectado = True

                    # 3. ¿Lleva alguna subreceta N2 afectada?
                    for n2_nombre, n2_inc in impactos_n2.items():
                        if verificar_ingrediente(ing_texto, [n2_nombre]):
                            inc_receta += cant * n2_inc
                            cant_usada_ref += cant
                            es_afectado = True

                if es_afectado and inc_receta > 0:
                    row_lista = df_lista_n3[df_lista_n3[df_lista_n3.columns[0]].astype(str).str.strip() == str(nombre_receta).strip()]
                    costo_base = 0.0
                    estado = "Activo"
                    if not row_lista.empty:
                        col_costo = next((c for c in row_lista.columns if "COSTO" in c.upper()), None)
                        col_est = next((c for c in row_lista.columns if "ESTADO" in c.upper()), None)
                        if col_costo: costo_base = extraer_num(row_lista.iloc[0][col_costo])
                        if col_est: estado = row_lista.iloc[0][col_est]

                    filas_resumen_n3.append({
                        "Producto / Subreceta": nombre_receta,
                        "Estado": estado,
                        "Cantidad Usada": f"{cant_usada_ref:.3f}",
                        "Costo Actual": f"Bs {costo_base:.2f}",
                        "Costo Simulado": f"Bs {(costo_base + inc_receta):.2f}",
                        "Variación (Bs)": f"+Bs {inc_receta:.2f}",
                        "Variación (%)": f"+{(inc_receta / costo_base * 100 if costo_base > 0 else 0):.1f}%"
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
                    st.info("No se encontraron productos finales afectados directamente ni por subrecetas.")

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
