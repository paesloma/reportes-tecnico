import streamlit as st
import pandas as pd
from datetime import date, datetime
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab para el PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader # Necesario para leer la imagen de fondo

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

# --- 2. CARGA DE DATOS (BLINDADA) ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                df.columns = df.columns.str.strip()
                nombres_clave = {'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'}
                df = df.rename(columns=nombres_clave)
                return df
            except: continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- NUEVA FUNCIÓN: MARCA DE AGUA ---
def agregar_marca_agua(canvas, doc):
    """Dibuja la marca de agua en el fondo de la página."""
    # Nombre del archivo de imagen de marca de agua
    watermark_file = "watermark.png"
    
    if os.path.exists(watermark_file):
        # Guardamos el estado actual del canvas
        canvas.saveState()
        
        # Establecemos la transparencia (0.1 es muy transparente, 1.0 es opaco)
        # Ajusta este valor si la quieres más o menos visible. 0.15 es un buen punto medio.
        canvas.setFillAlpha(0.15)
        
        # Obtenemos las dimensiones de la página (Carta/Letter)
        page_width, page_height = canvas._pagesize
        
        # Dibujamos la imagen.
        # (0, 0) es la esquina inferior izquierda.
        # width y height cubren toda la página.
        # preserveAspectRatio=True asegura que el logo no se deforme, 
        # anchor='c' lo centra en el área total de la página.
        canvas.drawImage(watermark_file, 0, 0, width=page_width, height=page_height, 
                         mask='auto', preserveAspectRatio=True, anchor='c')
        
        # Restauramos el estado del canvas para no afectar al texto siguiente
        canvas.restoreState()

# --- 3. FUNCIÓN GENERAR PDF (MODIFICADA) ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    # Definimos márgenes. Top margin un poco más alto para el título.
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    try: color_principal = colors.HexColor("#003366")
    except AttributeError: color_principal = colors.hexColor("#003366")

    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_principal, spaceAfter=20)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_principal, borderPadding=3, spaceBefore=10)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)

    story = []
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    # story.append(Spacer(1, 10)) # Espacio eliminado, el título ya tiene spaceAfter
    
    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    # Tabla un poco más ancha para aprovechar el espacio
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)
    story.append(Spacer(1, 15))

    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Ingresa a servicio técnico", datos['ingreso_tec']),
        ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']),
        ("4. Observaciones", datos['observaciones']),
        ("5. Conclusiones", datos['conclusiones'])
    ]

    for titulo, contenido in secciones:
        story.append(Paragraph(titulo, est_sec))
        # Reemplazamos saltos de línea por <br/> para que ReportLab los respete
        story.append(Paragraph(contenido.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 5))

    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        story.append(Spacer(1, 10))
        for img_file in imagenes_cargadas:
            try:
                img_file.seek(0)
                p_img = PilImage.open(img_file)
                img_b = BytesIO()
                if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
                # Calidad alta para las fotos
                p_img.save(img_b, format='JPEG', quality=85)
                img_b.seek(0)
                # Imágenes un poco más grandes
                story.append(Image(img_b, width=3.2*inch, height=2.4*inch))
                story.append(Spacer(1, 15))
            except Exception as e:
                 print(f"Error imagen: {e}")

    # AQUÍ ESTÁ LA CLAVE: Se pasa la función de marca de agua al construir el PDF
    # onFirstPage se aplica a la primera página, onLaterPages a todas las siguientes.
    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

# Búsqueda de Orden
with st.container():
    st.subheader("1. Localizar Orden")
    orden_id = st.text_input("Ingrese número de Orden")
    c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()
    if orden_id and not df_db.empty:
        res = df_db[df_db['Orden'] == orden_id]
        if not res.empty:
            row = res.iloc[0]
            c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
            try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
            except: pass
            st.success("✅ Datos cargados correctamente.")

st.markdown("---")

# Formulario
with st.form("form_tecnico"):
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    
    col1, col2 = st.columns(2)
    with col1:
        f_cliente = st.text_input("Cliente", value=c_v)
        f_prod = st.text_input("Producto", value=p_v)
        f_serie = st.text_input("Serie/Artículo", value=s_v)
    with col2:
        f_fac = st.text_input("Factura", value=f_v)
        f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
        f_tecnico = st.selectbox("Técnico Asignado", options=LISTA_TECNICOS)
    
    f_rev_fisica = st.text_area("1. Revisión Física")
    f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
    
    t_electro = "Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo."
    f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value=t_electro)
    
    f_obs = st.text_area("4. Observaciones", value="Luego de la revisión del artículo se observa lo siguiente: ")

    concl_map = {
        "FUERA DE GARANTIA": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
        "INFORME TECNICO": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales",
        "RECLAMO AL PROVEEDOR": "Se concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
    }
    f_conclusiones = st.text_area("5. Conclusiones", value=concl_map[tipo_rep])
    
    f_fotos = st.file_uploader("Evidencia Fotográfica", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    preparar = st.form_submit_button("💾 PREPARAR REPORTE")

# Botón de descarga
if preparar:
    if f_cliente and f_conclusiones:
        # Verificar que exista la imagen de marca de agua antes de generar
        if not os.path.exists("watermark.png"):
             st.warning("⚠️ ADVERTENCIA: No se encontró el archivo 'watermark.png'. El reporte se generará sin marca de agua.")

        pdf_data = generar_pdf({
            "tipo_reporte": tipo_rep, "orden": orden_id, "cliente": f_cliente,
            "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod,
            "serie": f_serie, "tecnico": f_tecnico, "fecha_hoy": date.today(),
            "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
            "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_conclusiones
        }, f_fotos)
        
        st.success("✅ El informe ha sido generado exitosamente.")
        st.download_button("📥 DESCARGAR INFORME PDF", data=pdf_data, file_name=f"Informe_Tecnico_{orden_id}.pdf")
    else:
        st.error("Por favor, complete los campos obligatorios antes de generar el reporte.")
