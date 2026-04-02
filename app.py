import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# Importaciones de ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 0. CONFIGURACIÓN DE IA ---
# Se recomienda usar st.secrets["GROQ_API_KEY"] si se sube a la nube
GROQ_KEY = "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"
client = Groq(api_key=GROQ_KEY)

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

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

# CONSTANTES
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. FUNCIONES DE APOYO ---
def limpiar_texto_ia(texto):
    """Elimina asteriscos del texto generado por la IA."""
    return texto.replace("*", "").strip()

def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    color_azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []
    # Logos
    if os.path.exists("logo.png") and os.path.exists("logo_derecho.png"):
        header_table = Table([[Image("logo.png", width=1.4*inch, height=0.55*inch), Image("logo_derecho.png", width=1.4*inch, height=0.55*inch)]], colWidths=[3.7*inch, 3.7*inch])
        header_table.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
        story.append(header_table)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    # Tabla de datos
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    info = [[Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {fac_txt}", est_txt)],
            [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
            [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
            [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    # Secciones
    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Revisión Técnica", datos['rev_electro']),
        ("3. Observaciones", datos['observaciones']),
        ("4. Conclusiones", datos['conclusiones'])
    ]
    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
    
    if lista_imgs:
        story.append(Paragraph("EVIDENCIA DE IMÁGENES", est_sec))
        for idx, i in enumerate(lista_imgs):
            img_obj = Image(i['imagen'], width=2.4*inch, height=1.7*inch)
            t_img = Table([[img_obj, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{i['descripcion']}", est_txt)]], colWidths=[2.6*inch, 4.6*inch])
            story.append(t_img)

    story.append(Spacer(1, 60))
    t_firmas = Table([[Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    return (f"CLIENTE: {datos['cliente']}\nORDEN: {datos['orden']}\nFACTURA: {fac_txt}\nPRODUCTO: {datos['producto']}\nSERIE: {datos['serie']}\n\nCONCLUSIONES:\n{datos['conclusiones']}")

# --- 4. INTERFAZ ---
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

# NUEVA CASILLA PARA EL DAÑO (INTERNO)
f_daño = st.text_area("🔧 Daño detectado (Uso interno/IA)", placeholder="Escribe aquí el fallo específico (ej: antena rota, humedad)...")

# REVISIÓN FÍSICA (LO QUE SE VE EN PDF)
f_rev_fisica = st.text_area("1. Revisión Física (PDF)", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

if st.button("🤖 Autocompletar con IA"):
    if f_daño:
        with st.spinner("Analizando..."):
            try:
                prompt = f"Analiza el daño: '{f_daño}' en un {f_prod}. Genera REVISION_TEC: [pasos] y OBSERVACIONES: [hallazgos]. No uses asteriscos."
                response = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                ai_text = limpiar_texto_ia(response.choices[0].message.content)
                if "REVISION_TEC:" in ai_text:
                    st.session_state.ai_rev_electro = ai_text.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                    st.session_state.ai_obs = ai_text.split("OBSERVACIONES:")[1].strip()
                st.rerun()
            except Exception: st.error("Error de cuota. Reintente en 60 seg.")

f_rev_electro = st.text_area("2. Revisión Técnica", value=st.session_state.ai_rev_electro)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ai_obs)
f_concl = st.text_area("4. Conclusiones", value=TEXTOS_CONCLUSIONES.get(tipo_rep, ""))

uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
descripciones_capturadas = [st.text_input(f"Descripción #{i+1}", value="Evidencia.", key=f"d_{i}") for i, _ in enumerate(uploaded_files)]

if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    lista_imgs_final = []
    for file, d_u in zip(uploaded_files, descripciones_capturadas):
        img_byte = BytesIO(); PilImage.open(file).convert('RGB').save(img_byte, format='JPEG'); img_byte.seek(0)
        lista_imgs_final.append({"imagen": img_byte, "descripcion": d_u})

    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador, "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl}
    st.session_state.pdf_data = generar_pdf(datos, lista_imgs_final)
    st.session_state.txt_data = generar_txt_contenido(datos)
    st.success("✅ Listos")

if st.session_state.pdf_data:
    col_a, col_b = st.columns(2)
    with col_a: st.download_button("📥 PDF", data=st.session_state.pdf_data, file_name=f"Inf_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
    with col_b: st.download_button("📝 TXT", data=st.session_state.txt_data, file_name=f"Stat_{orden_id}.txt", mime="text/plain", use_container_width=True)
