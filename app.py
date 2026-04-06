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

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🚀", layout="centered")

try:
    # Asegúrate de tener tu GROQ_API_KEY en los Secrets de Streamlit
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 Error: Configure una API Key válida en los Secrets de Streamlit.")
    st.stop()

# --- 2. INICIALIZACIÓN DE ESTADOS (EVITA KEYERROR) ---
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev_tec": "", "obs": "", "concl": ""}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- 3. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, engine='python')
                df.columns = df.columns.str.strip()
                df = df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
                return df
            except: continue
    return pd.DataFrame()

df_db = cargar_datos_servicios()

# --- CONSTANTES ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 4. FUNCIONES DE GENERACIÓN (PDF & TXT) ---
def agregar_marca_agua(canvas, doc):
    if os.path.exists("watermark.png"):
        canvas.saveState()
        canvas.setFillAlpha(0.12)
        canvas.drawImage("watermark.png", 0, 0, width=canvas._pagesize[0], height=canvas._pagesize[1], mask='auto', preserveAspectRatio=True, anchor='c')
        canvas.restoreState()

def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    color_azul = colors.HexColor("#0056b3")
    
    styles = getSampleStyleSheet()
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    
    story = []
    
    # Cabecera con Logos
    col_izq = [Image("logo.png", width=1.4*inch, height=0.55*inch)] if os.path.exists("logo.png") else []
    col_der = [Image("logo_derecho.png", width=1.4*inch, height=0.55*inch)] if os.path.exists("logo_derecho.png") else []
    
    header = Table([[col_izq, col_der]], colWidths=[3.7*inch, 3.7*inch])
    header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    # Tabla de Información
    fac_label = "STOCK" if str(datos['factura']).strip() in ["0", ""] else datos['factura']
    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {fac_label}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {date.today()}", est_txt)]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Revisión Técnica", datos['rev_tec']),
        ("3. Observaciones", datos['obs']),
        ("4. Conclusiones", datos['concl'])
    ]

    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))

    # Imágenes
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

# --- 5. INTERFAZ DE USUARIO ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(row.get('Fec_Fac_Min','')).date()
        except: pass

st.markdown("### Datos del Reporte")
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
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.") #

# --- BLOQUE IA ---
f_diag_ia = st.text_area("🔧 Diagnóstico de Entrada (Para IA)", placeholder="Describa la falla para que la IA genere el reporte...")

if st.button("🤖 Generar con Inteligencia Artificial", use_container_width=True):
    if f_diag_ia:
        with st.spinner("IA procesando diagnóstico..."):
            prompt = f"Producto: {f_prod}. Falla: {f_diag_ia}. Genera: REVISION_TEC, OBSERVACIONES, CONCLUSIONES."
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content
            if "REVISION_TEC:" in clean:
                st.session_state.ia_data["rev_tec"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ia_data["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ia_data["concl"] = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

f_final_rev = st.text_area("2. Revisión Técnica", value=st.session_state.ia_data["rev_tec"])
f_final_obs = st.text_area("3. Observaciones", value=st.session_state.ia_data["obs"])
f_final_con = st.text_area("4. Conclusiones", value=st.session_state.ia_data["concl"], height=150)

# --- FOTOS ---
st.markdown("### 📸 Evidencia Fotográfica")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
descripciones = []

if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        c_img, c_desc = st.columns([1, 3])
        with c_img: st.image(file, use_container_width=True)
        with c_desc: descripciones.append(st.text_input(f"Descripción #{idx+1}", value="Evidencia técnica.", key=f"d_{idx}"))

# --- GENERACIÓN FINAL ---
if st.button("💾 GUARDAR Y GENERAR ARCHIVOS", use_container_width=True):
    lista_imgs_final = []
    for file, desc in zip(uploaded_files, descripciones):
        p_img = PilImage.open(file).convert('RGB')
        img_byte = BytesIO()
        p_img.save(img_byte, format='JPEG')
        img_byte.seek(0)
        lista_imgs_final.append({"imagen": img_byte, "descripcion": desc})

    datos = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
        "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador,
        "rev_fisica": f_rev_fisica, "rev_tec": f_final_rev, "obs": f_final_obs, "concl": f_final_con
    }
    
    st.session_state.pdf_data = generar_pdf(datos, lista_imgs_final)
    st.session_state.txt_data = f"CLIENTE: {f_cliente}\nORDEN: {orden_id}\nCONCLUSIONES:\n{f_final_con}"
    st.success("✅ Archivos listos")

# --- DESCARGAS ---
if st.session_state.pdf_data:
    col_d1, col_d2 = st.columns(2)
    with col_d1: st.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Informe_{orden_id}.pdf", mime="application/pdf")
    with col_d2: st.download_button("📥 Descargar TXT", data=st.session_state.txt_data, file_name=f"Status_{orden_id}.txt", mime="text/plain")
