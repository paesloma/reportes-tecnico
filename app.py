import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 0. CONFIGURACIÓN DE IA ---
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🔧", layout="centered")

# Estados para persistencia y control de borrado
if 'lista_fotos' not in st.session_state: st.session_state.lista_fotos = []
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
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

# CONSTANTES DE INTERFAZ
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. LÓGICA DE INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: pass

st.subheader("Datos del Reporte")
col1, col2 = st.columns(2)
with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_daño = st.text_area("🔧 Daño detectado (Uso interno/IA)", placeholder="Describa el problema aquí...")
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

# ASISTENTE DE IA
if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("IA analizando..."):
            prompt = f"Analiza: {f_daño} en {f_prod}. Genera REVISION_TEC: [pasos] y OBSERVACIONES: [hallazgos]. No uses asteriscos."
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.replace("*", "").strip()
            if "REVISION_TEC:" in clean:
                st.session_state.ai_rev_electro = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ai_obs = clean.split("OBSERVACIONES:")[1].strip()
            st.rerun()

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones", value=TEXTOS_CONCLUSIONES.get(f_tipo, ""))

# --- GESTIÓN DE EVIDENCIA ---
st.subheader("🖼️ Evidencia Fotográfica")
# El key dinámico uploader_key permite resetear el widget al borrar
up_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if up_files:
    for f in up_files:
        if f.name not in [x['name'] for x in st.session_state.lista_fotos]:
            st.session_state.lista_fotos.append({"name": f.name, "data": f.getvalue(), "desc": "Evidencia técnica."})

# Previsualizador con borrado funcional
for i, foto in enumerate(st.session_state.lista_fotos):
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 0.5])
        c1.image(foto['data'], width=100)
        st.session_state.lista_fotos[i]['desc'] = c2.text_input(f"Descripción #{i+1}", value=foto['desc'], key=f"desc_{i}")
        if c3.button("🗑️", key=f"del_{i}"):
            st.session_state.lista_fotos.pop(i)
            st.session_state.uploader_key += 1 # Incremento para resetear el file_uploader
            st.rerun()

if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    # Aquí iría tu lógica de ReportLab para unir los datos al PDF
    st.success("✅ Datos listos para el informe")
