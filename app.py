import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
import os
from groq import Groq

# IMPORTACIONES CRÍTICAS PARA PDF Y ESTÉTICA
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch  # Solución al error

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

# --- 3. ESTADOS DE SESIÓN (Persistencia de datos) ---
if 'ia_data' not in st.session_state:
    st.session_state.ia_data = {"rev": "", "obs": "", "con": ""}
if 'fotos' not in st.session_state:
    st.session_state.fotos = []  # Lista para guardar {img_data, filename, pie}
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0  # Para resetear el uploader

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
st.title("🔧 Sistema de Reportes Técnicos con Evidencia")

# Selección de Tipo (Determina conclusiones)
f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)

# Búsqueda por Orden
orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", str(date.today())

if orden_id and not df_db.empty:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v = row.get('Cliente','')
        p_v = row.get('Producto','')
        f_v = row.get('Fac_Min','')
        ff_v = row.get('Fec_Fac_Min', str(date.today()))
        st.success(f"✅ Datos cargados: {c_v}")

st.subheader("📋 Datos del Servicio")
col1, col2 = st.columns(2)
with col1:
    f_cliente = st.text_input("Cliente", value=c_v)
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
with col2:
    f_fec_fac = st.text_input("Fecha Factura (YYYY/MM/DD)", value=ff_v) # Campo solicitado
    f_prod = st.text_input("Producto", value=p_v)
    f_tecnico = st.selectbox("Revisado por", LISTA_TECNICOS)

# 6. IA CON CONCLUSIONES DINÁMICAS
f_daño = st.text_area("🔧 Diagnóstico de Entrada (IA)")

if st.button("🤖 Generar Diagnóstico Técnico"):
    if f_daño:
        with st.spinner(f"Analizando para informe tipo: {f_tipo}..."):
            # Lógica según tipo de informe
            meta = "daño por mal uso" if f_tipo == "FUERA DE GARANTIA" else "falla de fábrica"
            prompt = (f"Producto: {f_prod}. Falla: {f_daño}. Informe: {f_tipo}. Objetivo: {meta}. "
                      "Estructura obligatoria: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos.")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean:
                st.session_state.ia_data["rev"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.ia_data["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.ia_data["con"] = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Edición de campos (Para que no salgan vacíos)
f_rev_tec = st.text_area("2. Revisión Técnica", value=st.session_state.ia_data["rev"])
f_obs = st.text_area("3. Observaciones", value=st.session_state.ia_data["obs"])
f_concl = st.text_area("4. Conclusiones", value=st.session_state.ia_data["con"])

# --- 7. GESTIÓN DE FOTOS ESTÉTICAS ---
st.divider()
st.subheader("🖼️ Evidencia Fotográfica (PDF)")

# Uploader que se resetea al borrar fotos
cargador_fotos = st.file_uploader("Subir imágenes de evidencia (JPG/PNG)", type=['jpg','png','jpeg'], accept_multiple_files=True, key=f"uploader_{st.session_state.uploader_key}")

# Guardar nuevas fotos en la sesión
if cargador_fotos:
    for f in cargador_fotos:
        # Evitar duplicados
        if f.name not in [x['filename'] for x in st.session_state.fotos]:
            img_bytes = f.getvalue()
            st.session_state.fotos.append({
                "data": img_bytes,
                "filename": f.name,
                "pie": "Evidencia técnica de falla detectada." # Pie por defecto
            })

# Vista preliminar estética (Miniaturas, Editar pie, Borrar)
if st.session_state.fotos:
    st.write("---")
    st.caption("Usa la X para borrar la foto o edita el texto para el PDF.")
    cols_foto = st.columns(3) # Miniaturas en filas de 3
    
    # Crear índice para borrar correctamente
    for i, foto in enumerate(st.session_state.fotos):
        with cols_foto[i % 3]:
            # Miniatura estética
            st.image(foto['data'], use_container_width=True, caption=foto['filename'])
            
            # Opciones de edición y borrado
            col_txt, col_del = st.columns([4, 1])
            # Cambiar texto
            new_pie = col_txt.text_input(f"Pie #{i+1}", value=foto['pie'], key=f"pie_{i}")
            st.session_state.fotos[i]["pie"] = new_pie
            # Borrar
            if col_del.button("❌", key=f"del_{i}"):
                st.session_state.fotos.pop(i)
                st.session_state.uploader_key += 1 # Resetear uploader
                st.rerun()

# --- 8. GENERACIÓN DE PDF SIN ERRORES (Usa inch) ---
def generar_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    # Estilo pie de foto
    pie_style = ParagraphStyle(name='Pie', parent=styles['Normal'], fontSize=9, italic=True, alignment=1)
    elements = []

    # Encabezado
    elements.append(Paragraph(f"INFORME TÉCNICO: {f_tipo}", styles['Title']))
    elements.append(Paragraph(f"Orden: {orden_id} | Fecha Factura: {f_fec_fac}", styles['Heading3']))
    elements.append(Paragraph(f"Cliente: {f_cliente} | Producto: {f_prod}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Tabla de Datos (Usa 'inch' correctamente aquí para evitar NameError)
    data = [
        ["Revisión Técnica:", f_rev_tec],
        ["Conclusiones:", f_concl]
    ]
    t = Table(data, colWidths=[1.5*inch, 5.5*inch])
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'TOP')]))
    elements.append(t)
    elements.append(Spacer(1, 24))
    
    # --- Incluir Fotos de forma estética ---
    if st.session_state.fotos:
        elements.append(Paragraph("EVIDENCIA FOTOGRÁFICA:", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        # Fotos de 2 en 2 para que queden estéticas y grandes
        foto_rows = [st.session_state.fotos[x:x+2] for x in range(0, len(st.session_state.fotos), 2)]
        
        for row in foto_rows:
            # Crear una tabla invisible para alinear las fotos
            table_row = []
            captions_row = []
            
            for foto in row:
                # Convertir bytes a RLImage de ReportLab
                img_io = BytesIO(foto['data'])
                img = RLImage(img_io)
                # Escalar para que quepan estéticamente
                w, h = img.wrap(0,0)
                aspect = h / w
                img.drawWidth = 3.2*inch
                img.drawHeight = 3.2*inch * aspect
                
                table_row.append(img)
                # Paragraph para el pie con estilo
                captions_row.append(Paragraph(foto['pie'], pie_style))
                
            # Si solo hay una foto en la última fila, rellenar para alineación
            if len(table_row) < 2:
                table_row.append("")
                captions_row.append("")
                
            # Tabla para fotos
            t_fotos = Table([table_row], colWidths=[3.5*inch, 3.5*inch])
            t_fotos.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            elements.append(t_fotos)
            
            # Tabla para pies de foto
            t_captions = Table([captions_row], colWidths=[3.5*inch, 3.5*inch])
            t_captions.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
            elements.append(t_captions)
            elements.append(Spacer(1, 15))
    
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(f"Realizado por: {f_realizador} | Revisado por: {f_tecnico}", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- 9. DESCARGA FINAL SIN RECARGAS (Rendimiento) ---
if st.session_state.ia_data["con"]:
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        # Generamos el PDF una sola vez al preparar la descarga
        st.download_button(
            label="📥 Descargar Reporte Completo (PDF)",
            data=generar_pdf(),
            file_name=f"Reporte_{orden_id}_{f_tipo.replace(' ','_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col_b:
        st.success(f"Reporte con {len(st.session_state.fotos)} fotos listo.")
