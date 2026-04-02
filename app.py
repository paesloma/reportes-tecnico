import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY

# --- 0. CONFIGURACIÓN DE IA ---
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y ESTADOS ---
st.set_page_config(page_title="Gestión de Reportes Técnicos", page_icon="🔧", layout="centered")

if 'lista_fotos' not in st.session_state: st.session_state.lista_fotos = []
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'ai_rev_electro' not in st.session_state: st.session_state.ai_rev_electro = ""
if 'ai_obs' not in st.session_state: st.session_state.ai_obs = ""
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'txt_data' not in st.session_state: st.session_state.txt_data = None

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for encoding in ['utf-8', 'latin-1']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=encoding, sep=None, engine='python')
                df.columns = df.columns.str.strip()
                df = df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
                return df
            except: continue
    return pd.DataFrame()

df_db = cargar_datos_servicios()

# CONSTANTES DE INTERFAZ
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. FUNCIONES DE GENERACIÓN ---

def añadir_marca_agua(canvas, doc):
    if os.path.exists("marca_agua.png"):
        canvas.saveState()
        canvas.drawImage("marca_agua.png", 1.25*inch, 2.5*inch, width=6*inch, height=6*inch, mask='auto')
        canvas.restoreState()

def generar_pdf(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    # ESTILOS CON JUSTIFICACIÓN Y ESPACIADO
    color_azul = colors.HexColor("#0056b3")
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=4, spaceBefore=12, spaceAfter=6)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=12, alignment=TA_JUSTIFY, leftIndent=5, rightIndent=5)
    
    story = []
    
    # Encabezado Logos
    if os.path.exists("logo.png") and os.path.exists("logo_derecho.png"):
        header = Table([[Image("logo.png", width=1.5*inch, height=0.6*inch), Image("logo_derecho.png", width=1.5*inch, height=0.6*inch)]], colWidths=[3.7*inch, 3.7*inch])
        header.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
        story.append(header)

    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    # Tabla de Datos Principales
    info = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
            [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"],
            [f"Serie: {datos['serie']}", f"Fecha Reporte: {datos['fecha_hoy']}"]]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('FONTSIZE', (0,0), (-1,-1), 9), ('PADDING', (0,0), (-1,-1), 4)]))
    story.append(t)

    # Secciones con Justificación
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Revisión Técnica", datos['rev_electro']),
        ("3. Observaciones", datos['observaciones']),
        ("4. Conclusiones", datos['conclusiones'])
    ]

    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
    
    # Evidencia Fotográfica Justificada
    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for f in fotos:
            img = Image(BytesIO(f['data']), width=2.5*inch, height=1.8*inch)
            # Tabla para alinear imagen y texto descriptivo justificado
            ft = Table([[img, Paragraph(f['desc'], est_txt)]], colWidths=[2.7*inch, 4.3*inch])
            ft.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 10)]))
            story.append(ft)

    doc.build(story, onLaterPages=añadir_marca_agua, onFirstPage=añadir_marca_agua)
    buffer.seek(0)
    return buffer.read()

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v = "", "", "", ""

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')

col1, col2 = st.columns(2)
with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_hoy = st.date_input("Fecha Reporte", value=date.today())
    f_serie = st.text_input("Serie/Artículo", value=s_v)

f_daño = st.text_area("🔧 Daño detectado (Uso interno/IA)", placeholder="Describa el fallo...")
f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("IA analizando..."):
            prompt = f"Analiza: {f_daño} en {f_prod}. Genera REVISION_TEC: [pasos] y OBSERVACIONES: [hallazgos]. No uses asteriscos."
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.replace("*", "").strip()
            if "REVISION_TEC:" in clean:
                st.session_state.ai_rev_electro = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ai_obs = clean.split("OBSERVACIONES:")[1].strip()
            st.rerun()

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones", value=TEXTOS_CONCLUSIONES.get(f_tipo, ""))

# --- EVIDENCIA ---
st.subheader("🖼️ Evidencia Fotográfica")
up_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if up_files:
    for f in up_files:
        if f.name not in [x['name'] for x in st.session_state.lista_fotos]:
            st.session_state.lista_fotos.append({"name": f.name, "data": f.getvalue(), "desc": "Evidencia técnica."})

for i, foto in enumerate(st.session_state.lista_fotos):
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 0.5])
        c1.image(foto['data'], width=100)
        st.session_state.lista_fotos[i]['desc'] = c2.text_input(f"Descripción #{i+1}", value=foto['desc'], key=f"d_{i}")
        if c3.button("🗑️", key=f"b_{i}"):
            st.session_state.lista_fotos.pop(i)
            st.session_state.uploader_key += 1
            st.rerun()

# --- ACCIONES ---
if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador, "fecha_hoy": f_fec_hoy, "rev_fisica": f_rev_fisica, "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl}
    st.session_state.pdf_data = generar_pdf(datos, st.session_state.lista_fotos)
    # Generación simple de TXT
    txt_str = f"ORDEN: {orden_id}\nCLIENTE: {f_cliente}\n\n1. FISICA:\n{f_rev_fisica}\n\n2. TECNICA:\n{f_rev_electro}\n\n4. CONCLU:\n{f_concl}"
    st.session_state.txt_data = txt_str.encode('utf-8')
    st.success("✅ Documentos generados con éxito")

if st.session_state.pdf_data:
    col_a, col_b = st.columns(2)
    col_a.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Reporte_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
    col_b.download_button("📥 Descargar TXT", data=st.session_state.txt_data, file_name=f"Resumen_{orden_id}.txt", mime="text/plain", use_container_width=True)
