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
st.set_page_config(page_title="🛠️ Generador de Reportes Técnicos", layout="centered")

def generar_pdf(datos, imagenes_cargadas):
    # Usaremos BytesIO para escribir el PDF directamente en la memoria
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.5 * inch, rightMargin=0.5 * inch)
    
    styles = getSampleStyleSheet()
    
    # Estilo base
    estilo_normal = styles['Normal']
    estilo_normal.fontName = 'Helvetica'
    estilo_normal.fontSize = 10
    
    # Estilos personalizados para el reporte
    estilo_titulo = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=1, spaceAfter=12, fontName='Helvetica-Bold')
    estilo_seccion = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, spaceAfter=6, fontName='Helvetica-Bold', backColor=colors.lightgrey, borderPadding=(0,0,0,0))
    estilo_campo_bold = ParagraphStyle('FieldBold', parent=estilo_normal, fontName='Helvetica-Bold', fontSize=10, spaceAfter=0)
    estilo_campo_valor = ParagraphStyle('FieldValue', parent=estilo_normal, fontSize=10, spaceAfter=6)
    estilo_costo = ParagraphStyle('Cost', parent=styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=12, alignment=0, fontName='Helvetica-Bold')
    
    story = []

    # --- 0. Logo de la Empresa ---
    LOGO_PATH = "logo.png"
    if os.path.exists(LOGO_PATH):
        try:
            # Insertamos el logo en la esquina superior izquierda
            logo = Image(LOGO_PATH, width=1.0 * inch, height=1.0 * inch) # Ajusta el tamaño según necesites
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 0.1 * inch))
        except Exception as e:
            st.warning(f"No se pudo cargar el logo 'logo.png'. Error: {type(e).__name__}")
    
    # --- Cabecera y Título ---
    story.append(Paragraph("REPORTE DE SERVICIO TÉCNICO", estilo_titulo))
    story.append(Spacer(1, 0.2 * inch))
    
    # --- 1. Información del Cliente y Equipo ---
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
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
    ]))
    story.append(tabla_cliente)
    story.append(Spacer(1, 0.1 * inch))

    # --- 2. Diagnóstico y Solución ---
    story.append(Paragraph("2. Diagnóstico y Solución", estilo_seccion))
    
    story.append(Paragraph("<b>Falla Reportada:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['falla'], estilo_campo_valor))
    story.append(Spacer(1, 0.1 * inch))
    
    story.append(Paragraph("<b>Trabajo Realizado:</b>", estilo_campo_bold))
    story.append(Paragraph(datos['solucion'], estilo_campo_valor))
    story.append(Spacer(1, 0.2 * inch))

    # --- 3. Costo Total ---
    story.append(Paragraph(f"<b>COSTO TOTAL DEL SERVICIO: ${datos['costo']:.2f}</b>", estilo_costo))

    # --- 4. Evidencia Fotográfica ---
    if imagenes_cargadas:
        story.append(Paragraph("4. Evidencia Fotográfica", estilo_seccion))
        story.append(Spacer(1, 0.1 * inch))
        
        # Iteramos sobre CADA imagen cargada
        for i, archivo_img in enumerate(imagenes_cargadas):
            descripcion = f"Imagen {i + 1} ({archivo_img.name})"
            story.append(Paragraph(f"<b>{descripcion}:</b>", estilo_campo_bold))
            
            try:
                archivo_img.seek(0)
                
                # CARGA CRÍTICA: Usamos Pillow para convertir la imagen a un buffer de bytes estable (JPEG)
                img_pillow = PilImage.open(archivo_img)
                
                img_buffer = BytesIO()
                
                # Forzamos JPEG (máxima compatibilidad)
                if img_pillow.mode in ('RGBA', 'P'):
                    img_pillow = img_pillow.convert('RGB')
                        
                img_pillow.save(img_buffer, format='JPEG')
                img_buffer.seek(0)
                
                # ReportLab lee el buffer de bytes
                img = Image(img_buffer, width=3.0 * inch, height=3.0 * inch) 
                story.append(img)
                story.append(Spacer(1, 0.2 * inch))
                    
            except Exception as e:
                story.append(Paragraph(f"(Error al cargar imagen. Tipo de fallo: {type(e).__name__})", estilo_campo_valor))
                st.warning(f"Advertencia: No se pudo incluir la imagen '{descripcion}'. Fallo al procesar la imagen.")
                
    # --- 5. Firmas ---
    story.append(Spacer(1, 0.5 * inch))
    
    # Usamos una tabla para alinear las firmas
    data_firmas = [
        ["_______________________", "_______________________"],
        ["Firma del Técnico", "Firma del Cliente"]
    ]
    tabla_firmas = Table(data_firmas, colWidths=[3.25 * inch, 3.25 * inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('GRID', (0,0), (-1,-1), 0.25, colors.white),
    ]))
    story.append(tabla_firmas)
    
    # Construir el documento
    doc.build(story)
    
    # Obtener los bytes del buffer para Streamlit
    buffer.seek(0)
    return buffer.read()

# --- Interfaz del Formulario (Streamlit) ---
st.title("🛠️ Generador de Reporte Técnico")
st.markdown("---")

with st.form("formulario_reporte"):
    st.subheader("Datos Generales")
    col1, col2 = st.columns(2)
    
    with col1:
        cliente = st.text_input("Nombre del Cliente", key="cliente")
        equipo = st.text_input("Equipo / Modelo", key="equipo")
    
    with col2:
        fecha = st.date_input("Fecha del Servicio", key="fecha", value=date.today())
        tecnico = st.text_input("Nombre del Técnico", key="tecnico")

    st.subheader("Detalles del Servicio")
    falla = st.text_area("Falla Reportada / Problema", key="falla")
    solucion = st.text_area("Diagnóstico y Solución Aplicada", key="solucion")
    costo = st.number_input("Costo Total ($)", min_value=0.0, key="costo")
    
    st.markdown("### 📸 Evidencia Fotográfica (Carga Múltiple)")
    
    # Carga de múltiples archivos
    imagenes_cargadas = st.file_uploader(
        "Cargar Fotos (JPEG, PNG)", 
        type=['jpg', 'png', 'jpeg'],
        accept_multiple_files=True,
        key="imgs_multiples"
    )

    submitted = st.form_submit_button("✅ Generar Reporte PDF")

# --- Generación y Descarga ---
if submitted:
    if not cliente or not equipo or not tecnico or not falla or not solucion:
        st.error("Por favor, complete los campos obligatorios: Cliente, Equipo, Técnico, Falla y Solución.")
    else:
        datos_formulario = {
            "cliente": cliente,
            "equipo": equipo,
            "fecha": fecha,
            "tecnico": tecnico,
            "falla": falla,
            "solucion": solucion,
            "costo": costo
        }
        
        # Pasamos la lista de archivos al generador
        with st.spinner('Generando PDF con Logo...'):
            try:
                pdf_bytes = generar_pdf(datos_formulario, imagenes_cargadas)
                st.success(f"¡Reporte generado con éxito! Se procesaron {len(imagenes_cargadas) if imagenes_cargadas else 0} imágenes.")
                
                nombre_archivo = f"Reporte_{cliente.replace(' ', '_')}_{date.today()}.pdf"
                st.download_button(
                    label="📥 Descargar PDF Final",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error CRÍTICO final al generar el PDF. Detalle: {type(e).__name__}. Asegúrese de que 'logo.png' exista en la raíz.")
