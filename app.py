import streamlit as st
import pandas as pd
from datetime import date
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
st.set_page_config(page_title="Sistema de Informes Técnicos", page_icon="🔧", layout="centered")

# --- CARGAR BASE DE DATOS ---
@st.cache_data
def cargar_base_datos():
    if os.path.exists("productos.csv"):
        return pd.read_csv("productos.csv", dtype={'Codigo': str})
    else:
        # DB de ejemplo si no existe el archivo
        return pd.DataFrame({
            'Codigo': ['101', '102'],
            'Descripcion': ['Producto de Prueba A', 'Producto de Prueba B']
        })

df_productos = cargar_base_datos()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.4 * inch, bottomMargin=0.4 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    
    styles = getSampleStyleSheet()
    
    # Estilos Personalizados
    estilo_titulo = ParagraphStyle('Title', fontSize=16, alignment=1, spaceAfter=10, fontName='Helvetica-Bold', textColor=colors.hexColor("#003366"))
    estilo_tipo_rep = ParagraphStyle('TipoRep', fontSize=12, alignment=1, spaceAfter=10, fontName='Helvetica-Bold', textColor=colors.red)
    estilo_seccion = ParagraphStyle('Section', fontSize=10, spaceBefore=8, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.hexColor("#003366"), borderPadding=3)
    estilo_campo_bold = ParagraphStyle('FieldBold', fontName='Helvetica-Bold', fontSize=9, textColor=colors.black)
    estilo_campo_valor = ParagraphStyle('FieldValue', fontSize=9, spaceAfter=4)
    estilo_firma = ParagraphStyle('Firma', alignment=1, fontSize=9, fontName='Helvetica-Bold')

    story = []

    # 0. Logo y Encabezado
    if os.path.exists("logo.png"):
        try:
            img_logo = Image("logo.png", width=0.8 * inch, height=0.8 * inch)
            img_logo.hAlign = 'LEFT'
            story.append(img_logo)
        except: pass

    story.append(Paragraph("REPORTE DE SERVICIO TÉCNICO", estilo_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", estilo_tipo_rep))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.hexColor("#003366"), spaceAfter=10))
    
    # 1. Datos del Cliente (Nueva Estructura)
    story.append(Paragraph("DATOS DEL CLIENTE Y DOCUMENTACIÓN", estilo_seccion))
    
    data_cliente = [
        [Paragraph("<b>Orden:</b>", estilo_campo_bold), Paragraph(datos['orden'], estilo_campo_valor), 
         Paragraph("<b>Factura:</b>", estilo_campo_bold), Paragraph(datos['factura'], estilo_campo_valor)],
        [Paragraph("<b>Cliente:</b>", estilo_campo_bold), Paragraph(datos['cliente'], estilo_campo_valor),
         Paragraph("<b>Fecha Factura:</b>", estilo_campo_bold), Paragraph(str(datos['fecha_factura']), estilo_campo_valor)],
        [Paragraph("<b>Fecha Reporte:</b>", estilo_campo_bold), Paragraph(str(datos['fecha']), estilo_campo_valor),
         Paragraph("<b>Serie:</b>", estilo_campo_bold), Paragraph(datos['serie'], estilo_campo_valor)],
        [Paragraph("<b>Código Prod:</b>", estilo_campo_bold), Paragraph(datos['codigo_prod'], estilo_campo_valor),
         Paragraph("<b>Descripción:</b>", estilo_campo_bold), Paragraph(datos['equipo'], estilo_campo_valor)],
        [Paragraph("<b>Técnico:</b>", estilo_campo_bold), Paragraph(datos['tecnico'], estilo_campo_valor), "", ""]
    ]
    
    t_cliente = Table(data_cliente, colWidths=[1.1 * inch, 2.4 * inch, 1.1 * inch, 2.4 * inch])
    t_cliente.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_cliente)

    # 2. Diagnóstico y Solución
    story.append(Paragraph("DETALLES TÉCNICOS (FALLA Y SOLUCIÓN)", estilo_seccion))
    story.append(Paragraph("<b>Falla Reportada:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['falla'], estilo_campo_valor))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>Trabajo Realizado:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['solucion'], estilo_campo_valor))

    # 3. Evidencia Fotográfica
    if imagenes_cargadas:
        story.append(Spacer(1, 10))
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", estilo_seccion))
        for img_file in imagenes_cargadas:
            try:
                img_file.seek(0)
                p_img = PilImage.open(img_file)
                img_b = BytesIO()
                if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
                p_img.save(img_b, format='JPEG', quality=75)
                img_b.seek(0)
                # Ajuste de tamaño para que quepan más por página
                img_draw = Image(img_b, width=3.2 * inch, height=2.2 * inch)
                img_draw.hAlign = 'CENTER'
                story.append(img_draw)
                story.append(Spacer(1, 8))
            except: continue

    # 4. Firmas
    story.append(Spacer(1, 40))
    data_firmas = [
        [Paragraph(datos['tecnico'], estilo_firma), Paragraph("", estilo_firma)],
        ["___________________________", "___________________________"],
        [Paragraph("Revisado por", estilo_firma), Paragraph("Firma del Cliente", estilo_firma)]
    ]
    tf = Table(data_firmas, colWidths=[3.25 * inch, 3.25 * inch])
    story.append(tf)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- INTERFAZ STREAMLIT ---
st.title("🔧 Generador de Informes Técnicos")

# --- BÚSQUEDA DE PRODUCTO (FUERA DEL FORMULARIO) ---
with st.container():
    st.subheader("🔍 Identificación de Producto")
    c_cod, c_desc = st.columns([1, 2])
    with c_cod:
        codigo_ingresado = st.text_input("Código del Producto", help="Digite el código y presione Enter")
    
    descripcion_auto = ""
    if codigo_ingresado:
        resultado = df_productos[df_productos['Codigo'] == codigo_ingresado]
        if not resultado.empty:
            descripcion_auto = resultado.iloc[0]['Descripcion']
            st.success("Producto localizado.")
        else:
            st.error("Código no encontrado.")
            descripcion_auto = "No registrado en base de datos"

    with c_desc:
        st.text_input("Descripción Automática", value=descripcion_auto, disabled=True)

st.markdown("---")

# --- FORMULARIO PRINCIPAL ---
with st.form("form_reporte"):
    # Selector de Tipo de Reporte (Destacado)
    tipo_reporte = st.selectbox("📋 TIPO DE REPORTE", options=OPCIONES_REPORTE)
    
    tab_cliente, tab_servicio, tab_fotos = st.tabs(["👥 Datos del Cliente", "🛠️ Servicio", "📸 Evidencia"])
    
    with tab_cliente:
        col1, col2 = st.columns(2)
        with col1:
            orden = st.text_input("N° de Orden")
            cliente = st.text_input("Nombre del Cliente / Empresa")
            serie = st.text_input("Número de Serie (S/N)")
        with col2:
            factura = st.text_input("N° de Factura")
            f_factura = st.date_input("Fecha de Factura", value=date.today())
            f_hoy = st.date_input("Fecha del Reporte", value=date.today())
            
        tecnico = st.selectbox("Técnico Responsable", options=LISTA_TECNICOS)

    with tab_servicio:
        falla = st.text_area("Falla Reportada", placeholder="Describa el problema detectado...")
        solucion = st.text_area("Trabajo Realizado", placeholder="Describa las acciones tomadas...")

    with tab_fotos:
        imgs = st.file_uploader("Cargar fotos de evidencia", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

    st.markdown("<br>", unsafe_allow_html=True)
    btn_submit = st.form_submit_button("🚀 GENERAR REPORTE PDF")

if btn_submit:
    if not (cliente and orden and codigo_ingresado and falla and solucion):
        st.warning("⚠️ Por favor complete los campos obligatorios (Orden, Cliente, Código, Falla y Solución).")
    else:
        with st.spinner("Generando documento..."):
            try:
                dict_datos = {
                    "tipo_reporte": tipo_reporte,
                    "orden": orden,
                    "cliente": cliente,
                    "factura": factura,
                    "fecha_factura": f_factura,
                    "fecha": f_hoy,
                    "serie": serie,
                    "codigo_prod": codigo_ingresado,
                    "equipo": descripcion_auto,
                    "tecnico": tecnico,
                    "falla": falla,
                    "solucion": solucion
                }
                pdf_output = generar_pdf(dict_datos, imgs)
                st.balloons()
                st.download_button(
                    label="📥 Descargar Informe PDF",
                    data=pdf_output,
                    file_name=f"Reporte_{orden}_{cliente}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error al generar el PDF: {e}")
