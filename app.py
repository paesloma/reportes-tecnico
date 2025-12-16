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
    
    # NUEVO ESTILO: para el nombre en la firma (centrado y sin espacio inferior)
    estilo_firma_nombre = ParagraphStyle('FirmaNombre', parent=estilo_normal, alignment=1, fontSize=10, spaceAfter=0)


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
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", estilo_titulo))
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
                
    # --- 3. Evidencia Fotográfica ---
    if imagenes_cargadas:
        story.append(Paragraph("3. Evidencia Fotográfica", estilo_seccion))
        story.append(Spacer(1, 0.1 * inch))
        
        # Iteramos sobre CADA imagen cargada
        for i, archivo_img in enumerate(imagenes_cargadas):
            nombre_base = os.path.splitext(archivo_img.name)[0]
            descripcion = f"Imagen {i + 1} ({nombre_base})"
            story.append(Paragraph(f"<b>{descripcion}:</b>", estilo_campo_bold))
            
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
                    
            except Exception as e:
                story.append(Paragraph(f"(Error al cargar imagen. Tipo de fallo: {type(e).__name__})", estilo_campo_valor))
                st.warning(f"Advertencia: No se pudo incluir la imagen '{descripcion}'. Fallo al procesar la imagen.")
                
    # --- 4. Firmas ---
    story.append(Spacer(1, 0.5 * inch))
    
    # Usamos una tabla para alinear las firmas
    nombre_tecnico = datos['tecnico']
    
    # CAMBIO CLAVE: Nueva fila para el nombre del técnico
    data_firmas = [
        # Fila 1: Nombre del técnico (se deja vacío el del cliente por ahora)
        [Paragraph(nombre_tecnico, estilo_firma_nombre), Paragraph("", estilo_firma_nombre)],
        # Fila 2: Líneas de firma
        ["_______________________", "_______________________"],
        # Fila 3: Etiquetas
        ["Firma del Técnico", "Firma del Cliente"]
    ]
    tabla_firmas = Table(data_firmas, colWidths=[3.25 * inch, 3.25 * inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        # Ajustes de padding para que el nombre quede justo encima de la línea
        ('BOTTOMPADDING', (0,0), (-1,0), 0),
        ('TOPPADDING', (0,1), (-1,1), 0),
    ]))
    story.append(tabla_firmas)
    
    # Construir el documento
    doc.build(story)
    
    # Obtener los bytes del buffer para Streamlit
    buffer.seek(0)
    return buffer.read()

# --- Interfaz del Formulario (Streamlit) ---
st.title("🔧 Informe Técnico")
st.markdown("Genera un informe detallado del servicio realizado, incluyendo evidencias fotográficas.")
st.markdown("---")

# Estilo mejorado: usar pestañas y columnas para una mejor organización

with st.form("formulario_reporte"):
    tab1, tab2 = st.tabs(["📋 Detalles Generales", "📸 Evidencia"])

    with tab1:
        st.subheader("Datos del Cliente y Equipo 👤")
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Nombre del Cliente", key="cliente", help="Nombre completo de la persona o empresa.")
            equipo = st.text_input("Equipo / Modelo", key="equipo", help="Modelo o descripción del dispositivo.")
        
        with col2:
            fecha = st.date_input("Fecha del Servicio", key="fecha", value=date.today(), help="Día en que se realizó el servicio.")
            tecnico = st.text_input("Nombre del Técnico", key="tecnico", help="Persona que realiza el diagnóstico y reparación.")

        st.subheader("Diagnóstico y Solución ✅")
        falla = st.text_area("Falla Reportada / Problema", key="falla", height=100, help="Descripción detallada del problema inicial.")
        solucion = st.text_area("Trabajo Realizado / Solución Aplicada", key="solucion", height=150, help="Pasos de diagnóstico, reparación y configuración final.")

    with tab2:
        st.subheader("Evidencia Fotográfica 🖼️")
        st.info("Sube todas las fotos relevantes. Se incluirán en orden en el informe.")
        
        # Carga de múltiples archivos
        imagenes_cargadas = st.file_uploader(
            "Cargar Fotos (JPEG, PNG)", 
            type=['jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key="imgs_multiples"
        )
    
    st.markdown("---")
    submitted = st.form_submit_button("💾 Generar Informe PDF")

# --- Generación y Descarga ---
if submitted:
    if not cliente or not equipo or not tecnico or not falla or not solucion:
        st.error("❌ ¡Error! Por favor, complete todos los campos obligatorios: Cliente, Equipo, Técnico, Falla y Solución.")
    else:
        datos_formulario = {
            "cliente": cliente,
            "equipo": equipo,
            "fecha": fecha,
            "tecnico": tecnico,
            "falla": falla,
            "solucion": solucion,
        }
        
        # Pasamos la lista de archivos al generador
        with st.spinner('⚙️ Generando Informe PDF...'):
            try:
                pdf_bytes = generar_pdf(datos_formulario, imagenes_cargadas)
                st.success(f"✅ ¡Informe generado con éxito! Se procesaron {len(imagenes_cargadas) if imagenes_cargadas else 0} imágenes.")
                
                nombre_archivo = f"Informe_Tecnico_{cliente.replace(' ', '_')}_{date.today()}.pdf"
                st.download_button(
                    label="⬇️ Descargar PDF Final",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"💥 Error CRÍTICO final al generar el PDF. Detalle: {type(e).__name__}. Verifique sus datos e imágenes.")
