import datetime
import re
import pandas as pd
import streamlit as st

# Intentar importar la librería de Google AI en ámbito global (google-genai / google-generativeai)
try:
    from google import genai
    GENAI_AVAILABLE = "new"
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_AVAILABLE = "legacy"
    except ImportError:
        GENAI_AVAILABLE = False

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ==========================================
st.set_page_config(
    page_title="Fridolin | Centro de Control",
    page_icon="🍰",
    layout="wide",
)

CSS_FRIDOLIN = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Poppins', sans-serif !important;
    }

    .stApp {
        background-color: #FAF8F5;
    }

    .header-fridolin {
        background-color: #8B1D2C !important;
        padding: 1.5rem 2rem !important;
        border-radius: 12px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 12px rgba(139, 29, 44, 0.15) !important;
    }
    
    .header-fridolin h1 {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        margin: 0 !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
    }

    .header-fridolin p {
        color: #F3E5E8 !important;
        font-family: 'Poppins', sans-serif !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
        font-size: 0.95rem !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EBE5DF;
    }

    .main h1, .main h2, .main h3, .main h4 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        color: #8B1D2C !important;
    }

    [data-testid="stMetricValue"] {
        color: #8B1D2C !important;
        font-weight: 700 !important;
    }
</style>
"""
st.markdown(CSS_FRIDOLIN, unsafe_allow_html=True)

# ==========================================
# 2. CARGA Y FUNCIONES AUXILIARES DE DATOS
# ==========================================
ID_HOJA = st.secrets.get("ID_HOJA", "1Y8Dzxl_1jVCUrceAQVfSc94RNugo2cgRsrHJwXLwmU4")


@st.cache_data(ttl=15)
def cargar_pestaña(nombre_pestaña):
    url = f"https://docs.google.com/spreadsheets/d/{ID_HOJA}/gviz/tq?tqx=out:csv&sheet={nombre_pestaña}"
    df = pd.read_csv(url, dtype=str)
    df.columns = [re.sub(r"\s+", " ", str(c)).strip() for c in df.columns]
    return df.fillna("")


def obtener_roles_desde_sheet():
    """Carga y procesa la pestaña Usuarios_Autorizados"""
    try:
        df_users = cargar_pestaña("Usuarios_Autorizados")
        df_users.columns = [str(c).upper().strip() for c in df_users.columns]
        
        dict_usuarios = {}
        for _, row in df_users.iterrows():
            email = str(row.get("EMAIL", "")).strip().lower()
            nombre = str(row.get("NOMBRE", "")).strip()
            rol = str(row.get("ROL", "")).strip().upper()
            pin = str(row.get("PIN", "")).strip()
            
            if email and "@" in email:
                dict_usuarios[email] = {
                    "nombre": nombre if nombre else email.split("@")[0].capitalize(),
                    "rol": rol,
                    "pin": pin
                }
        return dict_usuarios
    except Exception as e:
        st.sidebar.error(f"Error cargando lista de usuarios: {e}")
        return {}


def normalizar_cod(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return re.sub(r"[^A-Za-z0-9]", "", v).upper()


def limpiar_texto_comparar(val):
    if pd.isna(val):
        return ""
    v = str(val).strip().upper()
    return re.sub(r"[^A-Z0-9]", "", v)


def limpiar_cod_mostrar(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA"]:
        return ""
    v = str(val).strip()
    if v.endswith(".0"):
        v = v[:-2]
    return v.upper()


def extraer_num(val):
    if pd.isna(val) or str(val).strip() in ["", "-", "nan", "NO SE ENCONTRO", "NADA", "No Aplica"]:
        return 0.0
    try:
        cleaned = re.sub(r"[^\d.,-]", "", str(val)).replace(",", ".")
        return float(cleaned) if cleaned else 0.0
    except Exception:
        return 0.0


def normalizar_texto(val):
    if pd.isna(val):
        return ""
    return str(val).strip()


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
    for col in df.columns:
        c_u = str(col).strip().upper()
        if "COSTO POR KILO" in c_u or "COSTO POR UNIDAD" in c_u:
            return col

    patron = f"COSTO R{nivel}"
    for col in df.columns:
        if patron in str(col).strip().upper():
            return col

    for col in df.columns:
        c_u = str(col).upper()
        if "COSTO" in c_u and "TOTAL" not in c_u:
            return col

    return df.columns[-1] if len(df.columns) > 0 else ""


def buscar_valor_columna(df_row, lista_palabras_clave):
    for col in df_row.index:
        col_upper = str(col).strip().upper()
        if any(clave.upper() in col_upper for clave in lista_palabras_clave):
            val = df_row[col]
            num = extraer_num(val)
            if num > 0 or str(val).strip() in ["0", "0.0", "0,0"]:
                return num
    return 0.0


def obtener_rendimiento_total_batch(row_values):
    cantidades = []
    for val in row_values[1:]:
        num = extraer_num(val)
        if num > 0:
            cantidades.append(num)
    total = sum(cantidades)
    return total if total > 0 else 1.0


def obtener_precios_y_costo_n3(row_n3):
    costo = 0.0
    pv1, pv2, pv3 = 0.0, 0.0, 0.0

    for col in row_n3.index:
        col_u = str(col).upper().strip()
        val_num = extraer_num(row_n3[col])

        if "COSTO" in col_u and costo == 0.0:
            costo = val_num
        elif ("PRECIO 1" in col_u or "PV1" in col_u or col_u == "PRECIO DE VENTA 1" or "P. VENTA 1" in col_u) and pv1 == 0.0:
            pv1 = val_num
        elif ("PRECIO 2" in col_u or "PV2" in col_u or col_u == "PRECIO DE VENTA 2" or "P. VENTA 2" in col_u) and pv2 == 0.0:
            pv2 = val_num
        elif ("PRECIO 3" in col_u or "PV3" in col_u or col_u == "PRECIO DE VENTA 3" or "P. VENTA 3" in col_u) and pv3 == 0.0:
            pv3 = val_num

    if pv1 == 0.0 and len(row_n3) > 3:
        for val in row_n3.values[2:]:
            n = extraer_num(val)
            if n > costo and pv1 == 0.0:
                pv1 = n
            elif n > costo and pv2 == 0.0:
                pv2 = n
            elif n > costo and pv3 == 0.0:
                pv3 = n

    return costo, pv1, pv2, pv3


def extraer_componentes_por_columnas(filas_receta):
    mp_list = []
    n1_list = []
    n2_list = []

    for _, row in filas_receta.iterrows():
        # MATERIA PRIMA DIRECTA
        if len(row) > 1 and str(row.iloc[1]).strip() not in ["", "-", "NADA", "nan"]:
            nom_mp = str(row.iloc[1]).strip()
            cod_mp = limpiar_cod_mostrar(row.iloc[2]) if len(row) > 2 else ""
            cant_mp = extraer_num(row.iloc[4]) if len(row) > 4 else 0.0
            unid_mp = str(row.iloc[5]).strip() if len(row) > 5 and str(row.iloc[5]).strip() not in ["", "-", "nan", "None"] else "-"

            if nom_mp and nom_mp.upper() != "MATERIA PRIMA":
                mp_list.append({
                    "Código ERP": cod_mp if cod_mp else "-",
                    "Nombre del Insumo": nom_mp,
                    "Cantidad": f"{cant_mp:.4f}",
                    "Unidad": unid_mp
                })

        # RECETAS N1
        if len(row) > 6 and str(row.iloc[6]).strip() not in ["", "-", "NADA", "nan"]:
            nom_n1 = str(row.iloc[6]).strip()
            cod_n1 = limpiar_cod_mostrar(row.iloc[7]) if len(row) > 7 else ""
            cant_n1 = extraer_num(row.iloc[8]) if len(row) > 8 else 0.0
            unid_n1 = str(row.iloc[9]).strip() if len(row) > 9 and str(row.iloc[9]).strip() not in ["", "-", "nan"] else "Kg"

            if nom_n1 and nom_n1.upper() != "RECETAS N1":
                n1_list.append({
                    "codigo": cod_n1 if cod_n1 else normalizar_cod(nom_n1),
                    "nombre": nom_n1,
                    "cantidad": cant_n1,
                    "unidad": unid_n1
                })

        # RECETAS N2
        if len(row) > 10 and str(row.iloc[10]).strip() not in ["", "-", "NADA", "nan"]:
            nom_n2 = str(row.iloc[10]).strip()
            cod_n2 = limpiar_cod_mostrar(row.iloc[11]) if len(row) > 11 else ""
            cant_n2 = extraer_num(row.iloc[12]) if len(row) > 12 else 0.0
            unid_n2 = str(row.iloc[13]).strip() if len(row) > 13 and str(row.iloc[13]).strip() not in ["", "-", "nan"] else "Kg"

            if nom_n2 and nom_n2.upper() != "RECETAS N2":
                n2_list.append({
                    "Código ERP": cod_n2 if cod_n2 else "-",
                    "Nombre Receta N2": nom_n2,
                    "Cantidad": f"{cant_n2:.4f}",
                    "Unidad": unid_n2
                })

    return mp_list, n1_list, n2_list


# ==========================================
# 3. AUTENTICACIÓN DINÁMICA DE USUARIO (SIDEBAR)
# ==========================================
if "usuario_mail" not in st.session_state:
    st.session_state["usuario_mail"] = ""

usuarios_registrados = obtener_roles_desde_sheet()

st.sidebar.markdown("### 🔐 Inicio de Sesión")

if not st.session_state["usuario_mail"]:
    with st.sidebar.form("form_login"):
        mail_input = st.text_input("Correo Corporativo:", placeholder="ejemplo@fridolin.com.bo").strip().lower()
        pin_input = st.text_input("PIN de Acceso:", type="password", placeholder="****").strip()
        btn_login = st.form_submit_button("Ingresar", use_container_width=True)
        
        if btn_login:
            if "@" not in mail_input or "." not in mail_input:
                st.sidebar.error("⚠️ Ingresa un correo electrónico válido.")
            elif mail_input not in usuarios_registrados:
                st.sidebar.error("❌ El correo no se encuentra registrado en el sistema.")
            else:
                user_info = usuarios_registrados[mail_input]
                pin_guardado = user_info.get("pin", "")
                
                if pin_input == pin_guardado and pin_guardado != "":
                    st.session_state["usuario_mail"] = mail_input
                    st.rerun()
                else:
                    st.sidebar.error("🔑 PIN incorrecto. Inténtalo de nuevo.")
else:
    mail_actual = st.session_state["usuario_mail"]
    datos_user = usuarios_registrados.get(mail_actual, {})
    
    nombre_usuario = datos_user.get("nombre", mail_actual)
    rol_usuario = datos_user.get("rol", "SOLO LECTURA")

    es_admin = rol_usuario == "ADMINISTRADOR"
    es_operador = rol_usuario in ["OPERADOR", "ADMINISTRADOR", "OPERADOR AUTORIZADO"]

    st.sidebar.success(f"👤 **Usuario:** {nombre_usuario}\n\n`{mail_actual}`")
    
    if es_admin:
        st.sidebar.markdown("👑 **Rol:** `ADMINISTRADOR`")
    elif es_operador:
        st.sidebar.markdown("👷 **Rol:** `OPERADOR AUTORIZADO`")
    else:
        st.sidebar.warning("👁️ **Rol:** `SOLO LECTURA`")

    if st.sidebar.button("Cerrar Sesión", use_container_width=True):
        st.session_state["usuario_mail"] = ""
        st.rerun()

st.sidebar.divider()

# ==========================================
# 4. ENCABEZADO Y NAVEGACIÓN
# ==========================================
st.markdown(
    """
    <div class="header-fridolin">
        <h1>Fridolin • Centro de Control & Simulación Multinivel</h1>
        <p>Gestión Inteligente de Recetas N1, N2 y N3 • Análisis de Impacto Financiero & Bitácora</p>
    </div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🥧 Menú Principal")
