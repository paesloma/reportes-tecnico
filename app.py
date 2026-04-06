import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Gestión de Reportes Pro", layout="centered")

if 'fotos_lista' not in st.session_state:
    st.session_state.fotos_lista = []
if 'ia_obs' not in st.session_state:
    st.session_state.ia_obs = ""
if 'pdf_final' not in st.session_state:
    st.session_state.pdf_final = None

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets.")
    st.stop()

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_db():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_db()

# --- 3. FUNCIÓN PDF CON MEJORAS DE ALINEACIÓN ---
def generar_pdf_pro(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    azul = colors.HexColor("#0056b3")
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=azul, spaceAfter=20)
    # Espaciado extra entre sección y párrafo
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=azul, borderPadding=4, spaceBefore=15, spaceAfter=8)
    est_just = ParagraphStyle('J', fontSize=9, leading=12, alignment=TA_JUSTIFY, spaceAfter=10)
    
    story = []
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=1.5*inch, height=0.6*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Cabecera alineada
    t_data = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
              [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"]]
    t = Table(t_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

    # Secciones
    for tit, cont in [("1. REVISIÓN FÍSICA", datos['rf']), ("2. INGRESO A ST", datos['it']), 
                      ("3. REVISIÓN ELECTRO-MECÁNICA", datos['re']), ("4. OBSERVACIONES", datos['obs']), 
                      ("5. CONCLUSIONES", datos['con'])]:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_just))

    # Fotos alineadas
    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for f in fotos:
            img = Image(BytesIO(f['file']), width=2.4*inch, height=1.7*inch)
            # Tabla para alinear imagen y texto lateralmente de forma limpia
            t_foto = Table([[img, Paragraph(f['desc'], est_just)]], colWidths=[2.6*inch, 4.4*inch])
            t_foto.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(t_foto)
            story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🔧 Generador de Reportes Técnicos")
orden_id = st.text_input("Número de Orden")

c_v, p_v, s_v, f_v = "", "", "", ""
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        c_v, p_v, s_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Producto'], res.iloc[0]['Serie'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_fac = st.text_input("Factura", value=f_v)
    f_serie = st.text_input("Serie", value=s_v)

st.divider()

# Campos técnicos manuales
f_rf = st.text_area("1. Revisión Física", value=f"Ingresa {f_prod}. Se observa uso continuo.")
f_it = st.text_area("2. Ingresa a servicio técnico")
f_re = st.text_area("3. Revisión electro-mecánica", value="Revisión de voltajes y componentes.")

# IA: SOLO OBSERVACIONES
f_ia_prompt = st.text_area("🤖 Diagnóstico para IA (Generará solo Observaciones)")
if st.button("Generar Observaciones con IA"):
    if f_ia_prompt:
        with st.spinner("Analizando..."):
            try:
                prompt = f"Como técnico experto, genera las OBSERVACIONES para este problema: {f_ia_prompt}. Sé profesional y detallado."
                r = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile").choices[0].message.content
                st.session_state.ia_obs = r.strip()
                st.rerun()
            except: st.error("Error en IA")

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_obs)
f_con = st.text_area("5. Conclusiones", value="En base a los hallazgos...")

# --- GESTIÓN DE FOTOS (CON DESCARGA Y BORRADO) ---
st.subheader("📸 Galería de Evidencias")
uploaded = st.file_uploader("Subir Imágenes", type=['png','jpg','jpeg'], accept_multiple_files=True)

if uploaded:
    for f in uploaded:
        if not any(x['name'] == f.name for x in st.session_state.fotos_lista):
            st.session_state.fotos_lista.append({'file': f.read(), 'name': f.name, 'desc': "Evidencia técnica."})

for i, foto in enumerate(st.session_state.fotos_lista):
    c_img, c_desc, c_acc = st.columns([1, 3, 1])
    with c_img: st.image(foto['file'], width=120)
    with c_desc: 
        st.session_state.fotos_lista[i]['desc'] = st.text_input(f"Descripción #{i+1}", value=foto['desc'], key=f"d_{i}")
    with c_acc:
        # Botones de acción: Descargar y Borrar
        st.download_button("📥", data=foto['file'], file_name=foto['name'], key=f"down_{i}")
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.fotos_lista.pop(i)
            st.rerun()

# --- CIERRE ---
if st.button("💾 GENERAR INFORME PDF", use_container_width=True):
    d_pdf = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "producto": f_prod, "rf": f_rf, "it": f_it, "re": f_re, "obs": f_obs, "con": f_con}
    st.session_state.pdf_final = generar_pdf_pro(d_pdf, st.session_state.fotos_lista)
    st.success("✅ PDF Generado con éxito")

if st.session_state.pdf_final:
    st.download_button("📥 Descargar Reporte Completo", data=st.session_state.pdf_final, file_name=f"Reporte_{orden_id}.pdf", use_container_width=True)
