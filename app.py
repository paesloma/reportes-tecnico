import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# IMPORTACIONES PARA PDF Y DISEÑO ESTÉTICO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch 

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 Error de Autenticación: Verifica tu API Key en los Secrets de Streamlit.")
    st.stop()

# --- 2. PERSONAL Y OPCIONES NACIONALES ---
LISTA_TECNICOS = [
    "Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", 
    "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", 
    "Tec. Juan Farez", "Tec. Santiago Farez"
]

LISTA_REALIZADORES = [
    "Ing. Henry Beltran", "Ing. Pablo Lopez", 
    "Ing. Christian Calle", "Ing. Guillermo Ortiz"
]

OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. ESTADOS DE SESIÓN (Persistencia para evitar pérdida de datos) ---
if 'ia_fields' not in st.session_state:
    st.session_state.ia_fields = {"rev": "", "obs": "", "con": ""}
if 'evidencia_fotos' not in st.session_state:
    st.session_state.evidencia_fotos = [] 
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- 4. CARGA DE BASE DE DATOS (CSV) ---
@st.cache_data
def cargar_base():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={
                'Serie/Artículo': 'Serie', 
                'Fec. Fac. Min': 'Fec_Fac_Min', 
                'Fac. Min': 'Fac_Min'
            })
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = cargar_base()

# --- 5. INTERFAZ DE USUARIO ---
st.title("🔧 Gestión de Reportes Post-Venta")

# Búsqueda por Orden
orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v, ff_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min',''), row.get('Fec_Fac_Min', ff_v)
        st.success(f"✅ Datos cargados para: {c_v}")

st.subheader("📋 Información del Reporte")
col1, col2 = st.columns(2)

with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)

with col2:
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v) #
    f_prod = st.text_input("Producto", value=p_v)
    f_tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)

# --- 6. PROCESAMIENTO CON IA (CONCLUSIONES DINÁMICAS) ---
st.divider()
f_daño = st.text_area("✍️ Diagnóstico de Entrada (Falla reportada)")

if st.button("🤖 Generar Informe con IA"):
    if f_daño:
        with st.spinner(f"Redactando dictamen para {f_tipo}..."):
            # Ajuste de tono según el tipo de informe
            enfoque = "falla de fabricación" if f_tipo == "RECLAMO AL PROVEEDOR" else "daño por causas externas o mal uso"
            
            prompt = (f"Actúa como técnico senior. Producto: {f_prod}. Falla: {f_daño}. "
                      f"Tipo de reporte: {f_tipo}. Objetivo: Enfatizar {enfoque}. "
                      "Estructura: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos.")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean_text = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean_text:
                st.session_state.ia_fields["rev"] = clean_text.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ia_fields["obs"] = clean_text.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ia_fields["con"] = clean_text.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Campos editables (Evita cuadros vacíos en el PDF)
f_rev_tec = st.text_area("2. Revisión Técnica", value=st.session_state.ia_fields["rev"], height=150)
f_obs = st.text_area("3. Observaciones", value=st.session_state.ia_fields["obs"], height=100)
f_concl = st.text_area("4. Conclusiones", value=st.session_state.ia_fields["con"], height=100)

# --- 7. GESTIÓN DE EVIDENCIA FOTOGRÁFICA ---
st.divider()
st.subheader("📸 Evidencia Fotográfica")

subida = st.file_uploader("Cargar fotos (JPG/PNG)", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if subida:
    for f in subida:
        if f.name not in [x['name'] for x in st.session_state.evidencia_fotos]:
            st.session_state.evidencia_fotos.append({
                "name": f.name,
                "data": f.getvalue(),
                "caption": "Vista de la falla detectada."
            })

if st.session_state.evidencia_fotos:
    st.write("---")
    cols = st.columns(3)
    for i, foto in enumerate(st.session_state.evidencia_fotos):
        with cols[i % 3]:
            st.image(foto['data'], use_container_width=True)
            new_cap = st.text_input(f"Pie de foto {i+1}", value=foto['caption'], key=f"cap_{i}")
            st.session_state.evidencia_fotos[i]['caption'] = new_cap
            if st.button(f"Eliminar Foto {i+1}", key=f"del_{i}"):
                st.session_state.evidencia_fotos.pop(i)
                st.session_state.uploader_key += 1
                st.rerun()

# --- 8. GENERACIÓN DE PDF Y BOTONES DE DESCARGA ---
def crear_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = []

    # Título y Encabezado
    elements.append(Paragraph(f"INFORME TÉCNICO: {f_tipo}", styles['Title']))
    elements.append(Paragraph(f"Orden: {orden_id} | Fecha Factura: {f_fec_fac}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Tabla de Contenido Técnico
    data_table = [
        ["REVISIÓN TÉCNICA", Paragraph(f_rev_tec, styles['Normal'])],
        ["OBSERVACIONES", Paragraph(f_obs, styles['Normal'])],
        ["CONCLUSIONES", Paragraph(f_concl, styles['Normal'])]
    ]
    # Uso correcto de inch para evitar NameError
    t = Table(data_table, colWidths=[1.5*inch, 5.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('VALIGN',(0,0),(-1,-1),'TOP')]))
    elements.append(t)
    
    # Fotos en el PDF (Estética de 2 por fila)
    if st.session_state.evidencia_fotos:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("EVIDENCIA FOTOGRÁFICA", styles['Heading3']))
        
        filas = [st.session_state.evidencia_fotos[i:i+2] for i in range(0, len(st.session_state.evidencia_fotos), 2)]
        for fila in filas:
            imgs, caps = [], []
            for item in fila:
                img_io = BytesIO(item['data'])
                img_rl = RLImage(img_io, width=3*inch, height=2.5*inch, kind='proportional')
                imgs.append(img_rl)
                caps.append(Paragraph(item['caption'], styles['Italic']))
            
            if len(imgs) == 1:
                imgs.append(""); caps.append("")
                
            elements.append(Table([imgs, caps], colWidths=[3.5*inch, 3.5*inch]))
            elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer

st.divider()
if st.session_state.ia_fields["con"]:
    st.download_button(
        label="📥 Descargar Reporte Completo (PDF)",
        data=crear_pdf(),
        file_name=f"Reporte_{orden_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("💡 Genera el diagnóstico con la IA para habilitar la descarga.")
