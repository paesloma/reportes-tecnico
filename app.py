import streamlit as st
from datetime import date
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- Configuración de la página ---
st.set_page_config(page_title="🔧 Informe Técnico", layout="centered")

# --- LISTA DE TÉCNICOS CON PREFIJO 'Tec.' ---
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]

def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    
    styles = getSampleStyleSheet()
    
    # Estilos base
    estilo_normal = styles['Normal']
    estilo_normal.fontName = 'Helvetica'
    estilo_normal.fontSize = 10
    
    estilo_titulo = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=12, fontName='Helvetica-Bold')
    estilo_seccion = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, spaceAfter=6, fontName='Helvetica-Bold', backColor=colors.lightgrey, borderPadding=(0,0,0,0))
    estilo_campo_bold = ParagraphStyle('FieldBold', parent=estilo_normal, fontName='Helvetica-Bold', fontSize=10, spaceAfter=0)
    estilo_campo_valor = ParagraphStyle('FieldValue', parent=estilo_normal, fontSize=10, spaceAfter=6)
    estilo_firma_nombre = ParagraphStyle('FirmaNombre', parent=estilo_normal, alignment=1, fontSize=10, spaceAfter=0)

    story = []

    # --- 0. Logo ---
    LOGO_PATH = "logo.png"
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=1.0 * inch, height=1.0 * inch)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 0.1 * inch))
        except Exception:
            pass
    
    # --- Título ---
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", estilo_titulo))
    story.append(Spacer(1, 0.2 * inch))
    
    # --- 1. Información Cliente/Equipo ---
    story.append(Paragraph("1. Información del Cliente y Equipo", estilo_seccion))

    data_cliente = [
        [Paragraph("<b>Cliente:</b>", estilo_campo_bold), Paragraph(datos['cliente'], estilo_campo_valor), 
         Paragraph("<b>Fecha:</b>", estilo_campo_bold), Paragraph(str(datos['fecha']), estilo_campo_valor)],
        [Paragraph("<b>Dispositivo:</b>", estilo_campo_bold), Paragraph(datos['equipo'], estilo_campo_valor),
         Paragraph("<b>Técnico:</b>", estilo_campo_bold), Paragraph(datos['tecnico'], estilo_campo_valor)],
    ]
    
    tabla_cliente = Table(data_cliente, colWidths=[1.0 * inch, 2.5 * inch, 1.0 * inch, 2.5 * inch])
    tabla_cliente.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.white),
    ]))
    story.append(tabla_cliente)
    story.append(Spacer(1, 0.1 * inch))

    # --- 2. Diagnóstico ---
    story.append(Paragraph("2. Diagnóstico y Solución", estilo_seccion))
    story.append(Paragraph("<b>Falla Reportada:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['falla'], estilo_campo_valor))
    story.append(Paragraph("<b>Trabajo Realizado:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['solucion'], estilo_campo_valor))
    story.append(Spacer(1, 0.2 * inch))
                
    # --- 3. Evidencia ---
    if imagenes_cargadas:
        story.append(Paragraph("3. Evidencia Fotográfica", estilo_seccion))
        story.append(Spacer(1, 0.1 * inch))
        for i, archivo_img in enumerate(imagenes_cargadas):
            nombre_base = os.path.splitext(archivo_img.name)[0]
            story.append(Paragraph(f"<b>Imagen {i + 1} ({nombre_base}):</b>", estilo_campo_bold))
            try:
                archivo_img.seek(0)
                img_pillow = PilImage.open(archivo_img)
                img_buffer = BytesIO()
                if img_pillow.mode in ('RGBA', 'P'):
                    img_pillow = img_pillow.convert('RGB')
                img_pillow.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                img = Image(img_buffer, width=3.0 * inch, height=3.0 * inch) 
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))
            except:
                continue
                
    # --- 4. Firmas ---
    story.append(Spacer(1, 0.5 * inch))
    nombre_tecnico = datos['tecnico']
    
    data_firmas = [
        [Paragraph(nombre_tecnico, estilo_firma_nombre), Paragraph("", estilo_firma_nombre)],
        ["_______________________", "_______________________"],
        ["Revisado por", "Firma del Cliente"] # CAMBIO SOLICITADO AQUÍ
    ]
    tabla_firmas = Table(data_firmas, colWidths=[3.25 * inch, 3.25 * inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,0), 0),
        ('TOPPADDING', (0,1), (-1,1), 0),
    ]))
    story.append(tabla_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- Interfaz Streamlit ---
st.title("🔧 Informe Técnico")
st.markdown("---")

with st.form("formulario_reporte"):
    tab1, tab2 = st.tabs(["📋 Detalles Generales", "📸 Evidencia"])

    with tab1:
        st.subheader("Datos del Cliente y Equipo")
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.text_input("Nombre del Cliente")
            equipo = st.text_input("Equipo / Modelo")
        with col2:
            fecha = st.date_input("Fecha", value=date.today())
            tecnico = st.selectbox("Nombre del Técnico", options=LISTA_TECNICOS)

        st.subheader("Diagnóstico y Solución")
        falla = st.text_area("Falla Reportada")
        solucion = st.text_area("Trabajo Realizado")

    with tab2:
        st.subheader("Evidencia Fotográfica")
        imagenes_cargadas = st.file_uploader("Cargar Fotos", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
    
    submitted = st.form_submit_button("💾 Generar Informe PDF")

if submitted:
    if not (cliente and equipo and falla and solucion):
        st.error("Por favor, rellene todos los campos.")
    else:
        datos_formulario = {"cliente": cliente, "equipo": equipo, "fecha": fecha, "tecnico": tecnico, "falla": falla, "solucion": solucion}
        try:
            pdf_bytes = generar_pdf(datos_formulario, imagenes_cargadas)
            st.success("Informe generado correctamente.")
            st.download_button(label="⬇️ Descargar PDF", data=pdf_bytes, file_name=f"Informe_{cliente}.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Error: {e}")
