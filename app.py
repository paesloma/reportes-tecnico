import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
import google.generativeai as genai
import time  # Necesario para el temporizador

# --- 0. CONFIGURACIÓN DE SEGURIDAD Y API ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash')
        ia_disponible = True
    else:
        st.error("Error: GEMINI_API_KEY no encontrada en los Secrets.")
        ia_disponible = False
except Exception as e:
    st.error(f"Error de configuración: {e}")
    ia_disponible = False

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🚀", layout="centered")

if 'ai_electro' not in st.session_state: st.session_state.ai_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

# --- 2. CARGA DE BASE DE DATOS ---
@st.cache_data
def cargar_datos():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1', sep=None, engine='python')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_datos()

# Listas (Privacidad activada)
LISTA_TECNICOS = ["Técnico A", "Técnico B", "Técnico C"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_input = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, s_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Serie'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    tipo = st.selectbox("Tipo de Reporte", OPCIONES_REPORTE)
    cliente = st.text_input("Cliente", value=c_v)
    producto = st.text_input("Producto", value=p_v)
with col2:
    tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)
    serie = st.text_input("Serie", value=s_v)
    factura = st.text_input("Factura", value=f_v)

rev_fisica = st.text_area("1. Revisión Física", value=f"Se recibe {producto} para evaluación técnica.")

# --- 4. ASISTENTE DE IA CON TEMPORIZADOR ---
st.markdown("### ✨ Asistente de IA")
if st.button("🤖 Autocompletar con IA"):
    if ia_disponible and rev_fisica:
        with st.spinner("Analizando..."):
            try:
                prompt = f"Analiza técnicamente: {rev_fisica}. Formato: ELECTRO: [pasos] OBS: [observaciones]"
                response = model.generate_content(prompt)
                res_text = response.text
                if "ELECTRO:" in res_text:
                    st.session_state.ai_electro = res_text.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = res_text.split("OBS:")[1].strip()
                st.rerun()
            except Exception as e:
                if "429" in str(e):
                    st.warning("⚠️ Límite de cuota excedido. Iniciando temporizador de espera...")
                    
                    # --- LÓGICA DEL TEMPORIZADOR ---
                    placeholder = st.empty()
                    progress_bar = st.progress(0)
                    for segundos_restantes in range(60, 0, -1):
                        placeholder.subheader(f"⏳ Reintentando en {segundos_restantes} segundos...")
                        progress_bar.progress((60 - segundos_restantes + 1) / 60)
                        time.sleep(1)
                    
                    placeholder.success("🔄 ¡Listo! Ya puedes intentar de nuevo.")
                    progress_bar.empty()
                else:
                    st.error(f"Error: {e}")
    else:
        st.warning("Complete la revisión física primero.")

rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_electro)
obs_tecnica = st.text_area("3. Observaciones", value=st.session_state.ai_obs)

# --- 5. IMÁGENES Y PDF ---
st.markdown("### 📸 Evidencia")
archivos = st.file_uploader("Subir fotos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
# (Resto del código de procesamiento de imágenes y PDF igual al anterior)
