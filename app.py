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
from reportlab.lib.enums import TA_JUSTIFY # Para justificar texto

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Generador de Reportes Pro", page_icon="🔧")

# Inicialización de estados para evitar KeyError
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev_tec": "", "obs": "", "concl": ""}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# Configuración de Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets de Streamlit.")
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

# --- 3. FUNCIONES DE DISEÑO (PDF JUSTIFICADO) ---
def generar_pdf_pro(datos, lista_imgs):
    buffer = BytesIO()
    # Márgenes amplios para mayor claridad
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # ESTILO JUSTIFICADO Y CON ESPACIADO
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, spaceAfter=20, fontName='Helvetica-Bold', textColor=colors.HexColor("#0056b3"))
    est_seccion = ParagraphStyle('S', fontSize=11, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.HexColor("#0056b3"), borderPadding=4, spaceBefore=15, spaceAfter=8)
    est_justificado = ParagraphStyle('J', fontSize=10, fontName='Helvetica', leading=14, alignment=TA_JUSTIFY, spaceAfter=10)
    
    story = []
    
    # Logos y Encabezado
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Tabla de Datos Generales
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", ""] else datos['factura']
    info_table = [
        [f"Orden: {datos['orden']}", f"Factura: {fac_txt}"],
        [f"Cliente: {datos['cliente']}", f"Fecha Fac: {datos['fecha_factura']}"],
        [f"Producto: {datos['producto']}", f"Serie: {datos['serie']}"]
    ]
    t = Table(info_table, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Secciones con texto justificado y separación extra
    secciones = [
        ("1. REVISIÓN FÍSICA", datos['rev_fisica']),
        ("2. REVISIÓN TÉCNICA", datos['rev_tec']),
        ("3. OBSERVACIONES", datos['obs']),
        ("4. CONCLUSIONES", datos['concl'])
    ]

    for titulo, contenido in secciones:
        story.append(Paragraph(titulo, est_seccion))
        story.append(Paragraph(contenido.replace('\n', '<br/>'), est_justificado))
        story.append(Spacer(1, 5)) # Espacio extra entre bloques

    # Imágenes con pie de foto
    if lista_imgs:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_seccion))
        for img_data in lista_imgs:
            story.append(Spacer(1, 10))
            img = Image(img_data['imagen'], width=2.5*inch, height=1.8*inch)
            t_img = Table([[img, Paragraph(img_data['desc'], est_justificado)]], colWidths=[2.8*inch, 4*inch])
            story.append(t_img)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ STREAMLIT ---
st.title("🚀 Gestión de Reportes")
orden_id = st.text_input("Orden #")

# Autocompletado (resumido)
c_v, p_v, s_v, f_v, ff_v = "", "", "", "", date.today()
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, p_v, s_v, f_v = row.get('Cliente',''), row.get('Producto',''), row.get('Serie',''), row.get('Fac_Min','')

col1, col2 = st.columns(2)
with col1:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_fac = st.text_input("Factura", value=f_v)
    f_serie = st.text_input("Serie", value=s_v)

st.divider()

# Sección de IA corregida
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")
f_diag_ia = st.text_area("🔧 Diagnóstico de Entrada (IA)", placeholder="Describa el daño aquí...")

if st.button("🤖 Generar Diagnóstico con IA"):
    if f_diag_ia:
        with st.spinner("IA Generando informe..."):
            try:
                prompt = f"Producto: {f_prod}. Falla: {f_diag_ia}. Genera REVISION_TEC, OBSERVACIONES y CONCLUSIONES por separado."
                resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                raw = resp.choices[0].message.content
                # Lógica de separación simple (puedes mejorarla según el formato de la IA)
                st.session_state.ia_data["rev_tec"] = raw.split("OBSERVACIONES")[0].replace("REVISION_TEC:", "").strip()
                st.session_state.ia_data["obs"] = raw.split("OBSERVACIONES:")[1].split("CONCLUSIONES")[0].strip()
                st.session_state.ia_data["concl"] = raw.split("CONCLUSIONES:")[1].strip()
                st.rerun()
            except Exception as e:
                st.error(f"Error de IA: {e}. Verifique su conexión y API Key.")

# Campos finales que se guardan en el PDF
f_tec = st.text_area("2. Revisión Técnica", value=st.session_state.ia_data["rev_tec"])
f_obs = st.text_area("3. Observaciones", value=st.session_state.ia_data["obs"])
f_con = st.text_area("4. Conclusiones", value=st.session_state.ia_data["concl"])

# Botón de Generación Final
if st.button("💾 GENERAR PDF JUSTIFICADO"):
    datos_pdf = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": date.today(),
        "producto": f_prod, "serie": f_serie, "rev_fisica": f_rev_fisica,
        "rev_tec": f_tec, "obs": f_obs, "concl": f_con
    }
    st.session_state.pdf_data = generar_pdf_pro(datos_pdf, [])
    st.success("PDF generado con éxito.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Reporte Justificado", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_id}.pdf")
