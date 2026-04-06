import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# --- 1. CONFIGURACIÓN DE SEGURIDAD (SECRETS) ---
# IMPORTANTE: No pongas la llave aquí. 
# En Streamlit Cloud ve a: Settings -> Secrets y pega:
# GROQ_API_KEY = "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"

try:
    GROQ_KEY = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=GROQ_KEY)
except Exception:
    st.error("⚠️ Falta la configuración de la API Key en los Secrets de Streamlit.")
    st.info("Para solucionar esto: Ve a 'Manage App' -> 'Settings' -> 'Secrets' y añade tu llave.")
    st.stop()

# --- 2. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🔧", layout="centered")

if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'ai_concl' not in st.session_state: st.session_state.ai_concl = ""

# --- 3. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_datos_servicios()

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
ff_v = str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        ff_v = res.iloc[0].get('Fec_Fac_Min', str(date.today()))

st.subheader("Datos del Reporte")
col1, col2 = st.columns(2)
with col1:
    f_prod = st.text_input("Producto")
    f_realizador = st.selectbox("Realizado por", ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"])
with col2:
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v) # Campo solicitado
    f_tecnico = st.selectbox("Revisado por (Técnico)", ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango"])

f_daño = st.text_area("🔧 Diagnóstico de Entrada (Para IA)", placeholder="Ej: Falla en tarjeta principal...")

if st.button("🤖 Generar Diagnóstico con IA"):
    if f_daño:
        with st.spinner("El técnico IA está redactando el informe..."):
            prompt = (f"Actúa como técnico senior. Analiza la falla: '{f_daño}' en el equipo '{f_prod}'. "
                      "Redacta sin asteriscos ni negritas. Divide exactamente en: "
                      "REVISION_TEC: (pruebas realizadas), "
                      "OBSERVACIONES: (hallazgos técnicos), "
                      "CONCLUSIONES: (dictamen final).")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean:
                st.session_state.ai_rev_electro = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ai_obs = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ai_concl = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Campos de texto con los resultados de la IA
st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
st.text_area("3. Observaciones", value=st.session_state.ai_obs)
st.text_area("4. Conclusiones", value=st.session_state.ai_concl) # Campo solicitado

if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    st.success(f"Archivos generados correctamente para la orden {orden_id}.")
