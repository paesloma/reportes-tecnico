import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
import google.generativeai as genai

# --- 0. CONFIGURACIÓN DE SEGURIDAD Y API ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Usamos 2.0-flash para evitar errores 404 de modelos antiguos
        model = genai.GenerativeModel('gemini-2.0-flash')
        ia_disponible = True
    else:
        st.error("Error: GEMINI_API_KEY no encontrada en los Secrets.")
        ia_disponible = False
except Exception as e:
    st.error(f"Error de configuración: {e}")
    ia_disponible = False

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🚀", layout="centered")

# Inicialización de estados para evitar pérdida de datos al recargar
if 'ai_electro' not in st.session_state: st.session_state.ai_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None

# --- 2. CARGA DE BASE DE DATOS (CSV) ---
@st.cache_data
def cargar_datos():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1', sep=None, engine='python')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_datos()

# --- CONSTANTES ---
LISTA_TECNICOS = ["Técnico A", "Técnico B", "Técnico C"] # Nombres protegidos por privacidad
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. FUNCIONES DE GENERACIÓN DE PDF ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_pdf(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    est_txt = ParagraphStyle('Normal', fontSize=9)
    est_tit = ParagraphStyle('Sec', fontSize=10, fontName='Helvetica-Bold', textColor=colors.whitesmoke, backColor=colors.navy, borderPadding=3)
    
    story = []
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 12))
    
    # Tabla de datos generales
    tbl_data = [
        [f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
        [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"],
        [f"Serie: {datos['serie']}", f"Fecha: {datos['fecha_hoy']}"]
    ]
    t = Table(tbl_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    
    # Secciones de texto
    secciones = [("REVISIÓN FÍSICA", datos['rev_fisica']), ("ANÁLISIS TÉCNICO", datos['rev_electro']), ("CONCLUSIONES", datos['conclusiones'])]
    for tit, cont in secciones:
        story.append(Spacer(1, 10))
        story.append(Paragraph(tit, est_tit))
        story.append(Paragraph(cont, est_txt))
    
    # Inserción de imágenes
    if fotos:
        story.append(Spacer(1, 15))
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_tit))
        for f in fotos:
            img = Image(f['img'], width=2.5*inch, height=2*inch)
            story.append(Spacer(1, 8))
            story.append(Table([[img, Paragraph(f['desc'], est_txt)]], colWidths=[2.7*inch, 4.3*inch]))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ DE USUARIO (STREAMLIT) ---
st.title("🚀 Gestión de Reportes Técnicos")

# Búsqueda por Orden
orden_input = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, s_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Serie'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

# Formulario
col1, col2 = st.columns(2)
with col1:
    tipo = st.selectbox("Tipo de Reporte", OPCIONES_REPORTE)
    cliente = st.text_input("Cliente", value=c_v)
    producto = st.text_input("Producto", value=p_v)
with col2:
    tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)
    serie = st.text_input("Serie", value=s_v)
    factura = st.text_input("Factura", value=f_v)

rev_fisica = st.text_area("1. Revisión Física", value=f"Se recibe {producto} para evaluación.")

# Botón de IA con manejo de errores de cuota (429)
if st.button("🤖 Autocompletar con IA"):
    if ia_disponible and rev_fisica:
        with st.spinner("Analizando con Gemini..."):
            try:
                prompt = f"Analiza técnicamente: {rev_fisica}. Responde en este formato: ELECTRO: [pasos técnicos] OBS: [observaciones]"
                response = model.generate_content(prompt)
                res_text = response.text
                if "ELECTRO:" in res_text:
                    st.session_state.ai_electro = res_text.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = res_text.split("OBS:")[1].strip()
                st.rerun()
            except Exception as e:
                if "429" in str(e):
                    st.error("Límite de cuota excedido. Por favor, espera 60 segundos.")
                else:
                    st.error(f"Error: {e}")

rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_electro)
conclusiones = st.text_area("3. Conclusiones")

# --- 5. CARGA DE IMÁGENES ---
st.markdown("### 📸 Evidencia de Imágenes")
archivos = st.file_uploader("Subir fotos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
fotos_preparadas = []

if archivos:
    for i, file in enumerate(archivos):
        descripcion = st.text_input(f"Descripción para imagen {i+1}", value="Evidencia de estado del equipo", key=f"desc_{i}")
        # Procesamiento de imagen para PDF
        img_pil = PilImage.open(file)
        if img_pil.mode != 'RGB': img_pil = img_pil.convert('RGB')
        img_byteArr = BytesIO()
        img_pil.save(img_byteArr, format='JPEG')
        img_byteArr.seek(0)
        fotos_preparadas.append({'img': img_byteArr, 'desc': descripcion})

# --- 6. CIERRE Y DESCARGA ---
if st.button("💾 GENERAR REPORTE", use_container_width=True):
    datos_finales = {
        'orden': orden_input, 'cliente': cliente, 'producto': producto, 
        'factura': factura, 'serie': serie, 'fecha_hoy': date.today(),
        'rev_fisica': rev_fisica, 'rev_electro': rev_electro, 'conclusiones': conclusiones
    }
    st.session_state.pdf_data = generar_pdf(datos_finales, fotos_preparadas)
    st.success("Reporte generado con éxito.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Informe PDF", st.session_state.pdf_data, f"Reporte_{orden_input}.pdf", "application/pdf")
