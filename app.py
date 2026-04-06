import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes", layout="centered")

# Inicialización de persistencia para evitar KeyError
if 'ia_resp' not in st.session_state:
    st.session_state.ia_resp = {"obs": "", "concl": ""}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Cliente Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en Secrets.")
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

# --- 3. FUNCION PDF (JUSTIFICADO Y PROFESIONAL) ---
def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=colors.HexColor("#0056b3"), spaceAfter=12)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.HexColor("#0056b3"), borderPadding=4, spaceBefore=10, spaceAfter=5)
    est_txt = ParagraphStyle('TXT', fontSize=9, leading=12, alignment=TA_JUSTIFY)
    
    story = []
    if os.path.exists("logo.png"): story.append(Image("logo.png", width=1.5*inch, height=0.6*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Tabla de cabecera
    header_data = [
        [f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
        [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"]
    ]
    t = Table(header_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t)

    # Secciones
    secciones = [
        ("1. Revisión Física", datos['rf']),
        ("2. Ingresa a servicio técnico", datos['it']),
        ("3. Revisión electro-electrónica-mecanica", datos['re']),
        ("4. Observaciones", datos['obs']),
        ("5. Conclusiones", datos['con'])
    ]
    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))

    # Imágenes
    if lista_imgs:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for img_info in lista_imgs:
            story.append(Spacer(1, 10))
            img = Image(img_info['file'], width=2.5*inch, height=1.8*inch)
            t_img = Table([[img, Paragraph(img_info['desc'], est_txt)]], colWidths=[2.7*inch, 4*inch])
            story.append(t_img)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes")
orden_id = st.text_input("Orden #")

# Autocompletado
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

# CAMPOS ORIGINALES REINSTAURADOS
f_rf = st.text_area("1. Revisión Física", value=f"Ingresa {f_prod}. Se observa uso continuo.")
f_it = st.text_area("2. Ingresa a servicio técnico")
f_re = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se revisa sistema de alimentación y líneas de conexión.")

# IA CON FORMATO SEGURO
f_diag_ia = st.text_area("🔧 Diagnóstico para IA")
if st.button("🤖 Generar con IA"):
    if f_diag_ia:
        with st.spinner("Generando..."):
            prompt = f"Falla: {f_diag_ia}. Responde con este formato exacto: OBS: [texto] CON: [texto]"
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            texto = res.choices[0].message.content
            if "OBS:" in texto and "CON:" in texto:
                st.session_state.ia_resp["obs"] = texto.split("OBS:")[1].split("CON:")[0].strip()
                st.session_state.ia_resp["concl"] = texto.split("CON:")[1].strip()
            st.rerun()

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_resp["obs"])
f_con = st.text_area("5. Conclusiones", value=st.session_state.ia_resp["concl"])

# SECCIÓN DE IMÁGENES (CON MINIATURAS)
st.markdown("### 📸 Evidencia Fotográfica")
files = st.file_uploader("Subir imágenes", type=['png','jpg','jpeg'], accept_multiple_files=True)
lista_para_pdf = []

if files:
    for idx, f in enumerate(files):
        c1, c2 = st.columns([1, 3])
        with c1:
            st.image(f, width=150) # Miniatura
        with c2:
            desc = st.text_input(f"Descripción Foto #{idx+1}", value="Evidencia técnica.", key=f"desc_{idx}")
            
            # Procesar para PDF
            img_bytes = BytesIO()
            PilImage.open(f).convert('RGB').save(img_bytes, format='JPEG')
            img_bytes.seek(0)
            lista_para_pdf.append({"file": img_bytes, "desc": desc})

# GENERACIÓN
if st.button("💾 GENERAR REPORTE"):
    datos = {"orden": orden_id, "cliente": f_cliente, "producto": f_prod, "factura": f_fac, "serie": f_serie, "rf": f_rf, "it": f_it, "re": f_re, "obs": f_obs, "con": f_con}
    st.session_state.pdf_data = generar_pdf(datos, lista_para_pdf)
    st.success("PDF Listo")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Informe", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_id}.pdf")
