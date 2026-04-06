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

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="centered")

if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'txt_data' not in st.session_state: st.session_state.txt_data = None
if 'imagenes_guardadas' not in st.session_state: st.session_state.imagenes_guardadas = []
# Estructura base solicitada para la IA
if 'texto_ia_obs' not in st.session_state: 
    st.session_state.texto_ia_obs = "**Procedimiento de inspección:**\n\n**Resultados:**\n\n**Conclusión:**\n\n**Recomendaciones:**"

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
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    
    story = []
    logo_izq_path, logo_der_path = "logo.png", "logo_derecho.png"
    col_izq, col_der = [], []
    if os.path.exists(logo_izq_path): col_izq.append(Image(logo_izq_path, width=1.4*inch, height=0.55*inch))
    if os.path.exists(logo_der_path):
        img_der = Image(logo_der_path, width=1.4*inch, height=0.55*inch)
        img_der.hAlign = 'RIGHT'
        col_der.append(img_der)

    header_table = Table([[col_izq, col_der]], colWidths=[3.7*inch, 3.7*inch])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header_table)
    story.append(Spacer(1, 10)); story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo)); story.append(Spacer(1, 15))
    
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    info = [[Paragraph(f"<b>Orden:</b> {datos['orden']}", est_txt), Paragraph(f"<b>Factura:</b> {fac_txt}", est_txt)],
            [Paragraph(f"<b>Cliente:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>Fec. Factura:</b> {datos['fecha_factura']}", est_txt)],
            [Paragraph(f"<b>Producto:</b> {datos['producto']}", est_txt), Paragraph(f"<b>Serie:</b> {datos['serie']}", est_txt)],
            [Paragraph(f"<b>Realizado por:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>Fecha Reporte:</b> {datos['fecha_hoy']}", est_txt)]]
    t = Table(info, colWidths=[3.7*inch, 3.7*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

    secciones = [
        ("1. Revisión Física", datos['rev_fisica']), 
        ("2. Revisión electro-electrónica-mecanica", datos['rev_electro']), 
        ("3. Observaciones", datos['observaciones']), 
        ("4. Conclusiones", datos['conclusiones'])
    ]

    for tit, cont in secciones:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 5))

    if lista_imgs:
        story.append(Paragraph("EVIDENCIA DE IMÁGENES", est_sec))
        for idx, i in enumerate(lista_imgs):
            story.append(Spacer(1, 10))
            try:
                img_obj = Image(i['imagen'], width=2.4*inch, height=1.7*inch)
                t_img = Table([[img_obj, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{i['descripcion']}", est_txt)]], colWidths=[2.6*inch, 4.6*inch])
                story.append(t_img)
            except: story.append(Paragraph(f"Error cargando imagen {idx+1}", est_txt))

    story.append(Spacer(1, 60))
    t_firmas = Table([[Paragraph("Realizado por:", est_firma), Paragraph("Revisado por:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() == "0" else datos['factura']
    return f"ORDEN: {datos['orden']}\nCLIENTE: {datos['cliente']}\nFACTURA: {fac_txt}\nPRODUCTO: {datos['producto']}\nSERIE: {datos['serie']}\n\nOBSERVACIONES:\n{datos['observaciones']}\n\nCONCLUSIONES:\n{datos['conclusiones']}"

# --- 4. DIÁLOGO PANTALLA COMPLETA ---
@st.dialog("Edición Detallada (Pantalla Completa)", width="large")
def ventana_completa():
    st.session_state.texto_ia_obs = st.text_area("Edite el reporte detallado:", value=st.session_state.texto_ia_obs, height=600)
    if st.button("Guardar Cambios"):
        st.rerun()

# --- 5. INTERFAZ ---
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

f_rev_fisica = st.text_area("1. Revisión Física", value=f"Se observa el artículo {f_prod} con señales de uso normal.")
f_rev_electro = st.text_area("2. Revisión electro-electrónica-mecanica", value="Se procede a revisar el sistema de alimentación y componentes mecánicos.")

# --- BLOQUE IA Y OBSERVACIONES (ESTRUCTURADO) ---
st.markdown("---")
st.markdown("### 🤖 Asistente de Observaciones Estructuradas")
falla_breve = st.text_input("Describe la falla o procedimiento para la IA:")

c_ia, c_fs = st.columns(2)
with c_ia:
    if st.button("✨ Generar con Estructura Groq", use_container_width=True):
        try:
            client = Groq(api_key=st.secrets["GROQ_API_KEY"]) 
            prompt_sistema = """Eres un perito técnico experto. Redacta reportes siguiendo estrictamente este formato:
            Procedimiento de inspección: (Pasos realizados)
            Resultados: (Hallazgos técnicos)
            Conclusión: (Determinación final del origen del daño)
            Recomendaciones: (Consejos de uso para el cliente)
            Usa un tono profesional e imparcial."""

            chat = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Falla: {falla_breve}"}
                ],
                model="llama-3.3-70b-versatile",
            )
            st.session_state.texto_ia_obs = chat.choices[0].message.content
            st.rerun()
        except: st.error("Error con la IA. Revisa tu API Key.")

with c_fs:
    if st.button("📺 Pantalla Completa", use_container_width=True):
        ventana_completa()

st.markdown("#### 3. Detalle de Observaciones")
f_obs = st.text_area("Edición rápida:", value=st.session_state.texto_ia_obs, height=250)
f_concl = st.text_area("4. Conclusiones", value=TEXTOS_CONCLUSIONES.get(tipo_rep, ""), height=150)

# --- 6. SECCIÓN DE IMÁGENES ---
st.markdown("---")
st.subheader("📸 Evidencia Fotográfica")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        if not any(img['name'] == file.name for img in st.session_state.imagenes_guardadas):
            st.session_state.imagenes_guardadas.append({
                "id": f"{file.name}_{len(st.session_state.imagenes_guardadas)}", 
                "name": file.name, "bytes": file.getvalue(), "desc": "Evidencia técnica."
            })

if st.session_state.imagenes_guardadas:
    for idx, img_data in enumerate(st.session_state.imagenes_guardadas):
        col_img, col_desc, col_del = st.columns([1, 3, 0.5])
        with col_img: st.image(img_data["bytes"], use_container_width=True)
        with col_desc:
            st.session_state.imagenes_guardadas[idx]["desc"] = st.text_input(
                f"Descripción {idx+1}", value=img_data["desc"], key=f"desc_{img_data['id']}"
            )
        with col_del:
            if st.button("🗑️", key=f"del_{img_data['id']}"):
                st.session_state.imagenes_guardadas.pop(idx)
                st.rerun()

# --- 7. GENERACIÓN Y DESCARGA ---
st.markdown("---")
if st.button("💾 GENERAR ARCHIVOS FINALIZADOS", use_container_width=True):
    lista_imgs_final = [{"imagen": BytesIO(i["bytes"]), "descripcion": i["desc"]} for i in st.session_state.imagenes_guardadas]
    datos = {
        "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
        "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador,
        "fecha_hoy": date.today(), "rev_fisica": f_rev_fisica, "rev_electro": f_rev_electro, 
        "observaciones": f_obs, "conclusiones": f_concl
    }
    st.session_state.pdf_data = generar_pdf(datos, lista_imgs_final)
    st.session_state.txt_data = generar_txt_contenido(datos)
    st.success("✅ PDF y TXT listos.")

if st.session_state.pdf_data or st.session_state.txt_data:
    cd1, cd2 = st.columns(2)
    with cd1:
        if st.session_state.pdf_data: st.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Informe_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
    with cd2:
        if st.session_state.txt_data: st.download_button("📄 Descargar TXT", data=st.session_state.txt_data, file_name=f"Resumen_{orden_id}.txt", mime="text/plain", use_container_width=True)
