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
# Se recomienda usar st.secrets["GROQ_API_KEY"] en Streamlit Cloud por seguridad
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'txt_data' not in st.session_state: st.session_state.txt_data = None

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

# CONSTANTES
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. FUNCIONES DE GENERACIÓN ---
def limpiar_texto_ia(texto):
    """Elimina asteriscos y espacios extra del texto de la IA."""
    return texto.replace("*", "").strip()

def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    color_azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []
    # Logos (opcionales si existen)
    if os.path.exists("logo.png") and os.path.exists("logo_derecho.png"):
        header_table = Table([[Image("logo.png", width=1.4*inch, height=0.55*inch), Image("logo_derecho.png", width=1.4*inch, height=0.55*inch)]], colWidths=[3.7*inch, 3.7*inch])
        header_table.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
        story.append(header_table)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    # Datos generales
    info = [[Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
            [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt)],
            [Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt), Paragraph(f"<b>Fecha:</b> {datos['fecha_hoy']}", est_txt)]]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    # Solo incluimos la revisión física formal en el PDF
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Análisis Técnico", datos['rev_electro']),
        ("3. Observaciones", datos['observaciones']),
        ("4. Conclusiones", datos['conclusiones'])
    ]
    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
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
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Técnico", options=LISTA_TECNICOS)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

# NUEVA CASILLA PARA EL DAÑO (Solo para uso interno e IA)
f_daño = st.text_area("🔧 Daño detectado (interno)", placeholder="Ej: Antena del magnetrón dañada, humedad en tarjeta principal...")

# REVISIÓN FÍSICA (Lo que irá en el PDF)
f_rev_fisica = st.text_area("1. Revisión Física (para PDF)", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("Analizando daño..."):
            try:
                # La IA analiza el daño y la revisión física para crear el reporte
                prompt = f"Producto: {f_prod}. Daño: {f_daño}. Genera REVISION_TEC: [pasos de inspección] y OBSERVACIONES: [consecuencias del daño]. Sin asteriscos."
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                ai_text = limpiar_texto_ia(response.choices[0].message.content)
                if "REVISION_TEC:" in ai_text:
                    st.session_state.ai_rev_electro = ai_text.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                    st.session_state.ai_obs = ai_text.split("OBSERVACIONES:")[1].strip()
                st.rerun()
            except Exception as e: st.error("Límite de cuota excedido. Por favor, espera un momento.")

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones")

if st.button("💾 GENERAR PDF"):
    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_v, "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": "Pablo Lopez", "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl}
    st.session_state.pdf_data = generar_pdf(datos, [])
    st.success("✅ Reporte generado")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_id}.pdf", mime="application/pdf")
