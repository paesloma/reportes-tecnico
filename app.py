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

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Gestión Técnica", page_icon="🔧", layout="centered")

# --- 2. CARGAR BASE DE DATOS (BLINDADO) ---
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

# --- 3. GRÁFICO (REGLA: SIEMPRE GENERAR) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Rendimiento Mensual'], [95], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Nivel de Cumplimiento de Órdenes (%)")
    st.pyplot(fig)

# --- 4. GENERACIÓN DE PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    
    try: color_principal = colors.HexColor("#003366")
    except AttributeError: color_principal = colors.hexColor("#003366")

    est_titulo = ParagraphStyle('T', fontSize=18, alignment=1, fontName='Helvetica-Bold', textColor=color_principal)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_principal, borderPadding=3)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica')

    story = []
    story.append(Paragraph("REPORTE TÉCNICO DE SERVICIO", est_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", ParagraphStyle('TR', alignment=1, textColor=colors.red, fontName='Helvetica-Bold')))
    story.append(HRFlowable(width="100%", thickness=1, color=color_principal, spaceAfter=10))
    
    # Datos del Cliente
    info_cli = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t_cli = Table(info_cli, colWidths=[3.5*inch, 3.5*inch])
    t_cli.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t_cli)

    # NUEVAS SECCIONES REQUERIDAS
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Ingresa a servicio técnico", datos['ingreso_tec']),
        ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']),
        ("4. Observaciones", datos['observaciones']),
        ("5. Conclusiones", datos['conclusiones'])
    ]

    for titulo, contenido in secciones:
        story.append(Paragraph(titulo.upper(), est_sec))
        story.append(Paragraph(contenido.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 8))

    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for img_file in imagenes_cargadas:
            img_file.seek(0)
            p_img = PilImage.open(img_file)
            img_b = BytesIO()
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            p_img.save(img_b, format='JPEG', quality=80)
            img_b.seek(0)
            story.append(Image(img_b, width=3*inch, height=2.2*inch))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ ---
st.title("🚀 Gestión de Servicio Técnico")
mostrar_grafico()

# Búsqueda
with st.container():
    st.subheader("Búsqueda de Orden")
    orden_id = st.text_input("Ingrese la Orden")
    c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()
    if orden_id and not df_db.empty:
        res = df_db[df_db['Orden'] == orden_id]
        if not res.empty:
            row = res.iloc[0]
            c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
            try: ff_val = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
            except: pass
            st.success("✅ Datos cargados.")

st.markdown("---")

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
        f_tecnico = st.selectbox("Técnico", options=LISTA_TECNICOS)
    
    # --- NUEVAS SECCIONES CONFIGURABLES ---
    st.subheader("Detalles de la Revisión")
    f_rev_fisica = st.text_area("1. Revisión Física")
    f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
    
    # Texto predeterminado sección 3
    texto_electro = "Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo."
    f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value=texto_electro)
    
    # Texto predeterminado sección 4
    f_obs = st.text_area("4. Observaciones", value="Luego de la revisión del artículo se observa lo siguiente: ")

    # Lógica de Conclusiones automática
    concl_map = {
        "FUERA DE GARANTIA": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
        "INFORME TECNICO": "Con base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales.",
        "RECLAMO AL PROVEEDOR": "Se concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
    }
    f_conclusiones = st.text_area("5. Conclusiones (Automático según tipo)", value=concl_map[tipo_rep])
    
    f_fotos = st.file_uploader("Evidencia Fotográfica", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    if st.form_submit_button("💾 GENERAR REPORTE"):
        pdf = generar_pdf({
            "tipo_reporte": tipo_rep, "orden": orden_id, "cliente": f_cliente,
            "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod,
            "serie": f_serie, "tecnico": f_tecnico, "fecha_hoy": date.today(),
            "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
            "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_conclusiones
        }, f_fotos)
        st.download_button("📥 Descargar PDF", data=pdf, file_name=f"Reporte_{orden_id}.pdf")

# --- 6. TABLA (REGLA: SIEMPRE MOSTRAR) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
st.table(pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
}))
