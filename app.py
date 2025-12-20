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

# --- 2. CARGAR Y NORMALIZAR BASE DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                
                # NORMALIZACIÓN DE COLUMNAS: Quitamos espacios y renombramos según tu imagen
                df.columns = df.columns.str.strip()
                nombres_clave = {
                    'Serie/Artículo': 'Serie',
                    'Fec. Fac. Min': 'Fec_Fac_Min',
                    'Fac. Min': 'Fac_Min'
                }
                df = df.rename(columns=nombres_clave)
                return df
            except:
                continue
        return pd.DataFrame()
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. GRÁFICO (REGLA: SIEMPRE GENERAR) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Rendimiento Actual'], [92], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Nivel de Resolución Mensual (%)")
    st.pyplot(fig)

# --- 4. GENERACIÓN DE PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    est_titulo = ParagraphStyle('T', fontSize=18, alignment=1, fontName='Helvetica-Bold', textColor=colors.hexColor("#003366"))
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.hexColor("#003366"), borderPadding=3)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica')

    story = []
    story.append(Paragraph("REPORTE TÉCNICO DE SERVICIO", est_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", ParagraphStyle('TR', alignment=1, textColor=colors.red, fontName='Helvetica-Bold')))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.hexColor("#003366"), spaceAfter=10))
    
    data_info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(data_info, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t)

    story.append(Paragraph("DETALLES DEL TRABAJO", est_sec))
    story.append(Paragraph(f"<b>Falla:</b> {datos['falla']}", est_txt))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Solución:</b> {datos['solucion']}", est_txt))

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

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ ---
st.title("🔧 Generador de Reportes Técnicos")
mostrar_grafico()

with st.container():
    st.subheader("1. Localizar Orden")
    orden_busqueda = st.text_input("Ingrese el número de Orden")
    
    c_val, s_val, p_val, f_val, ff_val = "", "", "", "", date.today()
    
    if orden_busqueda and not df_db.empty:
        res = df_db[df_db['Orden'] == orden_busqueda]
        if not res.empty:
            row = res.iloc[0]
            # Usamos nombres normalizados para evitar el KeyError
            c_val = row.get('Cliente', '')
            s_val = row.get('Serie', '')
            p_val = row.get('Producto', '')
            f_val = row.get('Fac_Min', '')
            try:
                ff_val = datetime.strptime(str(row.get('Fec_Fac_Min', '')), '%Y-%m-%d').date()
            except: pass
            st.success(f"✅ Datos cargados.")
        else:
            st.warning("No se encontró la orden.")

st.markdown("---")

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
        f_tecnico = st.selectbox("Técnico", options=LISTA_TECNICOS)
    
    f_falla = st.text_area("Falla Reportada")
    f_solucion = st.text_area("Trabajo Realizado")
    f_fotos = st.file_uploader("Subir Imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    btn_generar = st.form_submit_button("🚀 GENERAR PDF")

if btn_generar:
    if f_cliente and f_falla:
        pdf = generar_pdf({
            "tipo_reporte": tipo_rep, "orden": orden_busqueda, "cliente": f_cliente,
            "factura": f_factura, "fecha_factura": f_fecha_fac, "producto": f_producto,
            "serie": f_serie, "tecnico": f_tecnico, "falla": f_falla,
            "solucion": f_solucion, "fecha_hoy": date.today()
        }, f_fotos)
        st.download_button("📥 Descargar Reporte", data=pdf, file_name=f"Reporte_{orden_busqueda}.pdf")

# --- 6. TABLA (REGLA: SIEMPRE MOSTRAR) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
st.table(pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
}))
