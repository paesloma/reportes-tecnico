import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# ReportLab para PDF profesional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes Pro", layout="centered")

# Inicialización de persistencia
if 'ia_resp' not in st.session_state:
    st.session_state.ia_resp = {"obs": "", "concl": ""}
if 'fotos' not in st.session_state:
    st.session_state.fotos = [] 
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Cliente Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets.")
    st.stop()

# --- 2. CARGA DE BASE DE DATOS ---
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

# --- 3. LÓGICA DE PDF (JUSTIFICADO) ---
def generar_pdf_profesional(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    azul_corp = colors.HexColor("#0056b3")
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=azul_corp, spaceAfter=15)
    est_seccion = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=azul_corp, borderPadding=4, spaceBefore=12, spaceAfter=6)
    est_just = ParagraphStyle('J', fontSize=9, leading=12, alignment=TA_JUSTIFY)
    
    story = []
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=1.5*inch, height=0.6*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    tbl_data = [
        [f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
        [f"Cliente: {datos['cliente']}", f"Fecha: {datos['fecha']}"],
        [f"Producto: {datos['producto']}", f"Serie: {datos['serie']}"]
    ]
    t = Table(tbl_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
    story.append(t)

    # Secciones Técnicas Mantenidas
    secciones = [
        ("1. REVISIÓN FÍSICA", datos['rf']),
        ("2. INGRESA A SERVICIO TÉCNICO", datos['it']),
        ("3. REVISIÓN ELECTRO-ELECTRÓNICA-MECÁNICA", datos['re']),
        ("4. OBSERVACIONES", datos['obs']),
        ("5. CONCLUSIONES", datos['con'])
    ]
    
    for titulo, contenido in secciones:
        story.append(Paragraph(titulo, est_seccion))
        story.append(Paragraph(contenido.replace('\n', '<br/>'), est_just))

    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_seccion))
        for f in fotos:
            story.append(Spacer(1, 10))
            img = Image(BytesIO(f['file']), width=2.4*inch, height=1.7*inch)
            t_img = Table([[img, Paragraph(f['desc'], est_just)]], colWidths=[2.6*inch, 4.4*inch])
            story.append(t_img)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🔧 Generador de Informes Técnicos")
orden_input = st.text_input("Número de Orden")

c_v, p_v, s_v, f_v = "", "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, p_v, s_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Producto'], res.iloc[0]['Serie'], res.iloc[0]['Fac_Min']

col_a, col_b = st.columns(2)
with col_a:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col_b:
    f_fac = st.text_input("Factura", value=f_v)
    f_serie = st.text_input("Serie", value=s_v)

st.divider()

# TODOS LOS CAMPOS MANTENIDOS
f_rf = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo.")
f_it = st.text_area("2. Ingresa a servicio técnico")
f_re = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se revisa sistema de alimentación y control.")

f_diag_ia = st.text_area("🤖 Diagnóstico para IA")
if st.button("Generar con IA"):
    if f_diag_ia:
        with st.spinner("IA trabajando..."):
            try:
                prompt = f"Falla: {f_diag_ia}. Genera para informe: OBS: [texto] y CON: [texto]"
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                texto = res.choices[0].message.content
                if "OBS:" in texto and "CON:" in texto:
                    st.session_state.ia_resp["obs"] = texto.split("OBS:")[1].split("CON:")[0].strip()
                    st.session_state.ia_resp["concl"] = texto.split("CON:")[1].strip()
                st.rerun()
            except: st.error("Error en IA")

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_resp["obs"])
f_con = st.text_area("5. Conclusiones", value=st.session_state.ia_resp["concl"])

# --- GESTIÓN DE IMÁGENES (CORREGIDO EL BORRADO) ---
st.subheader("📸 Galería de Evidencias")
uploader = st.file_uploader("Añadir Fotos", type=['png','jpg','jpeg'], accept_multiple_files=True)

if uploader:
    for f in uploader:
        if not any(img['name'] == f.name for img in st.session_state.fotos):
            img_bytes = f.read()
            st.session_state.fotos.append({'file': img_bytes, 'name': f.name, 'desc': "Evidencia técnica."})

# Renderizar y borrar miniaturas
for idx, foto in enumerate(st.session_state.fotos):
    c_img, c_desc, c_del = st.columns([1, 3, 0.5])
    with c_img:
        st.image(foto['file'], width=120)
    with c_desc:
        # Actualización de descripción en tiempo real
        st.session_state.fotos[idx]['desc'] = st.text_input(f"Descripción #{idx+1}", value=foto['desc'], key=f"t_{foto['name']}_{idx}")
    with c_del:
        # Función de borrado con rerun inmediato
        if st.button("🗑️", key=f"del_{foto['name']}_{idx}"):
            st.session_state.fotos.pop(idx)
            st.rerun()

# --- GENERACIÓN FINAL ---
if st.button("💾 GENERAR INFORME FINAL", use_container_width=True):
    payload = {
        "orden": orden_input, "cliente": f_cliente, "factura": f_fac, "fecha": date.today(),
        "producto": f_prod, "serie": f_serie, "rf": f_rf, "it": f_it, "re": f_re, 
        "obs": f_obs, "con": f_con
    }
    st.session_state.pdf_data = generar_pdf_profesional(payload, st.session_state.fotos)
    st.success("✅ PDF generado correctamente.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Reporte Justificado", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_input}.pdf", mime="application/pdf")
