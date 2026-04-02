import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
import google.generativeai as genai
import time

# --- 0. CONFIGURACIÓN DE SEGURIDAD Y API ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Se usa gemini-2.0-flash para evitar errores 404 de modelos antiguos
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

# Listas de selección
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Andres Mejia", "Tec. Juan Perez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
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
    est_txt = ParagraphStyle('Normal', fontSize=9, leading=12)
    est_tit = ParagraphStyle('Sec', fontSize=10, fontName='Helvetica-Bold', textColor=colors.whitesmoke, backColor=colors.navy, borderPadding=3)
    
    story = []
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 12))
    
    tbl_data = [
        [f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
        [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"],
        [f"Serie: {datos['serie']}", f"Fecha: {datos['fecha_hoy']}"]
    ]
    t = Table(tbl_data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    
    secciones = [("REVISIÓN FÍSICA", datos['rev_fisica']), ("ANÁLISIS TÉCNICO", datos['rev_electro']), ("OBSERVACIONES", datos['obs_ia']), ("CONCLUSIONES", datos['conclusiones'])]
    for tit, cont in secciones:
        story.append(Spacer(1, 10))
        story.append(Paragraph(tit, est_tit))
        story.append(Paragraph(cont if cont else "N/A", est_txt))
    
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

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_input = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""
if orden_input and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_input]
    if not res.empty:
        c_v, s_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Serie'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

st.markdown("### Datos del Reporte")
col1, col2 = st.columns(2)
with col1:
    tipo = st.selectbox("Tipo de Reporte", OPCIONES_REPORTE)
    realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
    cliente = st.text_input("Cliente", value=c_v)
    producto = st.text_input("Producto", value=p_v)
with col2:
    tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)
    factura = st.text_input("Factura", value=f_v)
    fec_factura = st.date_input("Fecha Factura", value=date.today())
    serie = st.text_input("Serie/Artículo", value=s_v)

rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {producto}. Se observa el uso continuo del artículo.")

# --- ASISTENTE DE IA ---
st.markdown("### ✨ Asistente de IA")
mensaje_ia = st.empty()
if st.button("🤖 Autocompletar con IA"):
    if ia_disponible and rev_fisica:
        with st.spinner("Generando análisis..."):
            try:
                prompt = f"Analiza técnicamente: {rev_fisica}. Formato: ELECTRO: [pasos técnicos] OBS: [observaciones técnicas]"
                response = model.generate_content(prompt)
                res_text = response.text
                if "ELECTRO:" in res_text:
                    st.session_state.ai_electro = res_text.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = res_text.split("OBS:")[1].strip()
                st.rerun()
            except Exception as e:
                if "429" in str(e):
                    mensaje_ia.warning("⚠️ Cuota excedida. Iniciando recuperación de seguridad...")
                    placeholder = st.empty()
                    barra = st.progress(0)
                    for i in range(70, 0, -1):
                        placeholder.subheader(f"⏳ Reintentando en {i} segundos...")
                        barra.progress((70 - i + 1) / 70)
                        time.sleep(1)
                    placeholder.empty()
                    barra.empty()
                    mensaje_ia.info("🔄 Ya puedes intentar de nuevo.")
                else:
                    st.error(f"Error: {e}")

rev_electro = st.text_area("2. Revisión Técnica (IA)", value=st.session_state.ai_electro)
obs_ia = st.text_area("3. Observaciones (IA)", value=st.session_state.ai_obs)
conclusiones = st.text_area("4. Conclusiones finales")

# --- 5. IMÁGENES ---
st.markdown("### 📸 Evidencia Fotográfica")
archivos = st.file_uploader("Subir fotos", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
fotos_preparadas = []
if archivos:
    for i, file in enumerate(archivos):
        desc = st.text_input(f"Descripción imagen {i+1}", value="Evidencia de revisión", key=f"img_{i}")
        img_pil = PilImage.open(file).convert('RGB')
        img_buf = BytesIO()
        img_pil.save(img_buf, format='JPEG')
        img_buf.seek(0)
        fotos_preparadas.append({'img': img_buf, 'desc': desc})

# --- 6. GENERACIÓN ---
if st.button("💾 GENERAR REPORTE PDF", use_container_width=True):
    datos = {
        'orden': orden_input, 'cliente': cliente, 'producto': producto,
        'factura': factura, 'serie': serie, 'fecha_hoy': date.today(),
        'rev_fisica': rev_fisica, 'rev_electro': rev_electro, 
        'obs_ia': obs_ia, 'conclusiones': conclusiones
    }
    st.session_state.pdf_data = generar_pdf(datos, fotos_preparadas)
    st.success("✅ PDF listo para descarga.")

if st.session_state.pdf_data:
    st.download_button("📥 Descargar Informe", st.session_state.pdf_data, f"Reporte_{orden_input}.pdf", "application/pdf")
