import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
import google.generativeai as genai

# --- 0. CONFIGURACIÓN DE GEMINI ---
# Intentamos configurar la IA. Si falla, la app seguirá funcionando pero sin el asistente.
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        # Usamos la ruta completa del modelo para evitar errores de 'NotFound'
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        ia_disponible = True
    else:
        st.error("Falta la GEMINI_API_KEY en los Secrets de Streamlit.")
        ia_disponible = False
except Exception as e:
    st.error(f"Error al configurar Gemini: {e}")
    ia_disponible = False

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None
if 'ai_electro' not in st.session_state:
    st.session_state.ai_electro = ""
if 'ai_obs' not in st.session_state:
    st.session_state.ai_obs = ""

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

# --- CONSTANTES ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. FUNCIONES DE GENERACIÓN PDF (ReportLab) ---
def agregar_marca_agua(canvas, doc):
    watermark_file = "watermark.png"
    if os.path.exists(watermark_file):
        canvas.saveState()
        canvas.setFillAlpha(0.12)
        canvas.drawImage(watermark_file, 0, 0, width=canvas._pagesize[0], height=canvas._pagesize[1], mask='auto', preserveAspectRatio=True, anchor='c')
        canvas.restoreState()

def generar_pdf(datos, lista_imgs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    color_azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []
    
    # Cabecera con logos
    logo_izq, logo_der = "logo.png", "logo_derecho.png"
    c_izq, c_der = [], []
    if os.path.exists(logo_izq): c_izq.append(Image(logo_izq, width=1.4*inch, height=0.55*inch))
    if os.path.exists(logo_der): 
        img_d = Image(logo_der, width=1.4*inch, height=0.55*inch)
        img_d.hAlign = 'RIGHT'
        c_der.append(img_d)

    header_table = Table([[c_izq, c_der]], colWidths=[3.7*inch, 3.7*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    story.append(Spacer(1, 15))
    
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    info = [
        [Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {fac_txt}", est_txt)],
        [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
        [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
        [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]
    ]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)]))
    story.append(t)

    secciones = [
        ("1. Revisión Física", datos['rev_fisica']),
        ("2. Ingresa a servicio técnico", datos['ingreso_tec']), 
        ("3. Revisión electro-electrónica-mecanica", datos['rev_electro']), 
        ("4. Observaciones", datos['observaciones']), 
        ("5. Conclusiones", datos['conclusiones'])
    ]

    for tit, cont in secciones:
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
    t_firmas = Table([[Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    
    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    return f"Estimados\n\nStatus de garantía:\nCLIENTE: {datos['cliente']}\nFACTURA: {fac_txt}\nORDEN: {datos['orden']}\nPRODUCTO: {datos['producto']}\n\nCONCLUSIONES:\n{datos['conclusiones']}\n\nAtentamente,\n{datos['realizador']}"

# --- 4. INTERFAZ ---
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: pass

st.markdown("### Datos del Reporte")
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

f_rev_fisica = st.text_area("1. Revisión Física", value=f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo.")

# --- LÓGICA DE IA ---
st.markdown("### ✨ Asistente de IA")
if st.button("🤖 Autocompletar con IA"):
    if ia_disponible and f_rev_fisica:
        with st.spinner("Gemini está analizando..."):
            try:
                prompt = f"Como técnico experto, analiza esta revisión física: '{f_rev_fisica}' del producto '{f_prod}'. Genera: 1- Pasos técnicos de revisión electro-mecánica. 2- Observaciones. Formato: ELECTRO: [texto] OBS: [texto]"
                response = model.generate_content(prompt)
                res_text = response.text
                if "ELECTRO:" in res_text and "OBS:" in res_text:
                    st.session_state.ai_electro = res_text.split("ELECTRO:")[1].split("OBS:")[0].strip()
                    st.session_state.ai_obs = res_text.split("OBS:")[1].strip()
                else:
                    st.session_state.ai_electro = res_text
            except Exception as e:
                st.error(f"Error al generar con IA: {e}")
    else:
        st.warning("IA no configurada o campo de revisión vacío.")

f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value=st.session_state.ai_electro if st.session_state.ai_electro else "Revisión estándar de líneas de energía y componentes.")
f_obs = st.text_area("4. Observaciones", value=st.session_state.ai_obs if st.session_state.ai_obs else "Se procede con el diagnóstico preventivo.")
f_concl = st.text_area("5. Conclusiones", value=TEXTOS_CONCLUSIONES.get(tipo_rep, ""), height=150)

# --- IMÁGENES ---
st.markdown("### 📸 Evidencia")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)
desc_list = []
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        desc = st.text_input(f"Descripción Imagen #{idx+1}", value="Evidencia técnica.", key=f"d_{idx}")
        desc_list.append(desc)

if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    imgs_final = []
    for file, d in zip(uploaded_files, desc_list):
        p_img = PilImage.open(file)
        if p_img.mode != 'RGB': p_img = p_img.convert('RGB')
        b = BytesIO()
        p_img.save(b, format='JPEG', quality=80)
        b.seek(0)
        imgs_final.append({"imagen": b, "descripcion": d})

    datos = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac, "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador, "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec, "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl, "tipo_reporte": tipo_rep}
    
    st.session_state.pdf_data = generar_pdf(datos, imgs_final)
    st.session_state.txt_data = generar_txt_contenido(datos)
    st.success("✅ Generado")

if st.session_state.pdf_data:
    c1, c2 = st.columns(2)
    st.download_button("Descargar PDF", st.session_state.pdf_data, f"Informe_{orden_id}.pdf", "application/pdf")
    st.download_button("Descargar TXT", st.session_state.txt_data, f"Status_{orden_id}.txt", "text/plain")
