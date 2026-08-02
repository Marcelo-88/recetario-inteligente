import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Multicolumna Multinivel Exacta por Código ERP")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    df.columns = df.columns.str.strip()
    return df.fillna("")


def limpiar_codigo(val):
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
    except Exception:
        return 0.0


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
        busqueda = st.text_input(
            f"🔍 Buscar en {pestaña_activa} (código, nombre):"
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

elif modo_app == "💥 Simulación Financiera Multinivel":
    st.header("💥 Simulación Multicolumna (Materia Prima + Sub-Recetas N1/N2)")
    st.info(
        "Escanéo integral de columnas: detecta insumos directamente o integrados como sub-receta en N1, N2 y N3."
    )

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        col_nom_mermas = df_mermas.columns[0]
        col_cod_mermas = df_mermas.columns[1]

        def buscar_col_costo(df):
            for c in df.columns:
                if any(k in c.upper() for k in ["COSTO", "PRECIO", "VALOR"]):
                    return c
            return df.columns[-1]

        df_mermas["COD_CLEAN"] = df_mermas[col_cod_mermas].apply(limpiar_codigo)
        df_mermas_validos = df_mermas[df_mermas["COD_CLEAN"] != ""].copy()

        df_mermas_validos["COMBO_LABEL"] = (
            "["
            + df_mermas_validos["COD_CLEAN"]
            + "] "
            + df_mermas_validos[col_nom_mermas].astype(str).str.strip()
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

            codigo_target = datos_insumo["COD_CLEAN"]
            articulo_mostrar = str(datos_insumo[col_nom_mermas]).strip()

            col_costo_m = buscar_col_costo(df_mermas)
            costo_actual = extraer_num(datos_insumo[col_costo_m])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Código ERP Insumo", f"[{codigo_target}]")
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

            def preparar_lista(df):
                df_c = df.copy()
                df_c.columns = [c.strip() for c in df_c.columns]
                cols = list(df_c.columns)
                df_c["COD_KEY"] = df_c[cols[0]].apply(limpiar_codigo)
                df_c["NOM_KEY"] = df_c[cols[1]] if len(cols) > 1 else df_c[cols[0]]
                col_c = buscar_col_costo(df_c)
                df_c["COSTO_VAL"] = df_c[col_c].apply(extraer_num)
                return df_c

            l1 = preparar_lista(df_lista_n1)
            l2 = preparar_lista(df_lista_n2)
            l3 = preparar_lista(df_lista_n3)

            # --- EVALUAR RECETAS N1 ---
            impactos_n1 = {}
            filas_n1 = []

            for index, row in df_recetas_n1.iterrows():
                row_vals = [limpiar_codigo(v) for v in row.values]
                if not row_vals[0]:
                    continue

                receta_padre = row_vals[0]
                # Buscar en todas las celdas de la fila
                if codigo_target in row_vals[1:]:
                    cant_usada = 0.0
                    for v in row.values:
                        num = extraer_num(v)
                        if num > 0 and num < 1000:
                            cant_usada = num
                            break

                    inc_total = (cant_usada if cant_usada > 0 else 1.0) * dif_precio
                    impactos_n1[receta_padre] = (
                        impactos_n1.get(receta_padre, 0.0) + inc_total
                    )

            for cod_rec, inc_total in impactos_n1.items():
                master = l1[l1["COD_KEY"] == cod_rec]
                costo_base = master.iloc[0]["COSTO_VAL"] if not master.empty else 0.0
                nom_rec = master.iloc[0]["NOM_KEY"] if not master.empty else cod_rec
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n1.append({
                    "Código Receta N1": cod_rec,
                    "Nombre Sub-Receta": nom_rec,
                    "Costo Actual Batch": f"Bs {costo_base:.2f}",
                    "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- EVALUAR RECETAS N2 ---
            impactos_n2 = {}
            filas_n2 = []

            for index, row in df_recetas_n2.iterrows():
                row_vals = [limpiar_codigo(v) for v in row.values]
                if not row_vals[0]:
                    continue

                receta_padre = row_vals[0]
                inc_fila = 0.0

                if codigo_target in row_vals[1:]:
                    inc_fila += dif_precio

                for cod_n1, inc_n1 in impactos_n1.items():
                    if cod_n1 in row_vals[1:]:
                        inc_fila += inc_n1

                if inc_fila > 0:
                    impactos_n2[receta_padre] = (
                        impactos_n2.get(receta_padre, 0.0) + inc_fila
                    )

            for cod_rec, inc_total in impactos_n2.items():
                master = l2[l2["COD_KEY"] == cod_rec]
                costo_base = master.iloc[0]["COSTO_VAL"] if not master.empty else 0.0
                nom_rec = master.iloc[0]["NOM_KEY"] if not master.empty else cod_rec
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n2.append({
                    "Código Receta N2": cod_rec,
                    "Nombre Intermedio": nom_rec,
                    "Costo Actual Batch": f"Bs {costo_base:.2f}",
                    "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            # --- EVALUAR RECETAS N3 ---
            impactos_n3 = {}
            filas_n3 = []

            for index, row in df_recetas_n3.iterrows():
                row_vals = [str(v).strip() for v in row.values]
                row_codes = [limpiar_codigo(v) for v in row.values]

                # Nombre/Código del Producto N3 (Columna A)
                receta_padre_nombre = row_vals[0]
                if not receta_padre_nombre:
                    continue

                inc_fila = 0.0

                # Check 1: ¿Usa la Materia Prima directamente?
                if codigo_target in row_codes:
                    inc_fila += dif_precio

                # Check 2: ¿Usa alguna Sub-Receta N1 afectada?
                for cod_n1, inc_n1 in impactos_n1.items():
                    if cod_n1 in row_codes:
                        inc_fila += inc_n1

                # Check 3: ¿Usa alguna Sub-Receta N2 afectada?
                for cod_n2, inc_n2 in impactos_n2.items():
                    if cod_n2 in row_codes:
                        inc_fila += inc_n2

                if inc_fila > 0:
                    impactos_n3[receta_padre_nombre] = (
                        impactos_n3.get(receta_padre_nombre, 0.0) + inc_fila
                    )

            for nom_rec, inc_total in impactos_n3.items():
                # Buscar en Lista_N3 por coincidencia de nombre o código
                master = l3[
                    (l3["NOM_KEY"].str.strip().str.upper() == nom_rec.upper())
                    | (l3["COD_KEY"] == limpiar_codigo(nom_rec))
                ]

                costo_base = master.iloc[0]["COSTO_VAL"] if not master.empty else 0.0
                cod_show = master.iloc[0]["COD_KEY"] if not master.empty else "-"
                porc_var = (inc_total / costo_base * 100) if costo_base > 0 else 0.0

                filas_n3.append({
                    "Código Producto N3": cod_show,
                    "Nombre Producto Final": nom_rec,
                    "Costo Actual": f"Bs {costo_base:.2f}",
                    "Costo Simulado": f"Bs {(costo_base + inc_total):.2f}",
                    "Variación (Bs)": f"+Bs {inc_total:.2f}",
                    "Variación (%)": f"+{porc_var:.1f}%",
                })

            resumen_l1 = pd.DataFrame(filas_n1)
            resumen_l2 = pd.DataFrame(filas_n2)
            resumen_l3 = pd.DataFrame(filas_n3)

            st.subheader(
                f"📊 Resultados de Simulación para Insumo: [{codigo_target}] - {articulo_mostrar}"
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
