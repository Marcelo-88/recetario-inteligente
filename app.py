import streamlit as st
import pandas as pd
import numpy as np

def calcular_pesos_totales_n3(df_recetas_n3):
    """Suma dinámicamente el peso de los ingredientes comestibles por producto."""
    df_ing = df_recetas_n3.copy()
    # Limpiar espacios en nombres de columnas
    df_ing.columns = df_ing.columns.str.strip()
    
    # Filtrar solo 'Ingrediente'
    if 'Categoria' in df_ing.columns:
        df_ing = df_ing[df_ing['Categoria'].astype(str).str.strip() == 'Ingrediente']
    
    # Convertir cantidades a número
    for col in ['Cantidad MP', 'Cantidad N1', 'Cantidad N2']:
        if col in df_ing.columns:
            df_ing[col] = pd.to_numeric(df_ing[col], errors='coerce').fillna(0.0)
        else:
            df_ing[col] = 0.0

    df_pesos = df_ing.groupby('Recetas 3')[['Cantidad MP', 'Cantidad N1', 'Cantidad N2']].sum()
    df_pesos['Peso_Comestible_Kg'] = df_pesos.sum(axis=1)
    
    return df_pesos['Peso_Comestible_Kg'].to_dict()


def construir_tabla_ejecutiva(df_lista3, df_recetas_n3, elemento_afectado, incremento_base_bs):
    if df_lista3.empty or df_recetas_n3.empty or not elemento_afectado:
        st.warning("⚠️ Selecciona un insumo para ver la simulación.")
        return pd.DataFrame()

    # Normalizar espacios en nombres de columnas
    df_lista3 = df_lista3.copy()
    df_recetas_n3 = df_recetas_n3.copy()
    df_lista3.columns = df_lista3.columns.str.strip()
    df_recetas_n3.columns = df_recetas_n3.columns.str.strip()
    
    if 'Categoria' in df_recetas_n3.columns:
        df_recetas_n3['Categoria'] = df_recetas_n3['Categoria'].astype(str).str.strip()

    diccionario_pesos = calcular_pesos_totales_n3(df_recetas_n3)
    filas_resumen = []
    elemento_afectado_str = str(elemento_afectado).strip().lower()

    for _, row in df_lista3.iterrows():
        nombre_producto = str(row.get('Recetas 3', '')).strip()
        if not nombre_producto:
            continue
            
        estado = str(row.get('Estado', 'Activo'))
        costo_base = pd.to_numeric(row.get('Costo R3', 0.0), errors='coerce')
        if pd.isna(costo_base): 
            costo_base = 0.0

        filas_receta = df_recetas_n3[df_recetas_n3['Recetas 3'].astype(str).str.strip() == nombre_producto]
        if filas_receta.empty:
            continue

        peso_comestible_torta = diccionario_pesos.get(nombre_producto, 0.0)
        impacto_total_bs = 0.0
        cantidad_usada_registrada = 0.0
        es_producto_afectado = False

        for _, f in filas_receta.iterrows():
            cat_ingrediente = str(f.get('Categoria', 'Ingrediente')).strip()

            cant_mp = pd.to_numeric(f.get('Cantidad MP', 0), errors='coerce') or 0.0
            cant_n1 = pd.to_numeric(f.get('Cantidad N1', 0), errors='coerce') or 0.0
            cant_n2 = pd.to_numeric(f.get('Cantidad N2', 0), errors='coerce') or 0.0

            # Coincidencias flexibles
            coincide_mp = elemento_afectado_str in str(f.get('Materia Prima', '')).strip().lower()
            coincide_cod = elemento_afectado_str == str(f.get('Código ERP', '')).strip().lower()
            coincide_n1 = elemento_afectado_str in str(f.get('Recetas N1', '')).strip().lower()
            coincide_n2 = elemento_afectado_str in str(f.get('Recetas N2', '')).strip().lower()

            if coincide_mp or coincide_cod or coincide_n1 or coincide_n2:
                es_producto_afectado = True
                cant_item = cant_mp + cant_n1 + cant_n2
                cantidad_usada_registrada += cant_item

                if cat_ingrediente == 'Empaque':
                    impacto_total_bs += incremento_base_bs * cant_item
                else:
                    if peso_comestible_torta > 0:
                        proporcionalidad = cant_item / peso_comestible_torta
                        impacto_total_bs += incremento_base_bs * proporcionalidad
                    else:
                        impacto_total_bs += incremento_base_bs * cant_item

        if es_producto_afectado:
            costo_simulado = costo_base + impacto_total_bs
            var_porc = (impacto_total_bs / costo_base * 100) if costo_base > 0 else 0.0

            filas_resumen.append({
                "Producto / Subreceta": nombre_producto,
                "Estado": estado,
                "Cant. Usada": f"{cantidad_usada_registrada:.3f}",
                "Peso Torta": f"{peso_comestible_torta:.3f} kg" if peso_comestible_torta > 0 else "Empaque",
                "Costo Actual": f"Bs {costo_base:.2f}",
                "Costo Simulado": f"Bs {costo_simulado:.2f}",
                "Variación (Bs)": f"+Bs {impacto_total_bs:.2f}",
                "Variación (%)": f"+{var_porc:.1f}%"
            })

    res_df = pd.DataFrame(filas_resumen)
    
    if res_df.empty:
        st.info("ℹ️ No se encontraron productos en Lista_N3 que utilicen directamente este insumo o subreceta en su receta final.")
    
    return res_df
