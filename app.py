import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configura la GROQ_API_KEY en los Secrets de Streamlit.")
    st.stop()

# --- 2. LISTADOS COMPLETOS DE PERSONAL ---
# Listado de los 8 técnicos que coordinas
LISTA_TECNICOS = [
    "Tec. Xavier Ramón", 
    "Tec. Juan Diego Quezada", 
    "Tec. Javier Quiguango", 
    "Tec. Wilson Quiguango", 
    "Tec. Carlos Jama", 
    "Tec. Manuel Vera", 
    "Tec. Juan Farez", 
    "Tec. Santiago Farez"
]

# Listado de ingenieros realizadores
LISTA_REALIZADORES = [
    "Ing. Henry Beltran", 
    "Ing. Pablo Lopez", 
    "Ing. Christian Calle", 
    "Ing. Guillermo Ortiz"
]

# --- 3. CARGA DE DATOS DESDE CSV ---
@st.cache_data
def cargar_db():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={
                'Serie/Artículo': 'Serie', 
                'Fec. Fac. Min': 'Fec_Fac_Min', 
                'Fac. Min': 'Fac_Min'
            })
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_db()

# --- 4. INTERFAZ ---
st.title("🔧 Sistema de Reportes - Post-Venta")

orden_id = st.text_input("Ingrese número de Orden")

# Autocompletado de datos
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v, ff_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min',''), row.get('Fec_Fac_Min', ff_v)

col1, col2 = st.columns(2)
with col1:
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES) # Ahora con la lista completa
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS) # Los 8 técnicos incluidos
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.text_input("Fecha Factura", value=ff_v)
    f_serie = st.text_input("Serie", value=s_v)

# --- 5. GENERACIÓN CON IA ---
st.subheader("📝 Análisis de Falla")
f_daño = st.text_area("Describa el problema para la IA")

if st.button("🤖 Generar Diagnóstico Profesional"):
    if f_daño:
        with st.spinner("Redactando informe..."):
            prompt = (f"Como experto en línea blanca y tecnología, analiza: {f_daño}. "
                      "Genera: REVISION_TEC, OBSERVACIONES y CONCLUSIONES.")
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            # Guardar en session_state para que no se borre al recargar
            if "REVISION_TEC:" in clean:
                st.session_state.rev = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.obs = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.con = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Mostrar resultados
st.text_area("2. Revisión Técnica", value=st.session_state.get('rev', ""))
st.text_area("3. Observaciones", value=st.session_state.get('obs', ""))
st.text_area("4. Conclusiones", value=st.session_state.get('con', "")) # Campo conclusiones corregido
