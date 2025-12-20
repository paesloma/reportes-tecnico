import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab para la creación del PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestión Técnica", page_icon="🔧", layout="centered")

# --- 2. FUNCIÓN CARGAR DATOS (BLINDADA CONTRA ERRORES DE FORMATO) ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        # Probamos diferentes codificaciones para evitar el UnicodeDecodeError
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                # sep=None con engine='python' detecta automáticamente si es coma o punto y coma
                df = pd.read_csv("servicios.csv", 
                                 dtype={'Orden': str, 'Serie': str, 'Fac_Min': str}, 
                                 encoding=encoding, 
                                 sep=None, 
                                 engine='python')
                return df
            except:
                continue
        st.error("❌ No se pudo leer el archivo 'servicios.csv'. Asegúrate de guardarlo como CSV UTF-8.")
        return pd.DataFrame()
    else:
        st.warning("⚠️ Archivo 'servicios.csv' no encontrado. Los datos deberán ingresarse manualmente.")
        return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. GRÁFICO DE ESTADO (REGLA: SIEMPRE GENERAR) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Eficiencia del Equipo'], [92], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Nivel de Resolución Mensual (%)")
    st.pyplot(fig)

# --- 4. FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    est_titulo = ParagraphStyle('T', fontSize=18, alignment=1, fontName='Helvetica-Bold', textColor=colors.hexColor("#003366"))
    est_tipo = ParagraphStyle('TR', fontSize=12, alignment=1, fontName='Helvetica-Bold', textColor=colors.red, spaceAfter=12)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.hexColor("#003366"), borderPadding=3)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica')

    story = []
    
    # Encabezado
    story.append(Paragraph("REPORTE TÉCNICO DE SERVICIO", est_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", est_tipo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.hexColor("#003366"), spaceAfter=10))
    
    # Tabla de Información
    data_info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(data_info, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t)

    # Contenido del Servicio
    story.append(Paragraph("DETALLES DEL TRABAJO", est_sec))
    story.append(Paragraph(f"<b>Falla:</b> {datos['falla']}", est_txt))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Solución:</b> {datos['solucion']}", est_txt))

    # Imágenes de Evidencia
    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for img_file in imagenes_cargadas:
            img_file.seek(0)
            p_img = PilImage.open(img_file)
            img_b = BytesIO()
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            p_img.save(img_b, format='JPEG', quality=75)
            img_b.seek(0)
            story.append(Image(img_b, width=3.2*inch, height=2.4*inch))
            story.append(Spacer(1, 10))

    # Firmas
    story.append(Spacer(1, 40))
    f_data = [["___________________________", "___________________________"], ["Responsable Técnico", "Firma del Cliente"]]
    tf = Table(f_data, colWidths=[3.5*inch, 3.5*inch])
    tf.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(tf)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ STREAMLIT ---
st.title("🔧 Generador de Reportes Profesionales")
mostrar_grafico()

# 5.1 Búsqueda por Orden
with st.container():
    st.subheader("1. Localizar Orden")
    orden_busqueda = st.text_input("Ingrese el número de Orden y presione Enter")
    
    # Variables de autocompletado
    c_val, s_val, p_val, f_val, ff_val = "", "", "", "", date.today()
    
    if orden_busqueda and not df_db.empty:
        res = df_db[df_db['Orden'] == orden_busqueda]
        if not res.empty:
            row = res.iloc[0]
            c_val, s_val, p_val, f_val = row['Cliente'], row['Serie'], row['Producto'], row['Fac_Min']
            try:
                ff_val = datetime.strptime(str(row['Fec_Fac_Min']), '%Y-%m-%d').date()
            except: pass
            st.success(f"✅ Datos de {c_val} cargados.")
        else:
            st.warning("Orden no encontrada. Ingrese los datos manualmente.")

st.markdown("---")

# 5.2 Formulario Editable
with st.form("form_final"):
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    
    col1, col2 = st.columns(2)
    with col1:
        f_cliente = st.text_input("Cliente", value=c_val)
        f_producto = st.text_input("Producto", value=p_val)
        f_serie = st.text_input("Serie/Artículo", value=s_val)
    with col2:
        f_factura = st.text_input("N° Factura", value=f_val)
        f_fecha_fac = st.date_input("Fecha de Factura", value=ff_val)
        f_tecnico = st.selectbox("Técnico Asignado", options=LISTA_TECNICOS)
    
    f_falla = st.text_area("Descripción de la Falla")
    f_solucion = st.text_area("Acciones Realizadas")
    f_fotos = st.file_uploader("Evidencia Fotográfica", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    btn_generar = st.form_submit_button("🚀 GENERAR REPORTE PDF")

if btn_generar:
    if not (f_cliente and f_falla and f_solucion):
        st.error("⚠️ Por favor complete los campos obligatorios.")
    else:
        pdf_bytes = generar_pdf({
            "tipo_reporte": tipo_rep, "orden": orden_busqueda, "cliente": f_cliente,
            "factura": f_factura, "fecha_factura": f_fecha_fac, "producto": f_producto,
            "serie": f_serie, "tecnico": f_tecnico, "falla": f_falla,
            "solucion": f_solucion, "fecha_hoy": date.today()
        }, f_fotos)
        st.download_button("📥 Descargar Reporte PDF", data=pdf_bytes, file_name=f"Reporte_{orden_busqueda}.pdf")

# --- 6. TABLA TÉCNICA (REGLA: SIEMPRE MOSTRAR) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
tabla_tecnicos = pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
})
st.table(tabla_tecnicos)
