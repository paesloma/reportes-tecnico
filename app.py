import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os

# Importaciones de ReportLab (PDF)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="wide")

# Inicialización de estados
claves_estado = ['pdf_es', 'txt_es']
for key in claves_estado:
    if key not in st.session_state:
        st.session_state[key] = None

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
            except Exception:
                continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()

# --- CONSTANTES ---
LISTA_TECNICOS = [
    "Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango",
    "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera",
    "Tec. Juan Farez", "Tec. Santiago Farez", "Tec.Ronald Paladinez", "Tec. Saul Vite",
    "Tec. Miguel Meza", "Tec German Tenemaza", "CISTRONIC", "Taller Externo", "Tec. Jorge Pintado"
]
LISTA_REALIZADORES = [
    "Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle",
    "Ing. Guillermo Ortiz", "Ing. Adrian Aguilar", "Ing. John Juela"
]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "Tras la evaluación técnica, se determina que la falla presentada no responde a defectos de fabricación ni de materiales, sino a factores externos o condiciones de operación inadecuadas. En consecuencia, el equipo queda excluido de la cobertura de garantía.",
    "INFORME TECNICO": "De acuerdo con la evaluación realizada, el equipo no presenta fallas y funciona correctamente según las indicaciones del fabricante, entregándose en óptimas condiciones de operación.",
    "RECLAMO AL PROVEEDOR": "Tras la evaluación técnica efectuada, se confirma que el daño identificado responde a un defecto de manufactura. Por lo tanto, se solicita su colaboración para proceder con la gestión de reclamo al proveedor."
}

# Plantillas de Observaciones
PLANTILLAS_OBSERVACIONES = {
    "Personalizado (Por defecto)": "Luego de la revisión del artículo se observa lo siguiente: ",
    "Negación - Humedad interna": "Luego de realizar la revisión física e interna del artículo, se constató el ingreso y acumulación de humedad que compromete directamente a la tarjeta electrónica, los integrados COF y el cable flex. Como consecuencia directa de esta exposición a la humedad, los componentes afectados presentan signos evidentes de sulfatación y corrosión en sus pistas y puntos de soldadura.",
    "Negación - Ingreso de insectos": "Tras la inspección técnica del artículo, se evidenció el ingreso y alojamiento de insectos en el interior del chasis. Debido a que sus residuos biológicos son corrosivos, el contacto directo con las tarjetas electrónicas provocó procesos de sulfatación y microcortocircuitos que comprometen la integridad de los circuitos y componentes.",
    "Negación - Golpe o rotura de pantalla": "Luego de realizar la revisión física del equipo, se constató la presencia de un impacto directo y fractura en el panel de visualización. Dado que este tipo de daño mecánico responde a factores externos, golpes o manipulación indebida y no a defectos de fabricación, el artículo queda fuera de los términos de cobertura de garantía.",
    "Negación - Problemas eléctricos": "De acuerdo con el diagnóstico técnico efectuado, el daño identificado en los componentes internos fue ocasionado por irregularidades en el suministro eléctrico externo, tales como picos de tensión, conexiones deficientes o falta de sistema de puesta a tierra. En virtud de que la garantía del fabricante aplica únicamente a fallas de manufactura y no contempla daños por factores externos de instalación, la presente solicitud no procede bajo cobertura de garantía.",
    "Negación - Uso sin aceite": "Tras la inspección técnica del artículo, se evidenció que el equipo operó sin lubricante o con un nivel de aceite por debajo del mínimo requerido por el fabricante. La ausencia de una película lubricante adecuada provocó fricción directa, sobrecalentamiento y desgaste severo en los componentes mecánicos internos. Al tratarse de una omisión en el mantenimiento y operación adecuada del equipo, la avería queda excluida de la cobertura de garantía."
}

if "obs_text" not in st.session_state:
    st.session_state.obs_text = PLANTILLAS_OBSERVACIONES["Personalizado (Por defecto)"]

def actualizar_observacion():
    seleccion = st.session_state.sel_plantilla_obs
    st.session_state.obs_text = PLANTILLAS_OBSERVACIONES[seleccion]

# Títulos y etiquetas dinámicas según el tipo de reporte seleccionado
def obtener_titulos_por_tipo(tipo_rep):
    tipo_upper = tipo_rep.upper()
    if "GARANTIA" in tipo_upper:
        return "INFORME FUERA DE GARANTIA"
    elif "TECNICO" in tipo_upper:
        return "INFORME TECNICO"
    elif "PROVEEDOR" in tipo_upper:
        return "RECLAMO AL PROVEEDOR"
    return tipo_rep

