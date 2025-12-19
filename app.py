import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Informe Técnico Pro", page_icon="🔧", layout="centered")

# --- CARGAR BASE DE DATOS (REGLA: SIEMPRE GENERAR CON PYTHON) ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        return pd.read_csv("servicios.csv", dtype={'Orden': str, 'Serie': str, 'Fac_Min': str})
    else:
        return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- GRÁFICO DE ESTADO (REGLA: ALWAYS GENERATE THIS GRAPH) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Órdenes Mes'], [85], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Progreso de Cumplimiento Mensual (%)")
    st.pyplot(fig)

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('Title', fontSize=18, alignment=1, spaceAfter=10, fontName='Helvetica-Bold', textColor=colors.hexColor("#003366"))
    estilo_seccion = ParagraphStyle('Section', fontSize=10, spaceBefore=8, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.hexColor("#003366"), borderPadding=3)
    estilo_campo = ParagraphStyle('Field', fontSize=9, fontName='Helvetica')

    story = []
    
    # Encabezado con logo si existe
    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=0.8*inch, height=0.8*inch)
        logo.hAlign = 'LEFT'
        story.append(logo)

    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", estilo_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", ParagraphStyle('T', alignment=1, textColor=colors.red, fontName='Helvetica-Bold')))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.hexColor("#003366"), spaceAfter=10))
    
    # Tabla de Datos (Incluyendo todos los campos editados)
    data = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", estilo_campo), Paragraph(f"<b>Factura:</b> {datos['factura']}", estilo_campo)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", estilo_campo), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", estilo_campo)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", estilo_campo), Paragraph(f"<b>Serie:</b> {datos['serie']}", estilo_campo)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", estilo_campo), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", estilo_campo)]
    ]
    t = Table(data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    # Contenido Técnico
    story.append(Paragraph("DETALLES DEL SERVICIO", estilo_seccion))
    story.append(Paragraph(f"<b>Falla Reportada:</b>", estilo_campo))
    story.append(Paragraph(datos['falla'], estilo_campo))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Trabajo Realizado:</b>", estilo_campo))
    story.append(Paragraph(datos['solucion'], estilo_campo))

    # Imágenes (REGLA: ALWAYS GENERATE THE IMAGE - si se cargan)
    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", estilo_seccion))
        for img in imagenes_cargadas:
            img.seek(0)
            p_img = PilImage.open(img)
            img_b = BytesIO()
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            p_img.save(img_b, format='JPEG')
            img_b.seek(0)
            story.append(Image(img_b, width=3*inch, height=2.2*inch))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- INTERFAZ DE USUARIO ---
st.title("🔧 Generador de Reportes (Auto-completado Editable)")
mostrar_grafico()

# Búsqueda inicial
with st.container():
    st.subheader("1. Ingrese el número de Orden")
    orden_id = st.text_input("Orden #", placeholder="Escriba aquí la orden y presione Enter...")
    
    # Variables de estado iniciales
    cliente_def, serie_def, prod_def, fac_def, fec_fac_def = "", "", "", "", date.today()
    
    if orden_id:
        res = df_db[df_db['Orden'] == orden_id]
        if not res.empty:
            row = res.iloc[0]
            cliente_def = row['Cliente']
            serie_def = row['Serie']
            prod_def = row['Producto']
            fac_def = row['Fac_Min']
            try:
                fec_fac_def = datetime.strptime(str(row['Fec_Fac_Min']), '%Y-%m-%d').date()
            except: pass
            st.info("✅ Datos encontrados. Puede editarlos en el formulario de abajo si es necesario.")
        else:
            st.warning("⚠️ Orden no encontrada. Por favor, ingrese los datos manualmente.")

st.markdown("---")

# Formulario Principal con datos editables
with st.form("main_form"):
    tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    
    col1, col2 = st.columns(2)
    with col1:
        # Los campos usan los valores encontrados como 'value', pero son 100% editables
        f_cliente = st.text_input("Cliente", value=cliente_def)
        f_prod = st.text_input("Producto", value=prod_def)
        f_serie = st.text_input("Serie/Artículo", value=serie_def)
    with col2:
        f_fac = st.text_input("Factura", value=fac_def)
        f_fec_fac = st.date_input("Fecha Factura", value=fec_fac_def)
        f_tecnico = st.selectbox("Técnico Responsable", options=LISTA_TECNICOS)
    
    st.subheader("2. Detalles del Trabajo")
    f_falla = st.text_area("Falla Reportada / Problema")
    f_solucion = st.text_area("Trabajo Realizado / Solución")
    
    st.subheader("3. Evidencia")
    imgs = st.file_uploader("Subir imágenes", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

    submit = st.form_submit_button("💾 GENERAR Y DESCARGAR PDF")

if submit:
    if not (f_cliente and f_falla and f_solucion):
        st.error("Error: Cliente, Falla y Solución son campos obligatorios.")
    else:
        with st.spinner("Procesando reporte..."):
            pdf_bytes = generar_pdf({
                "tipo_reporte": tipo, "orden": orden_id, "cliente": f_cliente,
                "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod,
                "serie": f_serie, "tecnico": f_tecnico, "falla": f_falla,
                "solucion": f_solucion, "fecha_hoy": date.today()
            }, imgs)
            st.success("Reporte generado con éxito.")
            st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name=f"Reporte_{orden_id}.pdf")

# --- TABLA DE TÉCNICOS (REGLA: ALWAYS SHOW THE TABLE) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
st.table(pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
}))
