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

# --- 1. CONFIGURACIÓN Y PERSISTENCIA (EVITA KEYERROR) ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", layout="centered")

if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev_tec": "", "obs": "", "concl": ""}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None

# Cliente Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets.")
    st.stop()

# --- 2. CARGA DE DATOS ---
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

# --- CONSTANTES ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. FUNCIONES DE GENERACIÓN (PDF JUSTIFICADO) ---
def agregar_marca_agua(canvas, doc):
    if os.path.exists("watermark.png"):
        canvas.saveState()
        canvas.setFillAlpha(0.12)
        canvas.drawImage("watermark.png", 0, 0, width=canvas._pagesize[0], height=canvas._pagesize[1], mask='auto', preserveAspectRatio=True, anchor='c')
        canvas.restoreState()

def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    color_azul = colors.HexColor("#0056b3")
    
    styles = getSampleStyleSheet()
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=4, spaceBefore=12, spaceAfter=6)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=12, alignment=TA_JUSTIFY)
    
    story = []
    
    # Encabezado (Logos)
    col_izq = [Image("logo.png", width=1.4*inch, height=0.55*inch)] if os.path.exists("logo.png") else []
    col_der = [Image("logo_derecho.png", width=1.4*inch, height=0.55*inch)] if os.path.exists("logo_derecho.png") else []
    header = Table([[col_izq, col_der]], colWidths=[3.7*inch, 3.7*inch])
    header.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Tabla de Datos
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", ""] else datos['factura']
    info = [
        [f"Orden: {datos['orden']}", f"Factura: {fac_txt}"],
        [f"Cliente: {datos['cliente']}", f"Fec. Factura: {datos['fecha_factura']}"],
        [f"Producto: {datos['producto']}", f"Serie: {datos['serie']}"]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
    story.append(t)

    # Secciones Mantenidas y Justificadas
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Ingresa a servicio técnico", datos['ingreso_tec']),
        ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']),
        ("4. Observaciones", datos['obs']),
        ("5. Conclusiones", datos['concl'])
    ]

    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 4)) # Espacio extra entre párrafos

    if lista_imgs:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for idx, img_data in enumerate(lista_imgs):
            story.append(Spacer(1, 10))
            img_obj = Image(img_data['imagen'], width=2.4*inch, height=1.7*inch)
            t_img = Table([[img_obj, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{img_data['descripcion']}", est_txt)]], colWidths=[2.6*inch, 4.6*inch])
            story.append(t_img)

    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ STREAMLIT ---
st.title("🚀 Gestión de Reportes Técnicos")
orden_id = st.text_input("Ingrese número de Orden")

# Autocompletado
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(row.get('Fec_Fac_Min','')).date()
        except: pass

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

st.divider()

# Campos Mantenidos
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")
f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se procede a revisar el sistema de alimentación...\nSe procede a revisar el sistema electrónico...")

# IA SECCIÓN (MEJORADA PARA EVITAR ERRORES)
f_diag_ia = st.text_area("🔧 Diagnóstico de Entrada (Para IA)", placeholder="Describa la falla...")

if st.button("🤖 Generar Diagnóstico con IA"):
    if f_diag_ia:
        with st.spinner("Procesando..."):
            try:
                prompt = f"Producto: {f_prod}. Falla: {f_diag_ia}. Responde exactamente con este formato:\nTEC: [descripción técnica]\nOBS: [observaciones]\nCON: [conclusiones]"
                resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                clean = resp.choices[0].message.content
                # Separación segura para evitar "index out of range"
                if "TEC:" in clean and "OBS:" in clean and "CON:" in clean:
                    st.session_state.ia_data["rev_tec"] = clean.split("TEC:")[1].split("OBS:")[0].strip()
                    st.session_state.ia_data["obs"] = clean.split("OBS:")[1].split("CON:")[0].strip()
                    st.session_state.ia_data["concl"] = clean.split("CON:")[1].strip()
                st.rerun()
            except Exception as e:
                st.error(f"Error de IA: {e}. Verifique API Key.")

f_final_obs = st.text_area("4. Observaciones", value=st.session_state.ia_data["obs"])
f_final_con = st.text_area("5. Conclusiones", value=st.session_state.ia_data["concl"])

# Imágenes
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
descs = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        descs.append(st.text_input(f"Descripción Foto #{idx+1}", value="Evidencia técnica.", key=f"d_{idx}"))

# Generación
if st.button("💾 GENERAR ARCHIVOS FINAL", use_container_width=True):
    lista_imgs = []
    for f, d in zip(uploaded_files, descs):
        img_b = BytesIO()
        PilImage.open(f).convert('RGB').save(img_b, format='JPEG')
        img_b.seek(0)
        lista_imgs.append({"imagen": img_b, "descripcion": d})

    datos = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
        "producto": f_prod, "serie": f_serie, "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
        "rev_electro": f_rev_electro, "obs": f_final_obs, "concl": f_final_con
    }
    st.session_state.pdf_data = generar_pdf(datos, lista_imgs)
    st.success("✅ Reporte listo para descargar.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar PDF Justificado", data=st.session_state.pdf_data, file_name=f"Informe_{orden_id}.pdf", mime="application/pdf")