LBL = {
    "orden": "Orden", "fac": "Factura", "cliente": "Cliente",
    "fec_fac": "Fecha factura", "prod": "Articulo", "serie": "Serie", "realizador": "Realizado por",
    "fec_rep": "Fecha reclamo", "revisador": "Revisado por", "evidencia": "EVIDENCIA DE IMÁGENES",
    "figura": "Figura", "marca": "Marca", "modelo": "Modelo", "repuesto": "Repuesto",
    "codigo": "Código", "cantidad": "Cantidad", "reporte": "Reporte"
}

# --- 3. FUNCIONES DE GENERACIÓN ---
def agregar_marca_agua(canvas, doc):
    watermark_file = "watermark.png"
    if os.path.exists(watermark_file):
        try:
            canvas.saveState()
            canvas.setFillAlpha(0.12)
            canvas.drawImage(
                watermark_file,
                0,
                0,
                width=canvas._pagesize[0],
                height=canvas._pagesize[1],
                mask='auto',
                preserveAspectRatio=True,
                anchor='c'
            )
            canvas.restoreState()
        except Exception:
            pass

def generar_pdf(datos, secciones_activas, lista_imgs):
    l = LBL
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch
    )
    color_azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    est_fig = ParagraphStyle('FIG', fontSize=10, fontName='Helvetica-Bold', alignment=1, spaceBefore=4)
    
    story = []

    # Cabecera (Logos)
    logo_izq_path = "logo.png"
    logo_der_path = "logo_derecho.png"
    col_izq = []
    col_der = []

    if os.path.exists(logo_izq_path):
        col_izq.append(RLImage(logo_izq_path, width=1.4 * inch, height=0.55 * inch))

    if os.path.exists(logo_der_path):
        img_der = RLImage(logo_der_path, width=1.4 * inch, height=0.55 * inch)
        img_der.hAlign = 'RIGHT'
        col_der.append(img_der)

    if col_izq or col_der:
        header_table = Table([[col_izq, col_der]], colWidths=[3.7 * inch, 3.7 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT')
        ]))
        story.append(header_table)
    
    story.append(Spacer(1, 10))
    
    # Título dinámico basado en la opción seleccionada
    titulo_principal = obtener_titulos_por_tipo(datos['tipo_reporte_original'])
    story.append(Paragraph(titulo_principal, est_titulo))
    story.append(Spacer(1, 15))
    
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", "nan", ""] else datos['factura']
    es_reclamo = "RECLAMO AL PROVEEDOR" in str(datos['tipo_reporte_original']).upper()
    
    if es_reclamo:
        rep_txt = f"<font color='red'>{datos['tipo_reporte']}</font>"
        info = [
            [Paragraph(f"<b>{l['orden']}:</b>", est_txt), Paragraph(f"{datos['orden']}", est_txt), Paragraph(f"<b>{l['fec_rep']}:</b>", est_txt), Paragraph(f"{datos['fecha_reporte']}", est_txt)],
            [Paragraph(f"<b>{l['cliente']}:</b>", est_txt), Paragraph(f"{datos['cliente']}", est_txt), Paragraph(f"<b>{l['prod']}:</b>", est_txt), Paragraph(f"{datos['producto']}", est_txt)],
            [Paragraph(f"<b>{l['fac']}:</b>", est_txt), Paragraph(f"{fac_txt}", est_txt), Paragraph(f"<b>{l['marca']}:</b>", est_txt), Paragraph(f"{datos['marca']}", est_txt)],
            [Paragraph(f"<b>{l['fec_fac']}:</b>", est_txt), Paragraph(f"{datos['fecha_factura']}", est_txt), Paragraph(f"<b>{l['modelo']}:</b>", est_txt), Paragraph(f"{datos['modelo']}", est_txt)],
            [Paragraph(f"<b>{l['repuesto']}:</b>", est_txt), Paragraph(f"{datos['repuesto']}", est_txt), Paragraph(f"<b>{l['codigo']}:</b>", est_txt), Paragraph(f"{datos['codigo']}", est_txt)],
            [Paragraph(f"<b>{l['cantidad']}:</b>", est_txt), Paragraph(f"{datos['cantidad']}", est_txt), Paragraph(f"<b>{l['reporte']}:</b>", est_txt), Paragraph(rep_txt, est_txt)]
        ]
        t = Table(info, colWidths=[1.1 * inch, 2.6 * inch, 1.1 * inch, 2.6 * inch])
    else:
        info = [
            [Paragraph(f"<b>{l['orden']}:</b> {datos['orden']}", est_txt), Paragraph(f"<b>{l['fac']}:</b> {fac_txt}", est_txt)],
            [Paragraph(f"<b>{l['cliente']}:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>{l['fec_fac']}:</b> {datos['fecha_factura']}", est_txt)],
            [Paragraph(f"<b>{l['prod']}:</b> {datos['producto']}", est_txt), Paragraph(f"<b>{l['serie']}:</b> {datos['serie']}", est_txt)],
