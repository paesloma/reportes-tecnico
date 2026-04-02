import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# --- 0. CONFIGURACIÓN DE IA ---
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🔧", layout="centered")

if 'lista_fotos' not in st.session_state: st.session_state.lista_fotos = []
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""

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

# --- 3. FUNCIONES DE GENERACIÓN ---

def dibujar_fondo(canvas, doc):
    """Aplica la marca de agua en el fondo de cada página."""
    if os.path.exists("marca_agua.png"):
        canvas.saveState()
        canvas.drawImage("marca_agua.png", 1*inch, 2*inch, width=6.5*inch, height=6.5*inch, mask='auto', preserveAspectRatio=True)
        canvas.restoreState()

def generar_pdf(datos, fotos):
    buffer = BytesIO()
    # Márgenes ajustados para scannability
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.6*inch, rightMargin=0.6*inch)
    
    color_azul = colors.HexColor("#0056b3")
    
    # ESTILOS
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=4, spaceBefore=15, spaceAfter=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=12, alignment=TA_JUSTIFY)
    est_firma_cargo = ParagraphStyle('FC', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
    est_firma_nombre = ParagraphStyle('FN', fontSize=9, alignment=TA_CENTER, fontName='Helvetica')

    story = []
    
    # Encabezado Logos
    if os.path.exists("logo.png") and os.path.exists("logo_derecho.png"):
        header = Table([[Image("logo.png", width=1.6*inch, height=0.65*inch), Image("logo_derecho.png", width=1.6*inch, height=0.65*inch)]], colWidths=[3.65*inch, 3.65*inch])
        header.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
        story.append(header)

    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    # Tabla de Datos Principales
    info = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
            [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"],
            [f"Serie: {datos['serie']}", f"Fecha Reporte: {datos['fecha_hoy']}"]]
    t = Table(info, colWidths=[3.65*inch, 3.65*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9), ('PADDING', (0,0), (-1,-1), 5)]))
    story.append(t)

    # Secciones Justificadas
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Revisión Técnica", datos['rev_electro']), 
        ("3. Observaciones", datos['observaciones']), 
        ("4. Conclusiones", datos['conclusiones'])
    ]

    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Spacer(1, 5))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
    
    # Evidencia Fotográfica
    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for f in fotos:
            img = Image(BytesIO(f['data']), width=2.6*inch, height=1.9*inch)
            ft = Table([[img, Paragraph(f['desc'], est_txt)]], colWidths=[2.8*inch, 4.5*inch])
            ft.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 15)]))
            story.append(ft)

    # Bloque de Firmas Centrado y Sin Línea
    story.append(Spacer(1, 60))
    firmas = [
        [Paragraph("Realizado por:", est_firma_cargo), Paragraph("Revisado por:", est_firma_cargo)],
        [Paragraph(datos['realizador'], est_firma_nombre), Paragraph(datos['tecnico'], est_firma_nombre)]
    ]
    tf = Table(firmas, colWidths=[3.65*inch, 3.65*inch])
    tf.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(tf)

    doc.build(story, onFirstPage=dibujar_fondo, onLaterPages=dibujar_fondo)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ DE USUARIO ---
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
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_hoy = st.date_input("Fecha Reporte", value=date.today())
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_daño = st.text_area("🔧 Análisis de Fallo (IA)")
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("IA trabajando..."):
            prompt = f"Analiza: {f_daño} en {f_prod}. Devuelve REVISION_TEC: [pasos] y OBSERVACIONES: [conclusiones]. Sin asteriscos."
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.replace("*", "").strip()
            if "REVISION_TEC:" in clean:
                st.session_state.ai_rev_electro = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ai_obs = clean.split("OBSERVACIONES:")[1].strip()
            st.rerun()

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones")

# Subida de fotos
st.subheader("🖼️ Evidencia Fotográfica")
up_files = st.file_uploader("Añadir fotos", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if up_files:
    for f in up_files:
        if f.name not in [x['name'] for x in st.session_state.lista_fotos]:
            st.session_state.lista_fotos.append({"name": f.name, "data": f.getvalue(), "desc": "Evidencia técnica."})

for i, foto in enumerate(st.session_state.lista_fotos):
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 0.5])
        c1.image(foto['data'], width=100)
        st.session_state.lista_fotos[i]['desc'] = c2.text_input(f"Descripción #{i+1}", value=foto['desc'], key=f"d_{i}")
        if c3.button("🗑️", key=f"b_{i}"):
            st.session_state.lista_fotos.pop(i)
            st.session_state.uploader_key += 1
            st.rerun()

if st.button("💾 GENERAR INFORME PDF", use_container_width=True):
    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador, "fecha_hoy": f_fec_hoy, "rev_fisica": f_rev_fisica, "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl}
    pdf_bytes = generar_pdf(datos, st.session_state.lista_fotos)
    st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name=f"Reporte_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
