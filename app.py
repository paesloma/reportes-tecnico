import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Asegúrate de haber guardado GROQ_API_KEY en los Secrets de Streamlit
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configura tu GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- ESTADOS DE SESIÓN ---
if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'ai_concl' not in st.session_state: st.session_state.ai_concl = ""

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_base_datos():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            # Mapeo de columnas según tus capturas
            return df.rename(columns={
                'Serie/Artículo': 'Serie', 
                'Fec. Fac. Min': 'Fec_Fac_Min', 
                'Fac. Min': 'Fac_Min',
                'Cliente': 'Cliente',
                'Producto': 'Producto'
            })
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_base_datos()

# --- INTERFAZ PRINCIPAL ---
st.title("🚀 Gestión de Reportes Técnicos Completos")

# 1. Búsqueda por Orden
orden_id = st.text_input("Ingrese número de Orden")

# Variables por defecto
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v = row.get('Cliente', '')
        s_v = row.get('Serie', '')
        p_v = row.get('Producto', '')
        f_v = row.get('Fac_Min', '')
        ff_v = row.get('Fec_Fac_Min', str(date.today()))
        st.success(f"✅ Datos cargados para el cliente: {c_v}")

# 2. Datos del Reporte
st.subheader("📋 Información del Servicio")
col1, col2 = st.columns(2)

with col1:
    f_tipo = st.selectbox("Tipo de Reporte", ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO"])
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
    f_realizador = st.selectbox("Realizado por", ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle"])

with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango"])
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.text_input("Fecha Factura (YYYY-MM-DD)", value=ff_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_fec_hoy = st.date_input("Fecha del Reporte", value=date.today())

# 3. Secciones Técnicas
st.subheader("🛠️ Análisis Técnico")

# Revisión Física automática
rev_fisica_default = f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo."
f_rev_fisica = st.text_area("1. Revisión Física", value=rev_fisica_default)

f_daño = st.text_area("🔧 Diagnóstico de Entrada (Describa la falla para la IA)", placeholder="Ej: No enciende, presenta ruido interno...")

if st.button("🤖 Generar Informe con IA"):
    if f_daño:
        with st.spinner("Redactando revisión, observaciones y conclusiones..."):
            prompt = (f"Actúa como técnico experto. Producto: {f_prod}. Falla: {f_daño}. "
                      "Genera un texto profesional sin asteriscos. Divide en: "
                      "REVISION_TEC: (pruebas y mediciones), "
                      "OBSERVACIONES: (daños encontrados), "
                      "CONCLUSIONES: (dictamen final).")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean:
                st.session_state.ai_rev_electro = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ai_obs = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ai_concl = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Campos que se llenan con la IA
st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro, height=150)
st.text_area("3. Observaciones", value=st.session_state.ai_obs, height=100)
st.text_area("4. Conclusiones", value=st.session_state.ai_concl, height=100) # Ahora ya no está vacío

# 4. Botón final
if st.button("💾 GUARDAR Y GENERAR ARCHIVOS", use_container_width=True):
    # Aquí iría tu lógica de generación de PDF/TXT
    st.balloons()
    st.success(f"Reporte de {f_cliente} listo para descarga.")
