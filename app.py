import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab para el PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

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

# --- 3. MARCA DE AGUA ---
def agregar_marca_agua(canvas, doc):
    watermark_file = "watermark.png"
    if os.path.exists(watermark_file):
        canvas.saveState()
        canvas.setFillAlpha(0.15)
        page_width, page_height = canvas._pagesize
        canvas.drawImage(watermark_file, 0, 0, width=page_width, height=page_height, 
                         mask='auto', preserveAspectRatio=True, anchor='c')
        canvas.restoreState()

# --- 4. FUNCIÓN GENERAR PDF (MODIFICADA PARA FOTOS CON DESCRIPCIÓN) ---
def generar_pdf(datos, lista_fotos_procesadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    try: color_principal = colors.HexColor("#003366")
    except AttributeError: color_principal = colors.hexColor("#003366")

    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_principal, spaceAfter=20)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_principal, borderPadding=3, spaceBefore=10)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_desc_foto = ParagraphStyle('DF', fontSize=9, fontName='Helvetica-Oblique', leading=11)

    story = []
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    # Tabla de Datos
    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)
    story.append(Spacer(1, 15))

    # Secciones de Texto
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Ingresa a servicio técnico", datos['ingreso_tec']),
        ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']),
        ("4. Observaciones", datos['observaciones']),
        ("5. Conclusiones", datos['conclusiones'])
    ]

    for titulo, contenido in secciones:
        story.append(Paragraph(titulo, est_sec))
        story.append(Paragraph(contenido.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 5))

    # --- NUEVA LÓGICA DE FOTOS EN EL PDF ---
    if lista_fotos_procesadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        story.append(Spacer(1, 10))
        
        # Creamos una tabla para las fotos: Columna 1 = Imagen, Columna 2 = Descripción
        tabla_fotos_data = []
        
        for idx, item in enumerate(lista_fotos_procesadas):
            # Procesar imagen
            img_byte_arr = item['imagen']
            descripcion_texto = item['descripcion']
            
            # Crear objeto Image de ReportLab
            img_obj = Image(img_byte_arr, width=2.5*inch, height=1.8*inch) # Tamaño ajustado
            
            # Crear párrafo de descripción con número
            p_desc = Paragraph(f"<b>Foto #{idx + 1}:</b><br/>{descripcion_texto}", est_desc_foto)
            
            # Añadir fila a la tabla
            tabla_fotos_data.append([img_obj, p_desc])
        
        # Crear la tabla de fotos
        t_fotos = Table(tabla_fotos_data, colWidths=[2.7*inch, 4.5*inch])
        t_fotos.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), # Centrar verticalmente
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15), # Espacio entre filas
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey) # Borde sutil opcional
        ]))
        
        story.append(t_fotos)

    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

# Búsqueda de Orden
st.subheader("1. Localizar Orden")
orden_id = st.text_input("Ingrese número de Orden")

# Variables por defecto
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

# Lógica de carga automática (fuera del form para reactividad)
if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: pass
        st.success("✅ Datos cargados.")

st.markdown("---")

# --- FORMULARIO DE DATOS (Sin st.form para permitir dinámica en fotos) ---
col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)
with col2:
    f_tecnico = st.selectbox("Técnico Asignado", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura", value=ff_v)

st.subheader("Detalles Técnicos")
f_rev_fisica = st.text_area("1. Revisión Física", height=100)
f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico", height=100)

t_electro = "Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo."
f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value=t_electro, height=100)

f_obs = st.text_area("4. Observaciones", value="Luego de la revisión del artículo se observa lo siguiente: ", height=100)

concl_map = {
    "FUERA DE GARANTIA": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales",
    "RECLAMO AL PROVEEDOR": "Se concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}
f_conclusiones = st.text_area("5. Conclusiones", value=concl_map[tipo_rep], height=100)

st.markdown("---")
st.subheader("📸 Evidencia Fotográfica y Descripciones")

# Uploader de fotos
uploaded_files = st.file_uploader("Subir fotos (Seleccione varias)", type=['jpg','png','jpeg'], accept_multiple_files=True)

lista_fotos_final = []

if uploaded_files:
    st.info(f"Has subido {len(uploaded_files)} fotos. Por favor añade una descripción a cada una.")
    
    # Iteramos sobre los archivos subidos para mostrar inputs dinámicos
    for i, file in enumerate(uploaded_files):
        c_img, c_txt = st.columns([1, 2])
        
        with c_img:
            # Mostrar miniatura
            st.image(file, width=150, caption=f"Foto #{i+1}")
            
        with c_txt:
            # Input de texto para la descripción
            desc = st.text_area(f"Descripción para la Foto #{i+1}", key=f"desc_{file.name}_{i}", height=100)
            
        # Preparamos los datos para el PDF (guardamos el archivo en memoria y la descripción)
        file.seek(0)
        p_img = PilImage.open(file)
        if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
        
        img_byte = BytesIO()
        p_img.save(img_byte, format='JPEG', quality=80)
        img_byte.seek(0)
        
        lista_fotos_final.append({
            "imagen": img_byte,
            "descripcion": desc if desc else "Sin descripción."
        })
    
    st.markdown("---")

# Botón de Generación
if st.button("💾 GENERAR REPORTE PDF", type="primary"):
    if f_cliente and f_conclusiones:
        # Verificar watermark
        if not os.path.exists("watermark.png"):
             st.warning("⚠️ No se detectó 'watermark.png'. El PDF se generará sin fondo.")

        pdf_data = generar_pdf({
            "tipo_reporte": tipo_rep, "orden": orden_id, "cliente": f_cliente,
            "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod,
            "serie": f_serie, "tecnico": f_tecnico, "fecha_hoy": date.today(),
            "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
            "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_conclusiones
        }, lista_fotos_final)
        
        st.success("✅ ¡Informe generado exitosamente!")
        st.download_button("📥 DESCARGAR PDF", data=pdf_data, file_name=f"Informe_{orden_id}.pdf")
    else:
        st.error("⚠️ Por favor, asegúrese de que los campos 'Cliente' y 'Conclusiones' no estén vacíos.")
