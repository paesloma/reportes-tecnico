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

# --- 2. CARGA DE DATOS ---
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
            except:
                continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. MARCA DE AGUA ---
def agregar_marca_agua(canvas, doc):
    watermark_file = "watermark.png"
    if os.path.exists(watermark_file):
        canvas.saveState()
        canvas.setFillAlpha(0.12)
        page_width, page_height = canvas._pagesize
        canvas.drawImage(watermark_file, 0, 0, width=page_width, height=page_height, 
                         mask='auto', preserveAspectRatio=True, anchor='c')
        canvas.restoreState()

# --- 4. FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, lista_imagenes_procesadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    color_azul_institucional = colors.HexColor("#0056b3")

    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul_institucional)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, 
                            backColor=color_azul_institucional, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)

    story = []

    if os.path.exists("logo.png"):
        img_logo = Image("logo.png", width=1.4*inch, height=0.55*inch)
        img_logo.hAlign = 'LEFT'
        story.append(img_logo)
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    factura_texto = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']

    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {factura_texto}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

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

    if lista_imagenes_procesadas:
        story.append(Paragraph("EVIDENCIA DE IMÁGENES", est_sec))
        story.append(Spacer(1, 10))
        tabla_imgs = []
        for idx, item in enumerate(lista_imagenes_procesadas):
            img_obj = Image(item['imagen'], width=2.4*inch, height=1.7*inch)
            p_desc = Paragraph(f"<b>Imagen #{idx + 1}:</b><br/>{item['descripcion']}", est_txt)
            tabla_imgs.append([img_obj, p_desc])
        t_fotos = Table(tabla_imgs, colWidths=[2.6*inch, 4.6*inch])
        t_fotos.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('BOTTOMPADDING', (0,0), (-1,-1), 12)]))
        story.append(t_fotos)

    story.append(Spacer(1, 60))
    firmas_data = [
        [Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)],
        [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]
    ]
    t_firmas = Table(firmas_data, colWidths=[3.7*inch, 3.7*inch])
    t_firmas.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_firmas)

    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

# --- 5. FUNCIÓN GENERAR TXT ---
def generar_txt(datos):
    factura_texto = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    contenido = f"""Estimados

Me dirijo a para indicar el status de estado de la garantia del siguiente producto

CLIENTE: {datos['cliente']}
FACTURA: {factura_texto}
FECHA: {datos['fecha_factura']}
ORDEN: {datos['orden']}
CODIGO: {datos['serie']}
DESCRIPCION: {datos['producto']}

OBSERVACION: {datos['tipo_reporte']}

DETALLES:
{datos['observaciones']}

Agradecido a la atención de la presente
Atentamente 
Ing. Pablo Lopez
Coordinador Postventa Hamilton Beach
0995115782"""
    return contenido

# --- 6. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: pass
        st.success("✅ Datos cargados.")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

st.subheader("Detalles Técnicos")
texto_rev_fisica = f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo."
f_rev_fisica = st.text_area("1. Revisión Física", value=texto_rev_fisica)
f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo.")
f_obs = st.text_area("4. Observaciones", value="Luego de la revisión del artículo se observa lo siguiente: ")

concl_map = {
    "FUERA DE GARANTIA": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales",
    "RECLAMO AL PROVEEDOR": "Se concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}
f_conclusiones = st.text_area("5. Conclusiones", value=concl_map[tipo_rep])

st.markdown("---")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
lista_imgs_final = []
if uploaded_files:
    for i, file in enumerate(uploaded_files):
        c_img, c_txt = st.columns([1, 2])
        with c_img: st.image(file, width=150)
        with c_txt: desc = st.text_area(f"Descripción Imagen #{i+1}", key=f"img_{i}")
        file.seek(0)
        p_img = PilImage.open(file)
        if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
        img_byte = BytesIO()
        p_img.save(img_byte, format='JPEG', quality=80)
        img_byte.seek(0)
        lista_imgs_final.append({"imagen": img_byte, "descripcion": desc if desc else "Sin descripción."})

# --- LÓGICA DE BOTONES ---
if st.button("💾 GENERAR REPORTE", type="primary", use_container_width=True):
    if f_cliente:
        datos_comunes = {
            "orden": orden_id, "cliente": f_cliente, "factura": f_fac, 
            "fecha_factura": f_fec_fac, "producto": f_prod, "serie": f_serie, 
            "tecnico": f_tecnico, "realizador": f_realizador, "fecha_hoy": date.today(), 
            "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec, "rev_electro": f_rev_electro, 
            "observaciones": f_obs, "conclusiones": f_conclusiones, "tipo_reporte": tipo_rep
        }
        
        # Generamos ambos archivos
        pdf_data = generar_pdf(datos_comunes, lista_imgs_final)
        txt_data = generar_txt(datos_comunes)
        
        st.success("✅ Archivos listos para descargar")
        
        # Mostramos los dos botones de descarga
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button("📥 DESCARGAR PDF", data=pdf_data, file_name=f"Informe_{orden_id}.pdf", use_container_width=True)
        with col_d2:
            st.download_button("📥 DESCARGAR TXT", data=txt_data, file_name=f"Status_{orden_id}.txt", use_container_width=True)
            
        # Opcional: Mostrar el texto para copiar rápido
        st.text_area("Copia el texto aquí:", value=txt_data, height=200)
    else:
        st.error("⚠️ Complete los datos del cliente.")
