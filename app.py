import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera - Impacto Unitario por Kilo/Unidad")
st.divider()

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
    patron = f"COSTO R{nivel}"
    for col in df.columns:
        if patron in str(col).strip().upper():
            return col
    for col in df.columns:
        c_u = str(col).upper()
        if "COSTO" in c_u and "PRECIO" not in c_u:
            return col
    return df.columns[-1]


def obtener_rendimiento_total_batch(row_values):
    cantidades = []
    for val in row_values[1:]:
        num = extraer_num(val)
        if num > 0:
            cantidades.append(num)
    total = sum(cantidades)
    return total if total > 0 else 1.0


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
    st.header("💥 Simulación Financiera Multinivel Proporcional")
    st.info("Visualización estandarizada por Kilo / Unidad para N1, N2 y N3")

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        col_nom_m = df_mermas.columns[0]
        col_cod_m = df_mermas.columns[1]
        col_costo_m = buscar_columna_mermas(df_mermas)

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

            costo_actual_unitario = extraer_num(datos_insumo[col_costo_m])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Código ERP Insumo", f"[{codigo_target_raw}]")
                st.caption(f"Insumo: {articulo_mostrar}")
            with c2:
                nuevo_precio_unitario = st.number_input(
                    "Nuevo precio simulado por Litro/Kg (Bs):",
                    min_value=0.0,
                    value=float(costo_actual_unitario + 1.00)
                    if costo_actual_unitario > 0
                    else 20.0,
                    step=0.10,
                )
            with c3:
                dif_precio_unitario = (
                    nuevo_precio_unitario - costo_actual_unitario
                )
                porc_inc = (
                    (dif_precio_unitario / costo_actual_unitario * 100)
                    if costo_actual_unitario > 0
                    else 0.0
                )
                st.metric(
                    "Variación Directa",
                    f"+Bs {dif_precio_unitario:.2f}",
                    delta=f"{porc_inc:.1f}%",
                )

            st.caption(
                f"📌 Costo base en Mermas_Costos: **Bs {costo_actual_unitario:.2f}**"
            )
            st.divider()

            def consultar_master_gen(df_lista, busqueda_str, nivel="3"):
                col_nom = df_lista.columns[0]
                col_cod = (
                    df_lista.columns[1] if len(df_lista.columns) > 1 else col_nom
                )
                col_costo = buscar_columna_costo_master(df_lista, nivel)

                query_norm = normalizar_cod(busqueda_str)
                query_clean = str(busqueda_str).strip().upper()

                # Búsqueda flexible por código o por nombre
                match = df_lista[
                    (df_lista[col_cod].apply(normalizar_cod) == query_norm)
                    | (
                        df_lista[col_nom]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        == query_clean
                    )
                    | (
                        df_lista[col_cod]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        == query_clean
                    )
                ]

                if not match.empty:
                    c_base = extraer_num(match.iloc[0][col_costo])
                    c_show = limpiar_cod_mostrar(match.iloc[0][col_cod])
                    n_show = str(match.iloc[0][col_nom]).strip()
                    return c_base, c_show, n_show

                return 0.0, "-", str(busqueda_str).strip()

            # --- 1. RECETAS N1 (Sub-Recetas Base) ---
            impactos_n1_kilo = {}

            for _, row in df_recetas_n1.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue
                receta_padre_norm = normalizar_cod(vals[0])
                if not receta_padre_norm:
                    continue

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

                    # Guardamos la variación expresada por Kilo / Unidad
                    var_por_kilo = inc_batch / rendimiento_batch
                    impactos_n1_kilo[receta_padre_norm] = (
                        impactos_n1_kilo.get(receta_padre_norm, 0.0)
                        + var_por_kilo
                    )

            filas_n1 = []
            for cod_norm, var_kilo in impactos_n1_kilo.items():
                costo_base_kg, cod_show, nom_show = consultar_master_gen(
                    df_lista_n1, cod_norm, "1"
                )
                costo_sim_kg = costo_base_kg + var_kilo
                porc_var = (
                    (var_kilo / costo_base_kg * 100)
                    if costo_base_kg > 0
                    else 0.0
                )

                filas_n1.append({
                    "Código N1": cod_show,
                    "Nombre Sub-Receta": nom_show,
                    "Costo Actual / Kg": f"Bs {costo_base_kg:.2f}",
                    "Costo Simulado / Kg": f"Bs {costo_sim_kg:.2f}",
                    "Variación / Kg (Bs)": f"+Bs {var_kilo:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- 2. RECETAS N2 (Rellenos / Intermedios) ---
            impactos_n2_kilo = {}

            for _, row in df_recetas_n2.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue
                receta_padre_norm = normalizar_cod(vals[0])
                if not receta_padre_norm:
                    continue

                row_norms = [normalizar_cod(v) for v in vals]
                inc_batch_n2 = 0.0

                # Aceite Directo en N2
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, len(vals)):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_batch_n2 += cant * dif_precio_unitario

                # N1 consumido en N2
                for cod_n1_norm, var_kilo_n1 in impactos_n1_kilo.items():
                    if cod_n1_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n1_norm) + 1
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
                    impactos_n2_kilo[receta_padre_norm] = (
                        impactos_n2_kilo.get(receta_padre_norm, 0.0)
                        + var_por_kilo_n2
                    )

            filas_n2 = []
            for cod_norm, var_kilo in impactos_n2_kilo.items():
                costo_base_kg, cod_show, nom_show = consultar_master_gen(
                    df_lista_n2, cod_norm, "2"
                )
                costo_sim_kg = costo_base_kg + var_kilo
                porc_var = (
                    (var_kilo / costo_base_kg * 100)
                    if costo_base_kg > 0
                    else 0.0
                )

                filas_n2.append({
                    "Código N2": cod_show,
                    "Nombre Intermedio": nom_show,
                    "Costo Actual / Kg": f"Bs {costo_base_kg:.2f}",
                    "Costo Simulado / Kg": f"Bs {costo_sim_kg:.2f}",
                    "Variación / Kg (Bs)": f"+Bs {var_kilo:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- 3. RECETAS N3 (Productos Finales) ---
            impactos_n3 = {}
            for _, row in df_recetas_n3.iterrows():
                vals = [str(v).strip() for v in row.values]
                if not vals or not vals[0]:
                    continue
                nombre_o_cod_n3 = vals[0]
                row_norms = [normalizar_cod(v) for v in vals]

                inc_producto_final = 0.0

                # Aceite Directo en N3
                if codigo_target_norm in row_norms[1:]:
                    idx = row_norms[1:].index(codigo_target_norm) + 1
                    cant = 0.0
                    for k in range(idx + 1, len(vals)):
                        num = extraer_num(vals[k])
                        if num > 0:
                            cant = num
                            break
                    inc_producto_final += cant * dif_precio_unitario

                # N1 consumido en N3
                for cod_n1_norm, var_kilo_n1 in impactos_n1_kilo.items():
                    if cod_n1_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n1_norm) + 1
                        cant_n1 = 0.0
                        for k in range(idx + 1, len(vals)):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant_n1 = num
                                break
                        inc_producto_final += cant_n1 * var_kilo_n1

                # N2 consumido en N3
                for cod_n2_norm, var_kilo_n2 in impactos_n2_kilo.items():
                    if cod_n2_norm in row_norms[1:]:
                        idx = row_norms[1:].index(cod_n2_norm) + 1
                        cant_n2 = 0.0
                        for k in range(idx + 1, len(vals)):
                            num = extraer_num(vals[k])
                            if num > 0:
                                cant_n2 = num
                                break
                        inc_producto_final += cant_n2 * var_kilo_n2

                if inc_producto_final > 0:
                    impactos_n3[nombre_o_cod_n3] = (
                        impactos_n3.get(nombre_o_cod_n3, 0.0)
                        + inc_producto_final
                    )

            filas_n3 = []
            for nom_o_cod, inc_total in impactos_n3.items():
                costo_base, cod_show, nom_show = consultar_master_gen(
                    df_lista_n3, nom_o_cod, "3"
                )
                porc_var = (
                    (inc_total / costo_base * 100) if costo_base > 0 else 0.0
                )

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

            st.subheader(
                f"📊 Resultados Simulación: [{codigo_target_raw}] - {articulo_mostrar}"
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
                st.write(
                    f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}"
                )
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
