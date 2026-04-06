import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os
from groq import Groq

# ReportLab para diseño profesional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes Pro", page_icon="🔧", layout="centered")

if 'fotos_lista' not in st.session_state:
    st.session_state.fotos_lista = []
if 'ia_obs_limpia' not in st.session_state:
    st.session_state.ia_obs_limpia = ""
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'txt_data' not in st.session_state:
    st.session_state.txt_data = None

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure 'GROQ_API_KEY' en los Secrets.")
    st.stop()

# --- 2. CARGA DE DATOS ---
@st.cache_data
def cargar_datos_servicios():
    if os.path.exists("servicios.csv"):
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv("servicios.csv", dtype=str, encoding=enc, sep=None, engine='python')
                df.columns = df.columns.str.strip()
                return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
            except: continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()

LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez ", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos, lamentamos indicarle que el daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos indicamos que el equipo funciona correctamente en base a lo que indica el fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nSe concluye que el daño es de fábrica debido a las características presentadas. Solicitamos su colaboración con el reclamo pertinente al proveedor."
}

# --- 3. FUNCIONES DE GENERACIÓN ---
def generar_pdf_pro(datos, fotos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.6*inch, rightMargin=0.6*inch)
    azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=17, alignment=TA_CENTER, fontName='Helvetica-Bold', textColor=azul, spaceAfter=20)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=azul, borderPadding=4, spaceBefore=15, spaceAfter=10)
    est_par = ParagraphStyle('P', fontSize=9, leading=13, alignment=TA_JUSTIFY)
    
    story = []
    if os.path.exists("logo.png"):
        story.append(Image("logo.png", width=1.5*inch, height=0.6*inch))
    
    story.append(Paragraph("INFORME TÉCNICO DE SERVICIO", est_titulo))
    
    info_tbl = [[f"Orden: {datos['orden']}", f"Factura: {datos['factura']}"],
                [f"Cliente: {datos['cliente']}", f"Producto: {datos['producto']}"]]
    t = Table(info_tbl, colWidths=[3.4*inch, 3.4*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)

    for tit, cont in [("1. REVISIÓN FÍSICA", datos['rf']), ("2. INGRESO A SERVICIO", datos['it']), 
                      ("3. REVISIÓN ELECTROMECÁNICA", datos['re']), ("4. OBSERVACIONES", datos['obs']), 
                      ("5. CONCLUSIONES", datos['con'])]:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_par))

    if fotos:
        story.append(Paragraph("EVIDENCIA FOTOGRÁFICA", est_sec))
        for idx, f in enumerate(fotos):
            img = Image(BytesIO(f['file']), width=2.5*inch, height=1.8*inch)
            t_foto = Table([[img, Paragraph(f"<b>Imagen #{idx+1}:</b><br/>{f['desc']}", est_par)]], colWidths=[2.7*inch, 4.1*inch])
            t_foto.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (1,0), (1,0), 12)]))
            story.append(t_foto)
            story.append(Spacer(1, 15))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()

def generar_txt_correo(datos):
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", ""] else datos['factura']
    return (
        f"Estimados\n\n"
        f"Me dirijo a usted para indicar el status de estado de la garantía del siguiente producto:\n\n"
        f"CLIENTE: {datos['cliente']}\n"
        f"FACTURA: {fac_txt}\n"
        f"ORDEN DE SERVICIO: {datos['orden']}\n"
        f"PRODUCTO: {datos['producto']}\n"
        f"TÉCNICO: {datos['tecnico']}\n\n"
        f"TIPO DE REPORTE: {datos['tipo']}\n\n"
        f"CONCLUSIONES:\n{datos['con']}\n\n"
        f"Atentamente,\n{datos['realizador']}\nCoordinador Postventa"
    )

# --- 4. INTERFAZ ---
st.title("🔧 Generador de Reportes de Calidad")
orden_id = st.text_input("Número de Orden")

# Autocompletado (Mantenido)
c_v, p_v, f_v = "", "", ""
if orden_id:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        c_v, p_v, f_v = res.iloc[0]['Cliente'], res.iloc[0]['Producto'], res.iloc[0]['Fac_Min']

col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_prod = st.text_input("Producto", value=p_v)
    f_fac = st.text_input("Factura", value=f_v)

f_rf = st.text_area("1. Revisión Física", value=f"Se recibe {f_prod}. Se observa uso continuo.")
f_it = st.text_area("2. Ingresa a servicio técnico")
f_re = st.text_area("3. Revisión electro-mecánica", value="Revisión de voltajes y componentes.")

# IA: OBSERVACIONES LIMPIAS
st.markdown("---")
p_ia = st.text_area("🤖 Describa la falla para la IA (Solo generará Observaciones)")
if st.button("🪄 Redactar Observaciones"):
    if p_ia:
        with st.spinner("Redactando texto limpio..."):
            resp = client.chat.completions.create(
                messages=[{"role": "system", "content": "Eres un técnico. Redacta solo las observaciones, sin comillas, ni asteriscos, ni títulos. Texto plano profesional."},
                          {"role": "user", "content": f"Falla: {p_ia}. Producto: {f_prod}"}],
                model="llama-3.3-70b-versatile"
            ).choices[0].message.content
            st.session_state.ia_obs_limpia = resp.replace('"', '').strip()
            st.rerun()

f_obs = st.text_area("4. Observaciones", value=st.session_state.ia_obs_limpia, height=150)
f_con = st.text_area("5. Conclusiones", value=TEXTOS_CONCLUSIONES.get(tipo_rep, ""))

# FOTOS CON ACCIONES
st.subheader("📸 Evidencia Fotográfica")
up = st.file_uploader("Subir Fotos", type=['jpg','png','jpeg'], accept_multiple_files=True)
if up:
    for f in up:
        if not any(x['name'] == f.name for x in st.session_state.fotos_lista):
            st.session_state.fotos_lista.append({'file': f.read(), 'name': f.name, 'desc': "Evidencia técnica."})

for i, foto in enumerate(st.session_state.fotos_lista):
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1: st.image(foto['file'], width=100)
    with c2: st.session_state.fotos_lista[i]['desc'] = st.text_input(f"Nota {i+1}", value=foto['desc'], key=f"d_{i}")
    with c3:
        st.download_button("📥", data=foto['file'], file_name=foto['name'], key=f"dl_{i}")
        if st.button("🗑️", key=f"del_{i}"):
            st.session_state.fotos_lista.pop(i)
            st.rerun()

# --- GENERACIÓN ---
if st.button("💾 GENERAR ARCHIVOS (PDF Y TXT)", use_container_width=True):
    payload = {"orden": orden_id, "cliente": f_cliente, "factura": f_fac, "producto": f_prod, "rf": f_rf, "it": f_it, "re": f_re, "obs": f_obs, "con": f_con, "tecnico": f_tecnico, "realizador": f_realizador, "tipo": tipo_rep}
    st.session_state.pdf_data = generar_pdf_pro(payload, st.session_state.fotos_lista)
    st.session_state.txt_data = generar_txt_correo(payload)
    st.success("✅ Archivos listos")

if st.session_state.pdf_data:
    c_pdf, c_txt = st.columns(2)
    with c_pdf: st.download_button("📥 Descargar PDF", data=st.session_state.pdf_data, file_name=f"Informe_{orden_id}.pdf", use_container_width=True)
    with c_txt: st.download_button("📥 Descargar TXT (Correo)", data=st.session_state.txt_data, file_name=f"Correo_{orden_id}.txt", use_container_width=True)
