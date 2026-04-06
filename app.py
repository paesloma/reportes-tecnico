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

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None
if 'fotos_lista' not in st.session_state:
    st.session_state.fotos_lista = []
if 'ia_obs' not in st.session_state:
    st.session_state.ia_obs = "Luego de la revisión del artículo se observa lo siguiente: "

# Configuración de Groq
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.warning("🔑 Configure 'GROQ_API_KEY' en los Secrets para usar la IA.")
    client = None

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

# --- CONSTANTES Y LISTAS ---
LISTA_TECNICOS = [
    "Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango",
    "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera",
    "Tec. Juan Farez", "Tec. Santiago Farez"
]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. FUNCIONES DE GENERACIÓN ---
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
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11, alignment=4) # alignment=4 es Justificado
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []

    logo_izq_path = "logo.png"
    logo_der_path = "logo_derecho.png"
    
    col_izq = []
    if os.path.exists(logo_izq_path):
        col_izq.append(Image(logo_izq_path, width=1.4*inch, height=0.55*inch))
    
    col_der = []
    if os.path.exists(logo_der_path):
        img_der = Image(logo_der_path, width=1.4*inch, height=0.55*inch)
        img_der.hAlign = 'RIGHT'
        col_der.append(img_der)

    header_table = Table([[col_izq, col_der]], colWidths=[3.7*inch, 3.7*inch])
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
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
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
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for idx, i in enumerate(lista_imgs):
            story.append(Spacer(1, 10))
            try:
                img_obj = Image(i['imagen'], width=2.4*inch, height=1.7*inch)
                desc_texto = i['descripcion']
                t_img = Table([[img_obj, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{desc_texto}", est_txt)]], colWidths=[2.6*inch, 4.6*inch])
                t_img.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
                story.append(t_img)
            except Exception as e:
                story.append(Paragraph(f"Error cargando imagen {idx+1}", est_txt))

    story.append(Spacer(1, 60))
    t_firmas = Table([[Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    
    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    return (
        f"Estimados\n\n"
        f"Me dirijo a usted para indicar el status de estado de la garantía del siguiente producto:\n\n"
        f"CLIENTE: {datos['cliente']}\n"
        f"FACTURA: {fac_txt}\n"
        f"FECHA DE FACTURA: {datos['fecha_factura']}\n"
        f"ORDEN DE SERVICIO: {datos['orden']}\n"
        f"SERIE/CÓDIGO: {datos['serie']}\n"
        f"PRODUCTO: {datos['producto']}\n"
        f"TÉCNICO ASIGNADO: {datos['tecnico']}\n\n"
        f"TIPO DE REPORTE: {datos['tipo_reporte']}\n\n"
        f"CONCLUSIONES:\n{datos['conclusiones']}\n\n"
        f"Agradecido a la atención de la presente.\n\n"
        f"Atentamente,\n"
        f"{datos['realizador']}\n"
        f"Coordinador Postventa"
    )

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
f_ingreso_tec = st.text_area("2. Ingresa a servicio técnico")
f_rev_electro = st.text_area("3. Revisión electro-electrónica-mecanica", value="Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo.\nSe procede a revisar el sistema mecanico del equipo")

# --- IA SOLO PARA OBSERVACIONES ---
st.markdown("---")
st.markdown("### 🤖 Asistente IA para Observaciones")
prompt_ia = st.text_area("Describa la falla para que la IA redacte el texto:")
if st.button("🪄 Redactar Observaciones"):
    if prompt_ia and client:
        with st.spinner("Generando observaciones limpias..."):
            sys_msg = "Eres un perito técnico. Redacta únicamente el párrafo de observaciones técnicas basadas en la falla indicada. No uses comillas, ni viñetas, ni títulos. Solo texto plano, profesional."
            resp = client.chat.completions.create(
                messages=[{"role": "system", "content": sys_msg},
                          {"role": "user", "content": f"Falla: {prompt_ia}. Producto: {f_prod}"}],
                model="llama-3.3-70b-versatile"
            ).choices[0].message.content
            st.session_state.ia_obs = resp.replace('"', '').strip()
            st.rerun()

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_obs, height=120)

texto_conclusiones_default = TEXTOS_CONCLUSIONES.get(tipo_rep, "")
f_concl = st.text_area("5. Conclusiones", value=texto_conclusiones_default, height=120)

# --- SECCIÓN DE IMÁGENES INTERACTIVA CON ELIMINACIÓN ---
st.markdown("---")
st.markdown("### 📸 Evidencia Fotográfica")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)

# Guardar archivos subidos en session_state para poder borrarlos luego
if uploaded_files:
    for file in uploaded_files:
        if not any(f['name'] == file.name for f in st.session_state.fotos_lista):
            st.session_state.fotos_lista.append({
                'name': file.name,
                'file': file.read(),
                'desc': "Evidencia técnica."
            })

if st.session_state.fotos_lista:
    st.info("📝 Edita la descripción o elimina la imagen si te equivocaste:")
    for i, foto in enumerate(st.session_state.fotos_lista):
        c_img, c_desc, c_btn = st.columns([1, 3, 1])
        with c_img:
            st.image(foto['file'], use_container_width=True)
        with c_desc:
            st.session_state.fotos_lista[i]['desc'] = st.text_input(f"Descripción Imagen #{i+1}", value=foto['desc'], key=f"desc_{i}")
        with c_btn:
            if st.button("🗑️ Eliminar", key=f"del_{i}"):
                st.session_state.fotos_lista.pop(i)
                st.rerun()

st.markdown("---")

# --- BOTÓN DE GENERACIÓN ---
if st.button("💾 GENERAR ARCHIVOS", use_container_width=True):
    lista_imgs_final = []
    
    # Procesamos las imágenes que quedaron en session_state (después de borrar las no deseadas)
    for foto in st.session_state.fotos_lista:
        try:
            p_img = PilImage.open(BytesIO(foto['file']))
            if p_img.mode in ('RGBA', 'P'): p_img = p_img.convert('RGB')
            img_byte = BytesIO()
            p_img.save(img_byte, format='JPEG', quality=80)
            img_byte.seek(0)
            
            lista_imgs_final.append({
                "imagen": img_byte, 
                "descripcion": foto['desc'] 
            })
        except Exception as e:
            st.error(f"Error procesando imagen {foto['name']}: {e}")

    datos = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
        "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador,
        "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "ingreso_tec": f_ingreso_tec,
        "rev_electro": f_rev_electro, "observaciones": f_obs, "conclusiones": f_concl, "tipo_reporte": tipo_rep
    }

    st.session_state.pdf_data = generar_pdf(datos, lista_imgs_final)
    st.session_state.txt_data = generar_txt_contenido(datos)
    st.success("✅ Archivos generados correctamente")

# --- DESCARGA ---
if st.session_state.pdf_data is not None:
    st.markdown("### 📥 Descargas")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Descargar PDF", data=st.session_state.pdf_data, file_name=f"Informe_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
    with c2:
        st.download_button("Descargar TXT", data=st.session_state.txt_data, file_name=f"Status_{orden_id}.txt", mime="text/plain", use_container_width=True)
