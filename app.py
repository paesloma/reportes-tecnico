import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# IMPORTACIONES PARA PDF Y DISEÑO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch # Solución al error NameError

# --- 1. SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure la API Key en los Secrets de Streamlit.")
    st.stop()

# --- 2. PERSONAL NACIONAL ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. ESTADOS DE SESIÓN (Persistencia) ---
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev": "", "obs": "", "con": ""}
if 'fotos' not in st.session_state:
    st.session_state.fotos = []
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

# --- 4. CARGA DE DATOS ---
@st.cache_data
def load_db():
    if os.path.exists("servicios.csv"):
        try:
            df = pd.read_csv("servicios.csv", dtype=str, encoding='latin-1')
            df.columns = df.columns.str.strip()
            return df.rename(columns={'Serie/Artículo': 'Serie', 'Fec. Fac. Min': 'Fec_Fac_Min', 'Fac. Min': 'Fac_Min'})
        except: return pd.DataFrame()
    return pd.DataFrame()

df_db = load_db()

# --- 5. INTERFAZ ---
st.title("🔧 Generador de Reportes Post-Venta")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, p_v, ff_v = row.get('Cliente',''), row.get('Producto',''), row.get('Fec_Fac_Min', str(date.today()))

col1, col2 = st.columns(2)
with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
with col2:
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v) #
    f_prod = st.text_input("Producto", value=p_v)
    f_tecnico = st.selectbox("Revisado por", LISTA_TECNICOS)

# 6. IA CON CONCLUSIONES DINÁMICAS
f_daño = st.text_area("🔧 Diagnóstico de Entrada")

if st.button("🤖 Generar Diagnóstico con IA"):
    if f_daño:
        with st.spinner(f"Analizando para {f_tipo}..."):
            objetivo = "falla de origen" if f_tipo == "RECLAMO AL PROVEEDOR" else "daño externo/mal uso"
            prompt = (f"Producto: {f_prod}. Falla: {f_daño}. Tipo: {f_tipo}. Objetivo: {objetivo}. "
                      "Divide en: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos.")
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            if "REVISION_TEC:" in clean:
                st.session_state.ia_data["rev"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ia_data["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ia_data["con"] = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Campos Editables
f_rev_tec = st.text_area("2. Revisión Técnica", value=st.session_state.ia_data["rev"])
f_obs = st.text_area("3. Observaciones", value=st.session_state.ia_data["obs"])
f_concl = st.text_area("4. Conclusiones", value=st.session_state.ia_data["con"])

# --- 7. GESTIÓN DE FOTOS ---
st.divider()
st.subheader("🖼️ Evidencia Fotográfica")
subida = st.file_uploader("Subir fotos", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")

if subida:
    for f in subida:
        if f.name not in [x['name'] for x in st.session_state.fotos]:
            st.session_state.fotos.append({"name": f.name, "data": f.getvalue(), "pie": "Evidencia de falla."})

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

# --- 8. DESCARGAS ---
def generar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"INFORME: {f_tipo}", styles['Title']), Paragraph(f"Orden: {orden_id} | Factura: {f_fec_fac}", styles['Normal']), Spacer(1, 12)]
    
    t = Table([["REVISIÓN", Paragraph(f_rev_tec, styles['Normal'])], ["CONCLUSIÓN", Paragraph(f_concl, styles['Normal'])]], colWidths=[1.5*inch, 5.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t)
    
    if st.session_state.fotos:
        elements.append(Spacer(1, 20))
        for foto in st.session_state.fotos:
            img = RLImage(BytesIO(foto['data']), width=3*inch, height=2.5*inch, kind='proportional')
            elements.append(img); elements.append(Paragraph(foto['pie'], styles['Italic'])); elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.session_state.ia_data["con"]:
    st.download_button("📥 Descargar PDF", data=generar_pdf(), file_name=f"Reporte_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