modo_app = st.sidebar.radio(
    "Selecciona la función:",
    [
        "📋 Ficha Técnica de Producto (N3)",
        "📊 Control de Márgenes y Estados (N3)",
        "🍰 Simulación Financiera Multinivel",
        "💬 Feedback por Producto (N3)",
        "📌 Bitácora General de Observaciones",
        "📖 Explorador de Tablas",
        "🤖 Asistente IA (Gemini)",
    ],
)
st.sidebar.divider()

# (mantenido resto del app igual hasta el bloque de Asistente IA)
# ... (omitted for brevity in this message) ...

# ------------------------------------------
# MODO 7: ASISTENTE IA (OPTIMIZADO CON CONTEXTO Y FALLBACK)
# ------------------------------------------
elif modo_app == "🤖 Asistente IA (Gemini)":
    st.markdown("## 🤖 Asistente Virtual Fridolin (Google Gemini)")
    st.caption("Consulta inteligente con contexto real de Recetas N1, N2, N3 y Costos.")

    api_key_secret = st.secrets.get("GEMINI_API_KEY", "") if "GEMINI_API_KEY" in st.secrets else ""

    if "gemini_key_manual" not in st.session_state:
        st.session_state["gemini_key_manual"] = ""

    with st.sidebar.expander("🔑 Configuración Gemini API"):
        if api_key_secret:
            st.success("✅ API Key detectada desde Secrets.")
            api_key_usar = api_key_secret
        else:
            st.info("Ingresa tu Google AI Studio API Key:")
            api_key_usar = st.text_input(
                "API Key:",
                value=st.session_state["gemini_key_manual"],
                type="password",
                placeholder="AIzaSy..."
            )
            st.session_state["gemini_key_manual"] = api_key_usar

    if not api_key_usar:
        st.warning("⚠️ **API Key requerida:** Para utilizar el asistente, ingresa tu API Key de Google Gemini en la barra lateral o en `secrets.toml`.")
        st.markdown("""
            **¿Cómo obtener tu API Key gratuita de Google?**
            1. Ve a [Google AI Studio](https://aistudio.google.com/).
            2. Inicia sesión con tu cuenta de Google.
            3. Haz clic en **Create API key** y copia la clave generada.
            4. Pégala en el panel de la izquierda en **Configuración Gemini API**.
        """)
    elif not GENAI_AVAILABLE:
        st.error("❌ La librería de Google GenAI no está instalada en el entorno Python. Agrega `google-genai` a tu `requirements.txt`.")
    else:
        @st.cache_data(ttl=60)
        def obtener_resumen_contexto():
            try:
                df_l3 = cargar_pestaña("Lista_N3")
                df_l2 = cargar_pestaña("Lista_N2")
                df_l1 = cargar_pestaña("Lista_N1")
                df_m = cargar_pestaña("Mermas_Costos")
                
                prods_n3 = df_l3.iloc[:, 0].dropna().head(15).tolist() if not df_l3.empty else []
                insumos = df_m.iloc[:, 0].dropna().head(15).tolist() if not df_m.empty else []

                contexto_str = (
                    f"Resumen de base de datos actual de Fridolin:\n"
                    f"- Total Recetas N3 (Productos Terminados): {len(df_l3)}\n"
                    f"- Muestra Productos N3: {', '.join(prods_n3[:8])}\n"
                    f"- Total Recetas N2 (Intermedios): {len(df_l2)}\n"
                    f"- Total Recetas N1 (Sub-recetas Base): {len(df_l1)}\n"
                    f"- Total Insumos Mermas/Costos: {len(df_m)}\n"
                    f"- Muestra Insumos: {', '.join(insumos[:8])}\n"
                )
                return contexto_str
            except Exception:
                return "Base de datos de recetas Fridolin activa."

        resumen_datos = obtener_resumen_contexto()

        if "mensajes_ia" not in st.session_state:
            st.session_state["mensajes_ia"] = [
                {
                    "role": "assistant",
                    "content": "¡Hola! Soy el asistente técnico de **Fridolin**. Tengo acceso al contexto de tus recetas N1, N2 y N3. ¿En qué consulta sobre rendimientos, insumos o costos pu..."
                }
            ]

        for msg in st.session_state["mensajes_ia"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Escribe tu consulta sobre recetas, productos o insumos...")

        if prompt:
            st.session_state["mensajes_ia"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Procesando consulta con Gemini..."):
                    historial_formateado = ""
                    for m in st.session_state["mensajes_ia"][-6:]:
                        r = "Usuario" if m["role"] == "user" else "Asistente"
                        historial_formateado += f"\n{r}: {m['content']}"

                    system_prompt = (
                        "Eres el asistente virtual especializado del Centro de Control de Recetas de Fridolin (Santa Cruz, Bolivia). "
                        "Respondes con precisión técnica, tono profesional y amigable. Ayudas en la gestión de materias primas, "
                        "estructuras de recetas multinivel (N1 sub-recetas, N2 intermedios, N3 productos finales) y costos.\n\n"
                        f"CONTEXTO DE DATOS:\n{resumen_datos}\n\n"
                        f"HISTORIAL RECIENTE:{historial_formateado}\n\n"
                        f"Consulta actual: {prompt}"
                    )

                    # Modelos preferidos (orden de intento)
                    modelos_preferidos = [
                        "gemini-2.5-flash",
                        "gemini-2.0-flash",
                        "gemini-1.5-flash",
                        "gemini-1.5-pro-latest",
                    ]

                    texto_respuesta = ""
                    ultimo_error = ""

                    # Función auxiliar: intentar listar modelos disponibles (muy tolerante según SDK)
                    def listar_modelos_disponibles(api_key):
                        modelos = []
                        try:
                            if GENAI_AVAILABLE == "new":
                                c = genai.Client(api_key=api_key)
                                # intentar varios accesos a listado según cliente
                                if hasattr(c, "list_models"):
                                    resp = c.list_models()
                                    # resp puede ser iterable de objetos
                                    try:
                                        modelos = [getattr(m, "name", str(m)) for m in resp]
                                    except Exception:
                                        modelos = [str(m) for m in resp]
                                elif hasattr(c, "models") and hasattr(c.models, "list"):
                                    resp = c.models.list()
                                    try:
                                        modelos = [getattr(m, "name", str(m)) for m in resp]
                                    except Exception:
                                        modelos = [str(m) for m in resp]
                            else:
                                # legacy google.generativeai
                                try:
                                    genai.configure(api_key=api_key)
                                    resp = genai.list_models()
                                    try:
                                        modelos = [m.get("name") if isinstance(m, dict) else getattr(m, "name", str(m)) for m in resp]
                                    except Exception:
                                        modelos = [str(m) for m in resp]
                                except Exception:
                                    modelos = []
                        except Exception:
                            modelos = []
                        return modelos

                    available_models = listar_modelos_disponibles(api_key_usar)

                    # Si obtuvimos modelos, filtramos la lista de preferidos para solo usar los que existan (por coincidencia parcial)
                    to_try = modelos_preferidos.copy()
                    if available_models:
                        filtered = []
                        for pref in modelos_preferidos:
                            if any(pref in am for am in available_models):
                                filtered.append(pref)
                        if filtered:
                            to_try = filtered

                    # Intentar cada modelo en to_try
                    for mod_name in to_try:
                        try:
                            if GENAI_AVAILABLE == "new":
                                client = genai.Client(api_key=api_key_usar)
                                # método generate_content puede variar por versión; intentamos con distintas firmas
                                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                                    response = client.models.generate_content(model=mod_name, contents=system_prompt)
                                    texto_respuesta = getattr(response, "text", None) or str(response)
                                else:
                                    # intentamos la API de alto nivel si está disponible
                                    response = client.generate_text(model=mod_name, prompt=system_prompt)
                                    texto_respuesta = getattr(response, "text", None) or str(response)
                            else:
                                genai.configure(api_key=api_key_usar)
                                model = genai.GenerativeModel(mod_name)
                                response = model.generate_content(system_prompt)
                                texto_respuesta = getattr(response, "text", None) or str(response)

                            if texto_respuesta:
                                break
                        except Exception as ex:
                            ultimo_error = str(ex)
                            # continuar al siguiente modelo
                            continue

                    if not texto_respuesta:
                        detalle = ultimo_error if ultimo_error else "Sin detalles de error (revise logs)."
                        texto_respuesta = (
                            f"⚠️ No fue posible obtener respuesta con los modelos configurados.\n\n"
                            f"**Detalle del error:** `{detalle}`\n\n"
                            "Sugerencias:\n"
                            "1. Asegúrate de que la API Key sea válida y tenga permisos para Generative AI (AI Studio).\n"
                            "2. Ejecuta una prueba local para listar modelos (usa genai.list_models()) y verifica los nombres disponibles.\n"
                            "3. Actualiza `requirements.txt` con `google-genai>=0.1.0` o `google-generativeai>=0.1.0` según la librería que prefieras.\n"
                            "4. Si recibes errores 404 para un modelo específico, cámbialo por uno listado en la respuesta de list_models().\n"
                        )

                    st.markdown(texto_respuesta)
                    st.session_state["mensajes_ia"].append({"role": "assistant", "content": texto_respuesta})

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
