import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq # <--- Nueva integración

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🚀", layout="centered")

# Inicializar estados
if 'fotos_lista' not in st.session_state:
    st.session_state.fotos_lista = []
if 'ia_llenado' not in st.session_state:
    st.session_state.ia_llenado = {"rf": "", "it": "", "re": "", "obs": ""}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Configuración de Cliente Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets de Streamlit.")
    st.stop()

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_datos_servicios()

# CONSTANTES
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]
TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación...",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente...",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas..."
}

# --- 3. FUNCIONES DE GENERACIÓN ---
def generar_pdf_pro(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=azul, borderPadding=3, spaceBefore=10)
    est_just = ParagraphStyle('J', fontSize=9, leading=12, alignment=TA_JUSTIFY)
    
    story = []
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=1.5*inch, height=0.5*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 10))
    
    # Tabla Info
    info_tbl = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
                [f"Cliente: {datos['cliente']}", f"Fecha: {datos['fecha_hoy']}"]]
    t = Table(info_tbl, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(t)

    # Secciones técnicas
    secciones = [("1. Revisión Física", datos['rf']), ("2. Ingresa a ST", datos['it']), 
                 ("3. Revisión Electro-Mecánica", datos['re']), ("4. Observaciones", datos['obs']), 
                 ("5. Conclusiones", datos['con'])]
    
    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_just))

    # Imágenes
    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for f in fotos:
            img = Image(BytesIO(f['file']), width=2.4*inch, height=1.7*inch)
            story.append(Table([[img, Paragraph(f['desc'], est_just)]], colWidths=[2.6*inch, 4.4*inch]))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")
orden_id = st.text_input("Ingrese número de Orden")

# Lógica de autocompletado
c_v, p_v, s_v, f_v = "", "", "", ""
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        c_v, p_v, s_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Producto'], res.iloc[0]['Serie'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura")
    f_serie = st.text_input("Serie/Artículo", value=s_v)

st.markdown("---")

# --- BOTÓN DE IA (Solo llena campos técnicos) ---
f_diag_ia = st.text_area("🤖 Describa la falla para que la IA llene el informe")
if st.button("Llenar Campos Técnicos con IA"):
    if f_diag_ia:
        with st.spinner("Procesando..."):
            prompt = f"Producto: {f_prod}. Falla: {f_diag_ia}. Genera 4 textos técnicos para un reporte: 1) Revision Fisica, 2) Ingreso a ST, 3) Revision Electromecanica, 4) Observaciones. Formato: RF: [texto] IT: [texto] RE: [texto] OBS: [texto]"
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile").choices[0].message.content
            # Parsing simple
            try:
                st.session_state.ia_llenado["rf"] = res.split("RF:")[1].split("IT:")[0].strip()
                st.session_state.ia_llenado["it"] = res.split("IT:")[1].split("RE:")[0].strip()
                st.session_state.ia_llenado["re"] = res.split("RE:")[1].split("OBS:")[0].strip()
                st.session_state.ia_llenado["obs"] = res.split("OBS:")[1].strip()
                st.rerun()
            except: st.error("Error al procesar la respuesta de la IA.")

# Campos del Formulario
f_rf = st.text_area("1. Revisión Física", value=st.session_state.ia_llenado["rf"] if st.session_state.ia_llenado["rf"] else f"Ingresa {f_prod}...")
f_it = st.text_area("2. Ingresa a servicio técnico", value=st.session_state.ia_llenado["it"])
f_re = st.text_area("3. Revisión electro-electrónica-mecanica", value=st.session_state.ia_llenado["re"])
f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_llenado["obs"])

# Conclusiones (Manuales por tipo de reporte)
f_concl = st.text_area("5. Conclusiones", value=TEXTOS_CONCLUSIONES.get(tipo_rep, ""), height=120)

# --- GALERÍA CON MINIATURAS Y BORRADO ---
st.markdown("### 📸 Evidencia Fotográfica")
uploader = st.file_uploader("Añadir Fotos", type=['png','jpg','jpeg'], accept_multiple_files=True)

if uploader:
    for f in uploader:
        if not any(img['name'] == f.name for img in st.session_state.fotos_lista):
            st.session_state.fotos_lista.append({'file': f.read(), 'name': f.name, 'desc': "Evidencia técnica."})

for idx, foto in enumerate(st.session_state.fotos_lista):
    c_img, c_desc, c_del = st.columns([1, 3, 0.5])
    with c_img: st.image(foto['file'], width=120)
    with c_desc: 
        st.session_state.fotos_lista[idx]['desc'] = st.text_input(f"Descripción #{idx+1}", value=foto['desc'], key=f"d_{idx}")
    with c_del:
        if st.button("🗑️", key=f"del_{idx}"):
            st.session_state.fotos_lista.pop(idx)
            st.rerun()

# --- GENERACIÓN ---
if st.button("💾 GENERAR REPORTE FINAL", use_container_width=True):
    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_hoy": date.today(),
             "producto": f_prod, "rf": f_rf, "it": f_it, "re": f_re, "obs": f_obs, "con": f_concl}
    st.session_state.pdf_data = generar_pdf_pro(datos, st.session_state.fotos_lista)
    st.success("✅ PDF Generado")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_id}.pdf")
