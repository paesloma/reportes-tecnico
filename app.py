import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# 1. IMPORTACIONES FUNDAMENTALES PARA PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch  # SOLUCIÓN AL NAMEERROR

# 2. CONFIGURACIÓN DE SEGURIDAD
try:
    # IMPORTANTE: Debes generar una nueva API KEY en Groq ya que la anterior fue revocada
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 Error: La API Key no es válida o fue revocada. Configure una nueva en los Secrets.")
    st.stop()

# 3. LISTAS DE PERSONAL
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# 4. INICIALIZACIÓN DE ESTADOS (SOLUCIÓN AL KEYERROR)
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev_fisica": "", "rev_tec": "", "obs": "", "concl": ""}
if 'fotos' not in st.session_state:
    st.session_state.fotos = []
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# 5. CARGA DE BASE DE DATOS
@st.cache_data
def load_db():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except Exception: return pd.DataFrame()
    return pd.DataFrame()

df_db = load_db()

# 6. INTERFAZ Y DISEÑO VISUAL
st.title("🚀 Gestión de Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")

# Variables de autocompletado
c_v, s_v, p_v, f_v, ff_v, rf_v = "", "", "", "", str(date.today()), ""

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min','')
        ff_v = row.get('Fec_Fac_Min', str(date.today()))
        rf_v = "Ingresa a servicio técnico. Se observa el uso continuo del artículo."

st.subheader("Datos del Reporte")
col1, col2 = st.columns(2)

with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Producto", value=p_v)

with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)
    f_factura = st.text_input("Factura", value=f_v)
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v)
    f_serie = st.text_input("Serie/Artículo", value=s_v)

# 7. SECCIONES DE DIAGNÓSTICO E IA
st.divider()

# Solución para el llenado de Revisión Física
f_rev_fisica = st.text_area("1. Revisión Física", value=st.session_state.ia_data["rev_fisica"] if st.session_state.ia_data["rev_fisica"] else rf_v)
st.session_state.ia_data["rev_fisica"] = f_rev_fisica

f_diag_ia = st.text_area("🔧 Diagnóstico de Entrada (Para IA)", placeholder="Ej: No enciende, falla en tarjeta principal...")

if st.button("🤖 Generar Diagnóstico con IA"):
    if f_diag_ia:
        with st.spinner("Procesando con IA..."):
            prompt = (f"Producto: {f_prod}. Falla: {f_diag_ia}. Tipo: {f_tipo}. "
                      "Genera: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos ni formato markdown.")
            try:
                resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                clean = resp.choices[0].message.content.strip()
                if "REVISION_TEC:" in clean:
                    st.session_state.ia_data["rev_tec"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                    st.session_state.ia_data["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                    st.session_state.ia_data["concl"] = clean.split("CONCLUSIONES:")[1].strip()
                st.rerun()
            except Exception:
                st.error("Error de conexión con la IA. Verifique su API Key.")

# Bloques con persistencia de datos
f_final_rev = st.text_area("2. Revisión Técnica", value=st.session_state.ia_data["rev_tec"])
f_final_obs = st.text_area("3. Observaciones", value=st.session_state.ia_data["obs"])
f_final_con = st.text_area("4. Conclusiones", value=st.session_state.ia_data["concl"])

# 8. EVIDENCIA FOTOGRÁFICA
st.divider()
st.subheader("🖼️ Evidencia Fotográfica")
subida = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if subida:
    for f in subida:
        if f.name not in [x['name'] for x in st.session_state.fotos]:
            st.session_state.fotos.append({"name": f.name, "data": f.getvalue(), "pie": "Evidencia técnica."})

if st.session_state.fotos:
    cols = st.columns(3)
    for i, foto in enumerate(st.session_state.fotos):
        with cols[i % 3]:
            st.image(foto['data'], use_container_width=True)
            st.session_state.fotos[i]['pie'] = st.text_input(f"Pie {i+1}", value=foto['pie'], key=f"p_{i}")
            if st.button(f"Borrar {i+1}", key=f"d_{i}"):
                st.session_state.fotos.pop(i)
                st.session_state.uploader_key += 1
                st.rerun()

# 9. GENERACIÓN DE PDF PROFESIONAL SIN ERRORES
def generar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"INFORME TÉCNICO: {f_tipo}", styles['Title']),
        Paragraph(f"Orden: {orden_id} | Factura: {f_factura} | Fecha: {f_fec_fac}", styles['Normal']),
        Paragraph(f"Producto: {f_prod} | Serie: {f_serie}", styles['Normal']),
        Spacer(1, 12)
    ]
    
    # Tabla técnica con anchos correctos usando inch
    data = [
        ["1. REVISIÓN FÍSICA", Paragraph(f_rev_fisica, styles['Normal'])],
        ["2. REVISIÓN TÉCNICA", Paragraph(f_final_rev, styles['Normal'])],
        ["3. OBSERVACIONES", Paragraph(f_final_obs, styles['Normal'])],
        ["4. CONCLUSIONES", Paragraph(f_final_con, styles['Normal'])]
    ]
    
    t = Table(data, colWidths=[1.6*inch, 5.4*inch])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (0,-1), colors.lightgrey)
    ]))
    elements.append(t)
    
    # Inserción de imágenes en el PDF
    if st.session_state.fotos:
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("EVIDENCIA FOTOGRÁFICA", styles['Heading3']))
        for f in st.session_state.fotos:
            img = RLImage(BytesIO(f['data']), width=3.5*inch, height=2.5*inch, kind='proportional')
            elements.append(img)
            elements.append(Paragraph(f['pie'], styles['Italic']))
            elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# 10. BOTÓN DE DESCARGA FINAL
if st.session_state.ia_data["concl"]:
    st.divider()
    st.download_button(
        label="📥 Descargar Reporte Final (PDF)",
        data=generar_pdf(),
        file_name=f"Reporte_{orden_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
