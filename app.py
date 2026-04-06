import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- 1. SEGURIDAD Y CONFIGURACIÓN ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure la API Key en los Secrets de Streamlit.")
    st.stop()

# Listados completos de personal nacional
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 2. ESTADO DE SESIÓN ---
if 'ia_fields' not in st.session_state:
    st.session_state.ia_fields = {"rev": "", "obs": "", "con": ""}

# --- 3. CARGA DE DATOS ---
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

# --- 4. INTERFAZ ---
st.title("🔧 Generador de Reportes Profesionales")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v, ff_v = row.get('Cliente',''), row.get('Serie',''), row.get('Producto',''), row.get('Fac_Min',''), row.get('Fec_Fac_Min', ff_v)

st.subheader("📋 Datos del Servicio")
col1, col2 = st.columns(2)
with col1:
    f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
with col2:
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v) # Campo solicitado
    f_prod = st.text_input("Producto", value=p_v)
    f_tecnico = st.selectbox("Revisado por (Técnico)", LISTA_TECNICOS)

f_daño = st.text_area("🔧 Diagnóstico de Entrada (IA)")

# --- 5. LÓGICA DE IA DINÁMICA ---
if st.button("🤖 Generar Diagnóstico"):
    if f_daño:
        with st.spinner(f"Analizando para informe tipo: {f_tipo}..."):
            # Ajuste de conclusiones según tipo de informe
            if f_tipo == "RECLAMO AL PROVEEDOR":
                meta = "Centrarse en falla de origen para garantía."
            elif f_tipo == "FUERA DE GARANTIA":
                meta = "Centrarse en daño por uso o causas externas."
            else:
                meta = "Resumen técnico general."

            prompt = (f"Producto: {f_prod}. Falla: {f_daño}. Tipo: {f_tipo}. Objetivo: {meta}. "
                      "Estructura: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos.")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean:
                st.session_state.ia_fields["rev"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ia_fields["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ia_fields["con"] = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Edición de campos generados
f_rev_tec = st.text_area("2. Revisión Técnica", value=st.session_state.ia_fields["rev"])
f_obs = st.text_area("3. Observaciones", value=st.session_state.ia_fields["obs"])
f_concl = st.text_area("4. Conclusiones", value=st.session_state.ia_fields["con"]) #

# --- 6. GENERACIÓN Y DESCARGA DE PDF ---
def generar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Encabezado
    elements.append(Paragraph(f"REPORTE TÉCNICO - {f_tipo}", styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Tabla de Datos
    datos = [
        ["Orden:", orden_id, "Fecha Factura:", f_fec_fac],
        ["Cliente:", f_cliente, "Producto:", f_prod]
    ]
    t = Table(datos, colWidths=[1*inch, 2*inch, 1.2*inch, 2*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # Secciones
    elements.append(Paragraph("REVISIÓN TÉCNICA:", styles['Heading3']))
    elements.append(Paragraph(f_rev_tec, styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("OBSERVACIONES:", styles['Heading3']))
    elements.append(Paragraph(f_obs, styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("CONCLUSIONES:", styles['Heading3']))
    elements.append(Paragraph(f_concl, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.session_state.ia_fields["con"]:
    pdf_file = generar_pdf()
    st.download_button(
        label="📥 Descargar Reporte en PDF",
        data=pdf_file,
        file_name=f"Reporte_{orden_id}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
