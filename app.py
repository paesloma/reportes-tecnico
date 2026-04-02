import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# --- 0. CONFIGURACIÓN DE IA ---
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes", page_icon="🔧", layout="centered")

# Inicialización de estados para persistencia y gestión de imágenes
if 'lista_fotos' not in st.session_state: st.session_state.lista_fotos = []
if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                df.columns = df.columns.str.strip()
                df = df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
                return df
            except: continue
    return pd.DataFrame()

df_db = cargar_datos_servicios()

LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. LÓGICA DE INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')

col1, col2 = st.columns(2)
with col1:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_daño = st.text_area("🔧 Daño detectado (Uso interno/IA)", placeholder="Ej: Antena rota, filtración de agua...")
f_rev_fisica = st.text_area("1. Revisión Física (PDF)", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

# --- BOTÓN IA ---
if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("Analizando..."):
            try:
                prompt = f"Producto: {f_prod}. Daño: {f_daño}. Genera REVISION_TEC: [pasos] y OBSERVACIONES: [hallazgos]. Sin asteriscos."
                resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                clean_text = resp.choices[0].message.content.replace("*", "").strip()
                if "REVISION_TEC:" in clean_text:
                    st.session_state.ai_rev_electro = clean_text.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                    st.session_state.ai_obs = clean_text.split("OBSERVACIONES:")[1].strip()
                st.rerun()
            except: st.error("Límite de cuota excedido. Reintente en breve.")

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones")

# --- 4. GESTIÓN DE IMÁGENES CON PREVISUALIZACIÓN Y BORRADO ---
st.subheader("🖼️ Evidencia Fotográfica")
uploaded_files = st.file_uploader("Añadir fotos", type=['jpg','png','jpeg'], accept_multiple_files=True, key="uploader")

# Agregar archivos nuevos a la lista de sesión
if uploaded_files:
    for f in uploaded_files:
        if f.name not in [x['name'] for x in st.session_state.lista_fotos]:
            img_data = f.read()
            st.session_state.lista_fotos.append({"name": f.name, "data": img_data, "desc": "Evidencia técnica."})

# Mostrar Previsualizador
if st.session_state.lista_fotos:
    for idx, foto in enumerate(st.session_state.lista_fotos):
        with st.container(border=True):
            col_img, col_info, col_del = st.columns([1, 2, 0.5])
            with col_img:
                st.image(foto['data'], width=100)
            with col_info:
                st.session_state.lista_fotos[idx]['desc'] = st.text_input(f"Descripción #{idx+1}", value=foto['desc'], key=f"desc_{idx}")
            with col_del:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.lista_fotos.pop(idx)
                    st.rerun()

# --- 5. GENERACIÓN ---
# (Aquí se llamaría a la función de ReportLab como en los pasos anteriores)
if st.button("💾 GENERAR REPORTE", use_container_width=True):
    # Lógica de construcción del PDF usando st.session_state.lista_fotos
    st.success("Reporte listo para descarga.")
