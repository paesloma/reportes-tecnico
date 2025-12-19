import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime
from io import BytesIO
from PIL import Image as PilImage 
import os

# Importaciones de ReportLab para el PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador de Reporte Técnico", page_icon="🔧", layout="centered")

# --- 2. CARGAR BASE DE DATOS (CON CORRECCIÓN DE UNICODE) ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        try:
            # Intento con UTF-8 (Estándar)
            return pd.read_csv("servicios.csv", dtype={'Orden': str, 'Serie': str, 'Fac_Min': str}, encoding='utf-8')
        except UnicodeDecodeError:
            # Intento con Latin-1 (Común en Excel/Windows en español)
            return pd.read_csv("servicios.csv", dtype={'Orden': str, 'Serie': str, 'Fac_Min': str}, encoding='latin-1')
    else:
        return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()
LISTA_TECNICOS = ["Tec. Juan Diego Quezada", "Tec. Xavier Ramon", "Tec. Santiago Farez"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. GRÁFICO DE CONTROL (REGLA: SIEMPRE GENERAR) ---
def mostrar_grafico():
    fig, ax = plt.subplots(figsize=(7, 2))
    ax.barh(['Cumplimiento Mensual'], [85], color='#003366')
    ax.set_xlim(0, 100)
    ax.set_title("Progreso de Órdenes (%)")
    st.pyplot(fig)

# --- 4. FUNCIÓN GENERAR PDF ---
def generar_pdf(datos, imagenes_cargadas):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    estilo_titulo = ParagraphStyle('Title', fontSize=18, alignment=1, spaceAfter=10, fontName='Helvetica-Bold', textColor=colors.hexColor("#003366"))
    estilo_seccion = ParagraphStyle('Section', fontSize=10, spaceBefore=8, spaceAfter=6, fontName='Helvetica-Bold', textColor=colors.white, backColor=colors.hexColor("#003366"), borderPadding=3)
    estilo_campo = ParagraphStyle('Field', fontSize=9, fontName='Helvetica')

    story = []
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", estilo_titulo))
    story.append(Paragraph(f"TIPO: {datos['tipo_reporte']}", ParagraphStyle('T', alignment=1, textColor=colors.red, fontName='Helvetica-Bold')))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.hexColor("#003366"), spaceAfter=10))
    
    data_tabla = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", estilo_campo), Paragraph(f"<b>Factura:</b> {datos['factura']}", estilo_campo)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", estilo_campo), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", estilo_campo)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", estilo_campo), Paragraph(f"<b>Serie:</b> {datos['serie']}", estilo_campo)],
        [Paragraph(f"<b>Técnico:</b> {datos['tecnico']}", estilo_campo), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", estilo_campo)]
    ]
    t = Table(data_tabla, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    story.append(Paragraph("DETALLES TÉCNICOS", estilo_seccion))
    story.append(Paragraph(f"<b>Falla:</b> {datos['falla']}", estilo_campo))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Solución:</b> {datos['solucion']}", estilo_campo))

    if imagenes_cargadas:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", estilo_seccion))
        for img in imagenes_cargadas:
            img.seek(0)
            p_img = PilImage.open(img)
            img_b = BytesIO()
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            p_img.save(img_b, format='JPEG')
            img_b.seek(0)
            story.append(Image(img_b, width=3*inch, height=2.2*inch))
            story.append(Spacer(1, 10))

    # Pie de página: Revisado por
    story.append(Spacer(1, 30))
    data_firmas = [
        ["___________________________", "___________________________"],
        ["Revisado por", "Firma del Cliente"]
    ]
    tf = Table(data_firmas, colWidths=[3.5*inch, 3.5*inch])
    tf.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(tf)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- 5. INTERFAZ DE USUARIO ---
st.title("🔧 Generador de Reporte Técnico")
mostrar_grafico()

# Búsqueda por Orden
with st.container():
    st.subheader("1. Buscar Orden de Servicio")
    orden_id = st.text_input("Digite el número de Orden y presione Enter")
    
    # Valores iniciales
    c_def, s_def, p_def, f_def, ff_def = "", "", "", "", date.today()
    
    if orden_id:
        res = df_db[df_db['Orden'] == orden_id]
        if not res.empty:
            row = res.iloc[0]
            c_def, s_def, p_def, f_def = row['Cliente'], row['Serie'], row['Producto'], row['Fac_Min']
            try: ff_def = datetime.strptime(str(row['Fec_Fac_Min']), '%Y-%m-%d').date()
            except: pass
            st.success("✅ Datos cargados. Puede editarlos si es necesario.")
        else:
            st.warning("⚠️ Orden no encontrada en servicios.csv")

st.markdown("---")

# Formulario (Editable)
with st.form("main_form"):
    tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    
    col1, col2 = st.columns(2)
    with col1:
        f_cliente = st.text_input("Cliente", value=c_def)
        f_prod = st.text_input("Producto", value=p_def)
        f_serie = st.text_input("Serie/Artículo", value=s_def)
    with col2:
        f_fac = st.text_input("Factura", value=f_def)
        f_fec_fac = st.date_input("Fecha Factura", value=ff_def)
        f_tecnico = st.selectbox("Técnico", options=LISTA_TECNICOS)
    
    f_falla = st.text_area("Falla Reportada")
    f_solucion = st.text_area("Trabajo Realizado")
    imgs = st.file_uploader("Evidencia Fotográfica", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)

    submit = st.form_submit_button("💾 GENERAR INFORME PDF")

if submit:
    if not (f_cliente and f_falla and f_solucion):
        st.error("Por favor complete los campos obligatorios.")
    else:
        pdf = generar_pdf({
            "tipo_reporte": tipo, "orden": orden_id, "cliente": f_cliente,
            "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod,
            "serie": f_serie, "tecnico": f_tecnico, "falla": f_falla,
            "solucion": f_solucion, "fecha_hoy": date.today()
        }, imgs)
        st.download_button("📥 Descargar PDF", data=pdf, file_name=f"Reporte_{orden_id}.pdf")

# --- 6. TABLA DE TÉCNICOS (REGLA: SIEMPRE MOSTRAR) ---
st.markdown("---")
st.subheader("🧑‍🔧 Técnicos a Nivel Nacional")
df_tecnicos = pd.DataFrame({
    "Ciudad": ["Guayaquil", "Guayaquil", "Quito", "Quito", "Cuenca", "Cuenca", "Cuenca", "Cuenca"],
    "Técnicos": ["Carlos Jama", "Manuel Vera", "Javier Quiguango", "Wilson Quiguango", "Juan Diego Quezada", "Juan Farez", "Santiago Farez", "Xavier Ramón"]
})
st.table(df_tecnicos)
