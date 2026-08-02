import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Multilevel Dinámica por Encabezados de Columna")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    # Limpiamos nombres de columnas quitando espacios extras
    df.columns = [str(c).strip() for c in df.columns]
    return df.fillna("")


def normalizar_cod(val):
    """Normaliza códigos quitando guiones y espacios para comparaciones súper robustas."""
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return re.sub(r"[^A-Za-z0-9]", "", v).upper()


def limpiar_cod_mostrar(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return v.upper()


def extraer_num(val):
    if pd.isna(val) or val == "":
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def buscar_columna_por_patron(df, patrones):
    """Busca dinámicamente el nombre exacto de la columna que coincida con algún patrón."""
    for col in df.columns:
        col_clean = str(col).strip().upper()
        for pat in patrones:
            if pat.upper() in col_clean:
                return col
    return None


# -------------------------------------------------------------
# MÓDULOS
# -------------------------------------------------------------
st.sidebar.header("🕹️ Módulos")
modo_app = st.sidebar.radio(
    "Selecciona la función:",
    ["📋 Explorador de Tablas", "💥 Simulación Financiera Multinivel"],
)
st.sidebar.divider()

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
        busqueda = st.text_input(f"🔍 Buscar en {pestaña_activa}:")

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

elif modo_app == "💥 Simulación Financiera Multinivel":
    st.header("💥 Simulación Multinivel por Mapeo Dinámico de Columnas")
    st.info(
        "Lógica estricta: Multiplicación de Cantidades Consumidas × Incremento del Insumo Base"
    )

    try:
        # Carga de pestañas
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # Mapeo Mermas_Costos
        col_nom_m = df_mermas.columns[0]
        col_cod_m = df_mermas.columns[1]
        col_costo_m = buscar_columna_por_patron(
            df_mermas, ["COSTO", "PRECIO", "VALOR"]
        ) or df_mermas.columns[-1]

        df_mermas["COD_RAW"] = df_mermas[col_cod_m].apply(limpiar_cod_mostrar)
        df_mermas["COD_NORM"] = df_mermas[col_cod_m].apply(normalizar_cod)

        df_mermas_validos = df_mermas[df_mermas["COD_NORM"] != ""].copy()
        df_mermas_validos["COMBO_LABEL"] = (
            "["
            + df_mermas_validos["COD_RAW"]
            + "] "
            + df_mermas_validos[col_nom_m].astype(str).str.strip()
        )

        lista_opciones = sorted(
            df_mermas_validos["COMBO_LABEL"].unique().tolist()
        )

        st.subheader("1️⃣ Selecciona el Código del Insumo a Simular")
        opcion_elegida = st.selectbox(
            "Buscar por Código ERP o Nombre:", lista_opciones
        )

        if opcion_elegida:
            datos_insumo = df_mermas_validos[
                df_mermas_validos["COMBO_LABEL"] == opcion_elegida
            ].iloc[0]

            codigo_target_norm = datos_insumo["COD_NORM"]
            codigo_target_raw = datos_insumo["COD_RAW"]
            articulo_mostrar = str(datos_insumo[col_nom_m]).strip()

            costo_actual = extraer_num(datos_insumo[col_costo_m])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Código ERP Insumo", f"[{codigo_target_raw}]")
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
                porc_inc = (
                    (dif_precio / costo_actual * 100) if costo_actual > 0 else 0.0
                )
                st.metric(
                    "Incremento Unitario Insumo",
                    f"+Bs {dif_precio:.2f}",
                    delta=f"{porc_inc:.1f}%",
                )

            st.divider()

            # Helper para consultar precios en Listas Máster
            def consultar_master(df_lista, cod_o_nom):
                col_cod = df_lista.columns[0]
                col_nom = df_lista.columns[1] if len(df_lista.columns) > 1 else col_cod
                col_costo = buscar_columna_por_patron(
                    df_lista, ["COSTO", "PRECIO", "VALOR"]
                ) or df_lista.columns[-1]

                query_norm = normalizar_cod(cod_o_nom)
                query_str = str(cod_o_nom).strip().upper()

                match = df_lista[
                    (df_lista[col_cod].apply(normalizar_cod) == query_norm)
                    | (df_lista[col_nom].astype(str).str.strip().str.upper() == query_str)
                ]

                if not match.empty:
                    c_base = extraer_num(match.iloc[0][col_costo])
                    c_show = limpiar_cod_mostrar(match.iloc[0][col_cod])
                    n_show = str(match.iloc[0][col_nom]).strip()
                    return c_base, c_show, n_show
                return 0.0, str(cod_o_nom).strip(), str(cod_o_nom).strip()

            # --- EVALUAR RECETAS N1 ---
            impactos_n1 = {}  # {cod_norm_n1: inc_total_bs}
            filas_n1 = []

            for _, row in df_recetas_n1.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue

                receta_padre_norm = normalizar_cod(vals[0])
                if not receta_padre_norm:
                    continue

                # Recorremos la fila buscando si el insumo está en alguna celda
                row_norms = [normalizar_cod(v) for v in vals]
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    # Buscamos la cantidad asociada en la celda contigua o siguiente numérica
                    cant = 0.0
                    for k in range(idx + 1, min(idx + 4, len(vals))):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break

                    inc = (cant if cant > 0 else 1.0) * dif_precio
                    impactos_n1[receta_padre_norm] = (
                        impactos_n1.get(receta_padre_norm, 0.0) + inc
                    )

            for cod_norm, inc_total in impactos_n1.items():
                costo_base, cod_show, nom_show = consultar_master(df_lista_n1, cod_norm)
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n1.append({
                    "Código Receta N1": cod_show,
                    "Nombre Sub-Receta": nom_show,
                    "Costo Actual Batch": f"Bs {costo_base:.2f}",
                    "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- EVALUAR RECETAS N2 ---
            impactos_n2 = {}
            filas_n2 = []

            for _, row in df_recetas_n2.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue

                receta_padre_norm = normalizar_cod(vals[0])
                if not receta_padre_norm:
                    continue

                row_norms = [normalizar_cod(v) for v in vals]
                inc_fila = 0.0

                # Check 1: Insumo directo en N2
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, min(idx + 4, len(vals))):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_fila += (cant if cant > 0 else 1.0) * dif_precio

                # Check 2: Sub-receta N1 afectada en N2
                for cod_n1_norm, inc_n1 in impactos_n1.items():
                    if cod_n1_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n1_norm) + 1
                        cant = 0.0
                        for k in range(idx + 1, min(idx + 4, len(vals))):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant = num
                                break
                        inc_fila += (cant if cant > 0 else 1.0) * inc_n1

                if inc_fila > 0:
                    impactos_n2[receta_padre_norm] = (
                        impactos_n2.get(receta_padre_norm, 0.0) + inc_fila
                    )

            for cod_norm, inc_total in impactos_n2.items():
                costo_base, cod_show, nom_show = consultar_master(df_lista_n2, cod_norm)
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n2.append({
                    "Código Receta N2": cod_show,
                    "Nombre Intermedio": nom_show,
                    "Costo Actual Batch": f"Bs {costo_base:.2f}",
                    "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- EVALUAR RECETAS N3 ---
            impactos_n3 = {}
            filas_n3 = []

            for _, row in df_recetas_n3.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue

                nombre_o_cod_n3 = vals[0]
                row_norms = [normalizar_cod(v) for v in vals]

                inc_fila = 0.0

                # 1. MP Directa en N3
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, min(idx + 4, len(vals))):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_fila += (cant if cant > 0 else 1.0) * dif_precio

                # 2. Sub-receta N1 en N3
                for cod_n1_norm, inc_n1 in impactos_n1.items():
                    if cod_n1_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n1_norm) + 1
                        cant = 0.0
                        for k in range(idx + 1, min(idx + 4, len(vals))):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant = num
                                break
                        inc_fila += (cant if cant > 0 else 1.0) * inc_n1

                # 3. Sub-receta N2 en N3
                for cod_n2_norm, inc_n2 in impactos_n2.items():
                    if cod_n2_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n2_norm) + 1
                        cant = 0.0
                        for k in range(idx + 1, min(idx + 4, len(vals))):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant = num
                                break
                        inc_fila += (cant if cant > 0 else 1.0) * inc_n2

                if inc_fila > 0:
                    impactos_n3[nombre_o_cod_n3] = (
                        impactos_n3.get(nombre_o_cod_n3, 0.0) + inc_fila
                    )

            for nom_o_cod, inc_total in impactos_n3.items():
                costo_base, cod_show, nom_show = consultar_master(df_lista_n3, nom_o_cod)
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n3.append({
                    "Código Producto N3": cod_show,
                    "Nombre Producto Final": nom_show,
                    "Costo Actual": f"Bs {costo_base:.2f}",
                    "Costo Simulado": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            resumen_l1 = pd.DataFrame(filas_n1)
            resumen_l2 = pd.DataFrame(filas_n2)
            resumen_l3 = pd.DataFrame(filas_n3)

            st.subheader(
                f"📊 Resultados de Simulación para Insumo: [{codigo_target_raw}] - {articulo_mostrar}"
            )

            t3, t2, t1 = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Listas_N2)",
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
