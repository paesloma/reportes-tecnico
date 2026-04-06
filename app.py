import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
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
st.set_page_config(page_title="Gestión de Reportes Técnicos", layout="centered")

# Persistencia de datos
if 'fotos_lista' not in st.session_state:
    st.session_state.fotos_lista = []
if 'ia_obs_solo' not in st.session_state:
    st.session_state.ia_obs_solo = ""
if 'pdf_output' not in st.session_state:
    st.session_state.pdf_output = None

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 2. CARGA DE BASE DE DATOS ---
@st.cache_data
def cargar_datos():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_datos()

# --- 3. GENERACIÓN DE PDF (DISEÑO ALINEADO) ---
def generar_pdf_corregido(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    azul = colors.HexColor("#0056b3")
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=azul, spaceAfter=20)
    
    # Espaciado mejorado entre sección y párrafo
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, 
                            backColor=azul, borderPadding=4, spaceBefore=18, spaceAfter=10)
    
    est_just = ParagraphStyle('J', fontSize=9, leading=12, alignment=TA_JUSTIFY)
    
    story = []
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=1.6*inch, height=0.6*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Info General
    tbl_data = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
                [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"]]
    t = Table(tbl_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

    # Secciones Técnicas
    for tit, cont in [("1. REVISIÓN FÍSICA", datos['rf']), ("2. INGRESO A SERVICIO", datos['it']), 
                      ("3. REVISIÓN ELECTROMECÁNICA", datos['re']), ("4. OBSERVACIONES", datos['obs']), 
                      ("5. CONCLUSIONES", datos['con'])]:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_just))

    # Evidencia Alineada
    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for f in fotos:
            img = Image(BytesIO(f['file']), width=2.5*inch, height=1.8*inch)
            # Tabla de 2 columnas para asegurar alineación perfecta de texto e imagen
            t_foto = Table([[img, Paragraph(f['desc'], est_just)]], colWidths=[2.7*inch, 4.3*inch])
            t_foto.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (1,0), (1,0), 15)]))
            story.append(t_foto)
            story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ DE USUARIO ---
st.title("🚀 Gestión de Reportes Técnicos")
orden_input = st.text_input("Ingrese número de Orden")

# Autocompletado desde DB
c_v, p_v, f_v = "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_fac = st.text_input("Factura", value=f_v)
    f_hoy = st.date_input("Fecha Reporte", value=date.today())

st.divider()

# Campos Manuales (No son afectados por la IA)
f_rf = st.text_area("1. Revisión Física", value=f"Se recibe {f_prod} para revisión técnica.")
f_it = st.text_area("2. Ingresa a servicio técnico")
f_re = st.text_area("3. Revisión electro-electrónica-mecánica", value="Pruebas de funcionamiento estándar.")

# IA: ÚNICAMENTE PARA OBSERVACIONES
st.markdown("### 🤖 Generar Observaciones con IA")
ia_prompt = st.text_area("Describa el hallazgo técnico para que la IA redacte las Observaciones")
if st.button("Redactar Observaciones"):
    if ia_prompt:
        with st.spinner("Redactando..."):
            try:
                # Prompt específico para una sola sección
                resp = client.chat.completions.create(
                    messages=[{"role": "user", "content": f"Redacta detalladamente la sección de OBSERVACIONES técnicas para este caso: {ia_prompt}. Producto: {f_prod}. No incluyas otros títulos."}],
                    model="llama-3.3-70b-versatile"
                ).choices[0].message.content
                st.session_state.ia_obs_solo = resp.strip()
                st.rerun()
            except: st.error("Error al conectar con la IA.")

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_obs_solo, height=150)
f_con = st.text_area("5. Conclusiones", value="En base a los hallazgos anteriores se determina...")

# --- 5. GALERÍA CON DESCARGA INDIVIDUAL ---
st.markdown("---")
st.subheader("📸 Galería de Evidencias")
uploader = st.file_uploader("Subir Fotos", type=['png','jpg','jpeg'], accept_multiple_files=True)

if uploader:
    for f in uploader:
        if not any(img['name'] == f.name for img in st.session_state.fotos_lista):
            st.session_state.fotos_lista.append({'file': f.read(), 'name': f.name, 'desc': "Evidencia técnica."})

# Render de miniaturas con acciones duales
for i, foto in enumerate(st.session_state.fotos_lista):
    c_img, c_desc, c_btn = st.columns([1, 3, 1])
    with c_img: st.image(foto['file'], width=120)
    with c_desc: 
        st.session_state.fotos_lista[i]['desc'] = st.text_input(f"Descripción #{i+1}", value=foto['desc'], key=f"txt_{i}")
    with c_btn:
        # Descarga individual
        st.download_button("📥", data=foto['file'], file_name=foto['name'], key=f"dl_{i}")
        # Borrado individual
        if st.button("🗑️", key=f"rm_{i}"):
            st.session_state.fotos_lista.pop(i)
            st.rerun()

st.markdown("---")

# --- 6. GENERACIÓN FINAL ---
if st.button("💾 GENERAR INFORME PDF", use_container_width=True):
    payload = {
        "orden": orden_input, "cliente": f_cliente, "factura": f_fac, "producto": f_prod,
        "rf": f_rf, "it": f_it, "re": f_re, "obs": f_obs, "con": f_con
    }
    st.session_state.pdf_output = generar_pdf_corregido(payload, st.session_state.fotos_lista)
    st.success("✅ Informe generado correctamente")

if st.session_state.pdf_output:
    st.download_button("📥 Descargar Reporte Final", data=st.session_state.pdf_output, 
                       file_name=f"Informe_{orden_input}.pdf", use_container_width=True)
