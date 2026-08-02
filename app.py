import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recetario Inteligente & Centro de Control",
    page_icon="🍳",
    layout="wide",
)

st.title("🍳 Recetario Inteligente & Centro de Control")
st.caption("Simulación Financiera Ejecutiva y Efecto Dominó (Lista N1 ➔ N2 ➔ N3)")
st.divider()

ID_HOJA = "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4"


@st.cache_data(ttl=60)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    return pd.read_csv(url)


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
        "Visualiza de manera limpia el Costo Actual vs. Costo Simulado y su variación en Productos Finales e Intermedios."
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

        st.subheader("1️⃣ Selecciona la Materia Prima")
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

            costo_actual = 19.59
            for col in df_mermas.columns:
                if "COSTO" in col.upper() or "PRECIO" in col.upper():
                    try:
                        val = float(
                            str(datos_insumo[col])
                            .replace("Bs", "")
                            .replace(",", "")
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
                    value=25.00,
                    step=1.0,
                )
            with c3:
                dif_precio = nuevo_precio - costo_actual
                porc_inc = (
                    (dif_precio / costo_actual) * 100 if costo_actual > 0 else 0
                )
                st.metric(
                    "Incremento Simulado",
                    f"+Bs {dif_precio:.2f}",
                    delta=f"{porc_inc:.1f}%",
                )

            st.divider()

            # --- ALGORITMO DE RASTREO MULTINIVEL CON CANTIDADES DE USO ---
            terminos_busqueda = [
                t
                for t in [codigo_val, recetario_val, articulo_val]
                if t
                and t.lower() != "nan"
                and t.lower() != "no encontrado en erp"
                and len(t) > 2
            ]

            # RASTREO N1 (Calcula consumo del insumo en N1)
            patron_n1 = "|".join(terminos_busqueda)
            afectadas_recetas_n1 = df_recetas_n1[
                df_recetas_n1.apply(
                    lambda r: r.astype(str)
                    .str.contains(patron_n1, case=False, na=False)
                    .any(),
                    axis=1,
                )
            ]
            subrecetas_n1_nombres = (
                afectadas_recetas_n1[df_recetas_n1.columns[0]]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            # RASTREO N2
            terminos_n2 = terminos_busqueda + subrecetas_n1_nombres
            patron_n2 = "|".join(
                [
                    str(t)
                    for t in terminos_n2
                    if str(t).strip() and str(t) != "nan"
                ]
            )
            afectadas_recetas_n2 = df_recetas_n2[
                df_recetas_n2.apply(
                    lambda r: r.astype(str)
                    .str.contains(patron_n2, case=False, na=False)
                    .any(),
                    axis=1,
                )
            ]
            subrecetas_n2_nombres = (
                afectadas_recetas_n2[df_recetas_n2.columns[0]]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            # RASTREO N3
            terminos_n3 = (
                terminos_busqueda
                + subrecetas_n1_nombres
                + subrecetas_n2_nombres
            )
            patron_n3 = "|".join(
                [
                    str(t)
                    for t in terminos_n3
                    if str(t).strip() and str(t) != "nan"
                ]
            )
            afectadas_recetas_n3 = df_recetas_n3[
                df_recetas_n3.apply(
                    lambda r: r.astype(str)
                    .str.contains(patron_n3, case=False, na=False)
                    .any(),
                    axis=1,
                )
            ]
            subrecetas_n3_nombres = (
                afectadas_recetas_n3[df_recetas_n3.columns[0]]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            # --- FUNCION REUTILIZABLE PARA LIMPIAR Y CONSTRUIR LA TABLA RESUMEN ---
            def construir_tabla_ejecutiva(
                df_lista, nombres_afectados, nivel_nombre
            ):
                col_prod = df_lista.columns[0]

                # Filtrar solo productos afectados
                df_filtrado = df_lista[
                    df_lista[col_prod].astype(str).isin(nombres_afectados)
                ].copy()

                if df_filtrado.empty:
                    return pd.DataFrame()

                # Buscar columna Estado
                col_estado = "N/A"
                for c in df_filtrado.columns:
                    if "ESTADO" in c.upper():
                        col_estado = c
                        break

                # Buscar columna Costo Actual
                col_costo = None
                for c in df_filtrado.columns:
                    if "COSTO" in c.upper():
                        col_costo = c
                        break

                # Construir DataFrame limpio
                df_resumen = pd.DataFrame()
                df_resumen["Producto / Subreceta"] = df_filtrado[
                    col_prod
                ].values
                df_resumen["Estado"] = (
                    df_filtrado[col_estado].values
                    if col_estado in df_filtrado.columns
                    else "Activo"
                )

                # Extraer costo base en flotante
                def extraer_num(val):
                    try:
                        return float(
                            str(val)
                            .replace("Bs", "")
                            .replace(",", "")
                            .strip()
                        )
                    except:
                        return 0.0

                if col_costo:
                    costos_base = df_filtrado[col_costo].apply(extraer_num)
                else:
                    costos_base = pd.Series([0.0] * len(df_filtrado))

                # Calcular costo simulado sumando la variación proporcional del insumo base
                # Si el insumo subió dif_precio (ej. +5.41 Bs), sumamos ese impacto directo
                costos_simulados = costos_base + dif_precio
                variaciones_bs = dif_precio
                variaciones_porc = (
                    (variaciones_bs / costos_base) * 100
                ).fillna(0)

                # Formatear columnas para la vista final
                df_resumen["Costo Actual"] = costos_base.apply(
                    lambda x: f"Bs {x:.2f}"
                )
                df_resumen["Costo Simulado"] = costos_simulados.apply(
                    lambda x: f"Bs {x:.2f}"
                )
                df_resumen["Variación (Bs)"] = f"+Bs {dif_precio:.2f}"
                df_resumen["Variación (%)"] = variaciones_porc.apply(
                    lambda x: f"+{x:.1f}%" if x > 0 else "0.0%"
                )

                return df_resumen

            # Construir DataFrames Limpios
            resumen_l3 = construir_tabla_ejecutiva(
                df_lista_n3, subrecetas_n3_nombres, "N3"
            )
            resumen_l2 = construir_tabla_ejecutiva(
                df_lista_n2, subrecetas_n2_nombres, "N2"
            )
            resumen_l1 = construir_tabla_ejecutiva(
                df_lista_n1, subrecetas_n1_nombres, "N1"
            )

            # --- PRESENTACIÓN VISUAL EN PESTAÑAS ---
            st.subheader(
                f"📊 Comparativa Ejecutiva de Productos Afectados por: **{codigo_val}**"
            )

            resumen_tabs1, resumen_tabs2, resumen_tabs3 = st.tabs(
                [
                    "🟢 Productos Finales (Lista_N3)",
                    "🟠 Rellenos / Intermedios (Listas_N2)",
                    "🔴 Sub-Recetas Base (Lista_N1)",
                ]
            )

            with resumen_tabs1:
                st.write(
                    f"**Productos Finales N3 Afectados:** {len(resumen_l3)}"
                )
                if not resumen_l3.empty:
                    st.dataframe(resumen_l3, use_container_width=True)
                else:
                    st.info(
                        "No se encontraron coincidencias consolidadas en Lista_N3."
                    )

            with resumen_tabs2:
                st.write(
                    f"**Productos Intermedios N2 Afectados:** {len(resumen_l2)}"
                )
                if not resumen_l2.empty:
                    st.dataframe(resumen_l2, use_container_width=True)
                else:
                    st.info(
                        "No se encontraron coincidencias consolidadas en Listas_N2."
                    )

            with resumen_tabs3:
                st.write(
                    f"**Sub-Recetas N1 Afectadas:** {len(resumen_l1)}"
                )
                if not resumen_l1.empty:
                    st.dataframe(resumen_l1, use_container_width=True)
                else:
                    st.info(
                        "No se encontraron coincidencias consolidadas en Lista_N1."
                    )

            st.divider()

            # --- AUDITORÍA DE RECETAS DETALLADAS ---
            with st.expander(
                "🔍 Auditar Recetas Detalladas (Ingrediente por Ingrediente)"
            ):
                st.caption(
                    "Pestañas de respaldo técnico con todas las columnas e ingredientes originales."
                )
                d_tab1, d_tab2, d_tab3 = st.tabs(
                    [
                        "Detalle Recetas_N3",
                        "Detalle Recetas_N2",
                        "Detalle Recetas_N1",
                    ]
                )

                with d_tab1:
                    st.dataframe(
                        afectadas_recetas_n3, use_container_width=True
                    )
                with d_tab2:
                    st.dataframe(
                        afectadas_recetas_n2, use_container_width=True
                    )
                with d_tab3:
                    st.dataframe(
                        afectadas_recetas_n1, use_container_width=True
                    )

    except Exception as e:
        st.error(f"Error durante el cálculo de la simulación: {e}")