import re
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Multinivel Exacta por Código ERP")
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
    st.header("💥 Simulación de Impacto por Código ERP")
    st.info(
        "Trazabilidad 100% relacional: Código Materia Prima ➔ Recetas N1 ➔ Recetas N2 ➔ Productos N3"
    )

    try:
        df_mermas = cargar_pestaña("Mermas_Costos")
        df_recetas_n1 = cargar_pestaña("Recetas_N1")
        df_recetas_n2 = cargar_pestaña("Recetas_N2")
        df_recetas_n3 = cargar_pestaña("Recetas_N3")

        df_lista_n1 = cargar_pestaña("Lista_N1")
        df_lista_n2 = cargar_pestaña("Listas_N2")
        df_lista_n3 = cargar_pestaña("Lista_N3")

        # Asignación segura por índice (Col A: Nombre, Col B: Código ERP)
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

            # Normalizar Tablas
            def preparar_df(df):
                df_copy = df.copy()
                df_copy.columns = [c.strip() for c in df_copy.columns]
                df_copy["RECETA_COD"] = df_copy.iloc[:, 0].apply(limpiar_codigo)
                df_copy["INSUMO_COD"] = df_copy.iloc[:, 1].apply(limpiar_codigo)
                return df_copy

            r1 = preparar_df(df_recetas_n1)
            r2 = preparar_df(df_recetas_n2)
            r3 = preparar_df(df_recetas_n3)

            def preparar_lista(df):
                df_copy = df.copy()
                df_copy.columns = [c.strip() for c in df_copy.columns]
                df_copy["COD_KEY"] = df_copy.iloc[:, 0].apply(limpiar_codigo)
                col_c = buscar_col_costo(df_copy)
                df_copy["COSTO_VAL"] = df_copy[col_c].apply(extraer_num)
                return df_copy

            l1 = preparar_lista(df_lista_n1)
            l2 = preparar_lista(df_lista_n2)
            l3 = preparar_lista(df_lista_n3)

            # --- EVALUACIÓN NIVEL N1 ---
            impactos_n1 = {}
            filas_n1 = []

            for cod_rec, group in r1.groupby("RECETA_COD"):
                if not cod_rec:
                    continue

                match_insumo = group[group["INSUMO_COD"] == codigo_target]
                if not match_insumo.empty:
                    cant_usada = sum(
                        match_insumo.iloc[:, 2].apply(extraer_num)
                    )
                    inc_total = cant_usada * dif_precio

                    impactos_n1[cod_rec] = inc_total

                    row_master = l1[l1["COD_KEY"] == cod_rec]
                    costo_base = (
                        row_master.iloc[0]["COSTO_VAL"]
                        if not row_master.empty
                        else 0.0
                    )
                    nombre_rec = (
                        row_master.iloc[0].iloc[1]
                        if not row_master.empty
                        else cod_rec
                    )

                    porc_var = (
                        (inc_total / costo_base * 100) if costo_base > 0 else 0.0
                    )

                    filas_n1.append(
                        {
                            "Código Receta": cod_rec,
                            "Nombre Receta": nombre_rec,
                            "Cant. Insumo Usada": f"{cant_usada:.3f}",
                            "Costo Actual Batch": f"Bs {costo_base:.2f}",
                            "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                            "Variación (Bs)": f"+Bs {inc_total:.2f}",
                            "Variación (%)": f"+{porc_var:.1f}%",
                        }
                    )

            # --- EVALUACIÓN NIVEL N2 ---
            impactos_n2 = {}
            filas_n2 = []

            for cod_rec, group in r2.groupby("RECETA_COD"):
                if not cod_rec:
                    continue

                inc_total = 0.0
                cant_usada = 0.0

                for _, row in group.iterrows():
                    ins_cod = row["INSUMO_COD"]
                    cant = extraer_num(row.iloc[2])

                    if ins_cod == codigo_target:
                        inc_total += cant * dif_precio
                        cant_usada += cant
                    elif ins_cod in impactos_n1:
                        inc_total += cant * impactos_n1[ins_cod]
                        cant_usada += cant

                if inc_total > 0:
                    impactos_n2[cod_rec] = inc_total

                    row_master = l2[l2["COD_KEY"] == cod_rec]
                    costo_base = (
                        row_master.iloc[0]["COSTO_VAL"]
                        if not row_master.empty
                        else 0.0
                    )
                    nombre_rec = (
                        row_master.iloc[0].iloc[1]
                        if not row_master.empty
                        else cod_rec
                    )

                    porc_var = (
                        (inc_total / costo_base * 100) if costo_base > 0 else 0.0
                    )

                    filas_n2.append(
                        {
                            "Código Receta N2": cod_rec,
                            "Nombre Receta": nombre_rec,
                            "Cant. Componente Usada": f"{cant_usada:.3f}",
                            "Costo Actual Batch": f"Bs {costo_base:.2f}",
                            "Costo Simulado Batch": f"Bs {(costo_base + inc_total):.2f}",
                            "Variación (Bs)": f"+Bs {inc_total:.2f}",
                            "Variación (%)": f"+{porc_var:.1f}%",
                        }
                    )

            # --- EVALUACIÓN NIVEL N3 ---
            filas_n3 = []

            for cod_rec, group in r3.groupby("RECETA_COD"):
                if not cod_rec:
                    continue

                inc_total = 0.0
                cant_usada = 0.0

                for _, row in group.iterrows():
                    ins_cod = row["INSUMO_COD"]
                    cant = extraer_num(row.iloc[2])

                    if ins_cod == codigo_target:
                        inc_total += cant * dif_precio
                        cant_usada += cant
                    elif ins_cod in impactos_n1:
                        inc_total += cant * impactos_n1[ins_cod]
                        cant_usada += cant
                    elif ins_cod in impactos_n2:
                        inc_total += cant * impactos_n2[ins_cod]
                        cant_usada += cant

                if inc_total > 0:
                    row_master = l3[l3["COD_KEY"] == cod_rec]
                    costo_base = (
                        row_master.iloc[0]["COSTO_VAL"]
                        if not row_master.empty
                        else 0.0
                    )
                    nombre_rec = (
                        row_master.iloc[0].iloc[1]
                        if not row_master.empty
                        else cod_rec
                    )

                    porc_var = (
                        (inc_total / costo_base * 100) if costo_base > 0 else 0.0
                    )

                    filas_n3.append(
                        {
                            "Código Producto N3": cod_rec,
                            "Nombre Producto": nombre_rec,
                            "Cant. Componente Usada": f"{cant_usada:.3f}",
                            "Costo Actual": f"Bs {costo_base:.2f}",
                            "Costo Simulado": f"Bs {(costo_base + inc_total):.2f}",
                            "Variación (Bs)": f"+Bs {inc_total:.2f}",
                            "Variación (%)": f"+{porc_var:.1f}%",
                        }
                    )

            resumen_l1 = pd.DataFrame(filas_n1)
            resumen_l2 = pd.DataFrame(filas_n2)
            resumen_l3 = pd.DataFrame(filas_n3)

            st.subheader(
                f"📊 Comparativa de Productos Afectados por Insumo Código: [{codigo_target}]"
            )

            t1, t2, t3 = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Listas_N2)",
                    "🔴 Sub-Recetas Base (Lista_N1)",
                ]
            )

            with t1:
                st.write(
                    f"**Productos Finales N3 Afectados:** {len(resumen_l3)}"
                )
                if not resumen_l3.empty:
                    st.dataframe(resumen_l3, use_container_width=True)
                else:
                    st.info("Sin registros N3.")

            with t2:
                st.write(
                    f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}"
                )
                if not resumen_l2.empty:
                    st.dataframe(resumen_l2, use_container_width=True)
                else:
                    st.info("Sin registros N2.")

            with t3:
                st.write(f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}")
                if not resumen_l1.empty:
                    st.dataframe(resumen_l1, use_container_width=True)
                else:
                    st.info("Sin registros N1.")

    except Exception as e:
        st.error(f"Error en simulación: {e}")
