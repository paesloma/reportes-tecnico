import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

# Inicializar contenedores en la sesión para que no se borren
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None
if 'nombre_orden' not in st.session_state:
    st.session_state.nombre_orden = "reporte"

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
            except: continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. FUNCIONES DE GENERACIÓN ---
def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    color_azul = colors.HexColor("#0056b3") #
    
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []
    if os.path.exists("logo.png"):
        img = Image("logo.png", width=1.4*inch, height=0.55*inch)
        img.hAlign = 'LEFT'
        story.append(img)
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)))
    story.append(Spacer(1, 15))
    
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura'] #
    
    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {fac_txt}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

    for tit, cont in [("1. Revisión Física", datos['rev_fisica']), ("2. Ingresa a servicio técnico", datos['ingreso_tec']), 
                       ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']), ("4. Observaciones", datos['observaciones']), 
                       ("5. Conclusiones", datos['conclusiones'])]:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 5))

    if lista_imgs:
        story.append(Paragraph("EVIDENCIA DE IMÁGENES", est_sec))
        for idx, i in enumerate(lista_imgs):
            story.append(Spacer(1, 10))
            img_obj = Image(i['imagen'], width=2.4*inch, height=1.7*inch)
            t_img = Table([[img_obj, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{i['descripcion']}", est_txt)]], colWidths=[2.6*inch, 4.6*inch])
            story.append(t_img)

    story.append(Spacer(1, 60))
    # Doble firma sin raya
    t_firmas = Table([[Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    return f"""Estimados\n\nMe dirijo a para indicar el status de estado de la garantia del siguiente producto\n\nCLIENTE: {datos['cliente']}\nFACTURA: {fac_txt}\nFECHA: {datos['fecha_factura']}\nORDEN: {datos['orden']}\nCODIGO: {datos['serie']}\nDESCRIPCION: {datos['producto']}\n\nOBSERVACION: {datos['tipo_reporte']}\n\nDETALLES:\n{datos['observaciones']}\n\nAgradecido a la atención de la presente\nAtentamente \nIng. Pablo Lopez\nCoordinador Postventa Hamilton Beach\n0995115782"""

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

# BUSCADOR FUERA DEL FORMULARIO
orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: pass
        st.success("✅ Datos de la orden cargados.")

# FORMULARIO PARA EVITAR RECARGAS ACCIDENTALES
with st.form("form_reporte"):
    col1, col2 = st.columns(2)
    with col1:
        tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
        f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES) # Incluye Henry Beltran
        f_cliente = st.text_input("Cliente", value=c_v)
        f_prod = st.text_input("Producto", value=p_v)
    with col2:
        f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
        f_fac = st.text_input("Factura", value=f_v)
        f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
        f_serie = st.text_input("Serie/Artículo", value=s_v)

    f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")
    f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
    f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo.")
    f_obs = st.text_area("4. Observaciones", value="Luego de la revisión del artículo se observa lo siguiente: ")
    f_concl = st.text_area("5. Conclusiones")

    uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    # Botón de Generación dentro del Formulario
    submit = st.form_submit_button("💾 GENERAR ARCHIVOS", use_container_width=True)

if submit:
    # Procesar imágenes
    lista_imgs_final = []
    if uploaded_files:
        for file in uploaded_files:
            p_img = PilImage.open(file)
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            img_byte = BytesIO()
            p_img.save(img_byte, format='JPEG', quality=80)
            img_byte.seek(0)
            lista_imgs_final.append({"imagen": img_byte, "descripcion": "Evidencia técnica."})

    datos = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
        "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador,
        "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
        "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl, "tipo_reporte": tipo_rep
    }

    # Guardar en session_state para que los botones de descarga funcionen
    st.session_state.pdf_data = generar_pdf(datos, lista_imgs_final)
    st.session_state.txt_data = generar_txt_contenido(datos)
    st.session_state.nombre_orden = orden_id if orden_id else "reporte"

# --- 5. MOSTRAR BOTONES DE DESCARGA (Fuera del formulario) ---
if st.session_state.pdf_data is not None:
    st.markdown("---")
    st.success("✅ ¡Archivos listos!")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            label="📥 DESCARGAR PDF",
            data=st.session_state.pdf_data,
            file_name=f"Informe_{st.session_state.nombre_orden}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with c2:
        st.download_button(
            label="📥 DESCARGAR TXT",
            data=st.session_state.txt_data,
            file_name=f"Status_{st.session_state.nombre_orden}.txt",
            mime="text/plain",
            use_container_width=True
        )
    st.text_area("Copia rápida del TXT:", value=st.session_state.txt_data, height=200)
