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

# --- 2. CARGAR Y NORMALIZAR BASE DE DATOS (BLINDADO) ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                # Detectamos automáticamente el separador (coma o punto y coma)
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                
                # Normalización: Limpiamos espacios en blanco en los nombres de las columnas
                df.columns = df.columns.str.strip()
                
                # Mapeo exacto según tu imagen de encabezados
                nombres_clave = {
                    'Serie/Artículo': 'Serie',
                    'Fec. Fac. Min': 'Fec_Fac_Min',
                    'Fac. Min': 'Fac_Min',
                    'Fec_Fac_Min': 'Fec_Fac_Min', # Por si acaso
                    'Fac_Min': 'Fac_Min'
                }
                df = df.rename(columns=nombres_clave)
                return df
            except:
                continue
        st.error("Error crítico: No se pudo leer servicios.csv. Revisa el formato CSV UTF-8.")
        return pd.DataFrame()
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. GRÁFICO (REGLA: SIEMPRE GENERAR) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Eficiencia Mensual'], [95], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Nivel de Cumplimiento de Órdenes (%)")
    st.pyplot(fig)

# --- 4. GENERACIÓN DE PDF (CORRECCIÓN DE ATTRIBUTERROR) ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    # Intentamos HexColor (Mayúscula) para evitar el AttributeError
    try:
        color_principal = colors.HexColor("#003366")
    except AttributeError:
        color_principal = colors.hexColor("#003366")

    est_titulo = ParagraphStyle('T', fontSize=18, alignment=1, fontName='Helvetica-Bold', textColor=color_principal)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_principal, borderPadding=3)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica')

    story = []
    story.append(Paragraph("REPORTE TÉCNICO DE SERVICIO", est_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", ParagraphStyle('TR', alignment=1, textColor=colors.red, fontName='Helvetica-Bold')))
    story.append(HRFlowable(width="100%", thickness=1, color=color_principal, spaceAfter=10))
    
    # Tabla de Información principal
    data_info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {datos['factura']}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(data_info, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t)

    story.append(Paragraph("DETALLES TÉCNICOS DEL SERVICIO", est_sec))
    story.append(Paragraph(f"<b>Falla Reportada:</b> {datos['falla']}", est_txt))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Solución Técnica:</b> {datos['solucion']}", est_txt))

    # Imágenes (REGLA: SIEMPRE GENERAR SI SE CARGAN)
    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for img_file in imagenes_cargadas:
            try:
                img_file.seek(0)
                p_img = PilImage.open(img_file)
                img_b = BytesIO()
                if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
                p_img.save(img_b, format='JPEG', quality=80)
                img_b.seek(0)
                story.append(Image(img_b, width=3.2*inch, height=2.4*inch))
                story.append(Spacer(1, 10))
            except Exception as e:
                st.error(f"Error procesando imagen: {e}")

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ ---
st.title("🚀 Generador de Reportes Técnicos")
mostrar_grafico()

# Búsqueda inicial
with st.container():
    st.subheader("1. Buscar por Número de Orden")
    orden_busqueda = st.text_input("Ingrese la Orden y presione Enter")
    
    c_val, s_val, p_val, f_val, ff_val = "", "", "", "", date.today()
    
    if orden_busqueda and not df_db.empty:
        res = df_db[df_db['Orden'] == orden_busqueda]
        if not res.empty:
            row = res.iloc[0]
            c_val = row.get('Cliente', '')
            s_val = row.get('Serie', '')
            p_val = row.get('Producto', '')
            f_val = row.get('Fac_Min', '')
            try:
                # Intentamos parsear la fecha del CSV
                fecha_str = str(row.get('Fec_Fac_Min', ''))
                ff_val = pd.to_datetime(fecha_str).date()
            except: pass
            st.success(f"✅ Datos cargados automáticamente.")
        else:
            st.warning("⚠️ Orden no encontrada en el sistema.")

st.markdown("---")

# Formulario de entrada
with st.form("form_final"):
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    
    col1, col2 = st.columns(2)
    with col1:
        f_cliente = st.text_input("Nombre del Cliente", value=c_val)
        f_producto = st.text_input("Descripción del Producto", value=p_val)
        f_serie = st.text_input("Serie/Artículo", value=s_val)
    with col2:
        f_factura = st.text_input("Número de Factura", value=f_val)
        f_fecha_fac = st.date_input("Fecha de Compra", value=ff_val)
        f_tecnico = st.selectbox("Técnico que atendió", options=LISTA_TECNICOS)
    
    f_falla = st.text_area("Falla detectada")
    f_solucion = st.text_area("Trabajo realizado")
    f_fotos = st.file_uploader("Evidencia Fotográfica (JPG/PNG)", type=['jpg','png','jpeg'], accept_multiple_files=True)
    
    btn_generar = st.form_submit_button("💾 GENERAR E IMPRIMIR REPORTE")

if btn_generar:
    if f_cliente and f_falla and f_solucion:
        try:
            with st.spinner('Creando PDF...'):
                pdf_output = generar_pdf({
                    "tipo_reporte": tipo_rep, "orden": orden_busqueda, "cliente": f_cliente,
                    "factura": f_factura, "fecha_factura": f_fecha_fac, "producto": f_producto,
                    "serie": f_serie, "tecnico": f_tecnico, "falla": f_falla,
                    "solucion": f_solucion, "fecha_hoy": date.today()
                }, f_fotos)
                st.download_button("📥 Descargar Reporte Final (PDF)", data=pdf_output, file_name=f"Informe_{orden_busqueda}.pdf")
        except Exception as e:
            st.error(f"Ocurrió un error al generar el PDF: {e}")
    else:
        st.error("⚠️ Debes llenar Cliente, Falla y Solución.")

# --- 6. TABLA TÉCNICA (REGLA: SIEMPRE MOSTRAR) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
df_tec = pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
})
st.table(df_tec)
