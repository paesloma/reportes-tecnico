import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq  # Nueva librería que reemplaza a Google

# --- CONFIGURACIÓN DE IA ---
# Tu clave de Groq ya integrada
client = Groq(api_key="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")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Reportes Gerardo Ortiz", page_icon="🛠️")

if 'ai_electro' not in st.session_state: st.session_state.ai_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

# --- CARGA DE DATOS ---
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

# --- MOTOR PDF ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_pdf(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    est_txt = ParagraphStyle('Normal', fontSize=9, leading=11)
    est_tit = ParagraphStyle('Sec', fontSize=10, fontName='Helvetica-Bold', textColor=colors.whitesmoke, backColor=colors.navy, borderPadding=3)
    story = []
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 12))
    tbl_data = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"], [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"], [f"Serie: {datos['serie']}", f"Fecha: {datos['fecha_hoy']}"]]
    t = Table(tbl_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    secciones = [("REVISIÓN FÍSICA", datos['rev_fisica']), ("ANÁLISIS TÉCNICO", datos['rev_electro']), ("OBSERVACIONES", datos['obs_ia']), ("CONCLUSIONES", datos['conclusiones'])]
    for tit, cont in secciones:
        story.append(Spacer(10, 10)); story.append(Paragraph(tit, est_tit)); story.append(Paragraph(cont if cont else "N/A", est_txt))
    if fotos:
        story.append(Spacer(1, 15)); story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_tit))
        for f in fotos:
            img = Image(f['img'], width=2.5*inch, height=2.2*inch)
            story.append(Table([[img, Paragraph(f['desc'], est_txt)]], colWidths=[2.7*inch, 4.3*inch]))
    doc.build(story); buffer.seek(0); return buffer.read()

# --- INTERFAZ ---
st.title("🛠️ Gestión de Reportes Técnicos")

orden_input = st.text_input("Número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, s_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Serie'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    tipo = st.selectbox("Reporte", ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"])
    realizador = st.selectbox("Realizador", ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"])
    cliente = st.text_input("Cliente", value=c_v)
    producto = st.text_input("Producto", value=p_v)
with col2:
    tecnico = st.selectbox("Técnico", ["Tec. Xavier Ramón", "Tec. Andres Mejia", "Tec. Juan Perez"])
    factura = st.text_input("Factura", value=f_v)
    fec_factura = st.date_input("Fecha", value=date.today())
    serie = st.text_input("Serie", value=s_v)

rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa para revisión técnica {producto}.")

# --- ASISTENTE IA (GROQ) ---
st.markdown("### ✨ Asistente de IA")
if st.button("🤖 Autocompletar con IA"):
    if rev_fisica:
        with st.spinner("Generando análisis con Groq..."):
            try:
                chat = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Eres experto técnico. Analiza: {rev_fisica}. Formato: ELECTRO: [pasos] OBS: [notas]"}],
                    model="llama-3.3-70b-versatile",
                )
                res_text = chat.choices[0].message.content
                if "ELECTRO:" in res_text:
                    st.session_state.ai_electro = res_text.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = res_text.split("OBS:")[1].strip()
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_electro)
obs_ia = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
conclusiones = st.text_area("4. Conclusiones")

# --- FOTOS Y PDF ---
archivos = st.file_uploader("Subir fotos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
fotos_preparadas = []
if archivos:
    for i, file in enumerate(archivos):
        desc = st.text_input(f"Descripción foto {i+1}", value="Evidencia", key=f"f_{i}")
        img_pil = PilImage.open(file).convert('RGB')
        buf = BytesIO(); img_pil.save(buf, format='JPEG'); buf.seek(0)
        fotos_preparadas.append({'img': buf, 'desc': desc})

if st.button("💾 GENERAR REPORTE", use_container_width=True):
    datos = {'orden': orden_input, 'cliente': cliente, 'producto': producto, 'factura': factura, 'serie': serie, 'fecha_hoy': date.today(), 'rev_fisica': rev_fisica, 'rev_electro': rev_electro, 'obs_ia': obs_ia, 'conclusiones': conclusiones}
    st.session_state.pdf_data = generar_pdf(datos, fotos_preparadas)
    st.success("PDF generado.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Reporte", st.session_state.pdf_data, f"Reporte_{orden_input}.pdf", "application/pdf")
