import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
import google.generativeai as genai

# --- 0. CONFIGURACIÓN DE GEMINI ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Cambiamos a 'gemini-pro' que es el más estable para evitar errores 404
         model = genai.GenerativeModel('gemini-2.0-flash')
        ia_disponible = True
    else:
        st.error("Falta la GEMINI_API_KEY en los Secrets de Streamlit.")
        ia_disponible = False
except Exception as e:
    st.error(f"Error al configurar Gemini: {e}")
    ia_disponible = False

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

if 'ai_electro' not in st.session_state: st.session_state.ai_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                df.columns = df.columns.str.strip()
                return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
            except: continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()

# --- CONSTANTES ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')

st.markdown("### Datos del Reporte")
col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

# --- BOTÓN DE IA ---
if st.button("🤖 Autocompletar con IA"):
    if ia_disponible and f_rev_fisica:
        with st.spinner("Gemini Pro está procesando..."):
            try:
                prompt = f"Técnico experto. Basado en: '{f_rev_fisica}' de '{f_prod}', genera: 1- Pasos revisión electro-mecánica. 2- Observaciones. Formato: ELECTRO: [texto] OBS: [texto]"
                response = model.generate_content(prompt)
                txt = response.text
                if "ELECTRO:" in txt and "OBS:" in txt:
                    st.session_state.ai_electro = txt.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = txt.split("OBS:")[1].strip()
                else:
                    st.session_state.ai_electro = txt
                st.rerun()
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    else:
        st.warning("Escribe algo en Revisión Física primero.")

st.text_area("3. Revisión electro-electrónica-mecanica", value=st.session_state.ai_electro)
st.text_area("4. Observaciones", value=st.session_state.ai_obs)
