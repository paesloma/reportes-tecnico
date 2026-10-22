import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO
from PIL import Image as PilImage
import os

# Importaciones de ReportLab (PDF)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="Generador de Reportes", page_icon="🔧", layout="wide")

# Inicialización de estados
claves_estado = ['pdf_es', 'txt_es']
for key in claves_estado:
    if key not in st.session_state:
        st.session_state[key] = None

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
            except:
                continue
    return pd.DataFrame(columns=['Orden', 'Cliente', 'Serie', 'Producto', 'Fec_Fac_Min', 'Fac_Min'])

df_db = cargar_datos_servicios()

# --- CONSTANTES ---
LISTA_TECNICOS = [
    "Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango",
    "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera",
    "Tec. Juan Farez", "Tec. Santiago Farez", "Tec.Ronald Paladinez", "Tec. Saul Vite",
    "Tec. Miguel Meza", "Tec German Tenemaza", "CISTRONIC", "Taller Externo","Tec. Jorge Pintado"
]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz", "Ing. Adrian Aguilar", "Ing. John Juela"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

TEXTOS_CONCLUSIONES = {
    "FUERA DE GARANTIA": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nEl daño identificado no es atribuible a defectos de fabricación o materiales, sino al uso indebido del equipo, lo cual invalida la cobertura de garantía.",
    "INFORME TECNICO": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nCon base en estos hallazgos se informa que el equipo funciona correctamente en base a las indicaciones de operacion del fabricante",
    "RECLAMO AL PROVEEDOR": "En marco de las políticas de garantía que mantienen un orden en el proceso se concluye:\nEl daño presentado corresponde a un defecto de manufactura debido al diagnostico realizado. Solicitamos su colaboración con el proceso de Reclamo al Proveedor."
}

# Plantillas de Observaciones
PLANTILLAS_OBSERVACIONES = {
    "Personalizado (Por defecto)": "Luego de la revisión del artículo se observa lo siguiente: ",
    "Negación - Humedad interna (Tarjetas)": "Luego de la revisión del artículo se observa lo siguiente: la presencia de humedad interna en las tarjetas o componentes electrónicos. La acumulación de líquido o sulfatación en el sistema altera su funcionamiento y anula la garantía de forma inmediata, al tratarse de una afectación por agentes externos.",
    "Negación - Humedad en panel (Pantalla)": "Luego de la revisión del artículo se observa lo siguiente: la presencia de humedad interna en el panel de visualización (pantalla). La filtración o condensación de líquido entre las capas del display genera manchas permanentes y cortocircuitos internos, condición provocada por factores ambientales o manipulación externa no cubierta por la garantía.",
    "Negación - Ingreso de insectos": "Luego de la revisión del artículo se observa lo siguiente: el ingreso de insectos al interior del chasis. La acumulación de plagas o residuos biológicos sobre los circuitos electrónicos provoca cortocircuitos y fallas severas, lo cual constituye un factor externo excluido de la garantía del fabricante.",
    "Negación - Golpe o rotura de pantalla": "Luego de la revisión del artículo se observa lo siguiente: un golpe o rotura en la pantalla. Al presentar un impacto físico visible o fisura interna en el panel de visualización, la avería se clasifica como daño accidental o manipulación inadecuada, quedando fuera de la cobertura de garantía.",
    "Negación - Problemas eléctricos (Variaciones)": "Luego de la revisión del artículo se observa lo siguiente: una falla por problemas eléctricos derivados de una conexión ineficiente (variaciones severas de voltaje, tomacorrientes defectuosos o falta de puesta a tierra). La garantía cubre únicamente defectos de fábrica, por lo que los daños ocasionados por sobretensiones o anomalías en la red eléctrica externa no aplican para reparación sin costo."
}

if "obs_text" not in st.session_state:
    st.session_state.obs_text = PLANTILLAS_OBSERVACIONES["Personalizado (Por defecto)"]

def actualizar_observacion():
    seleccion = st.session_state.sel_plantilla_obs
    st.session_state.obs_text = PLANTILLAS_OBSERVACIONES[seleccion]

# Títulos y etiquetas dinámicas según el tipo de reporte seleccionado
def obtener_titulos_por_tipo(tipo_rep):
    tipo_upper = tipo_rep.upper()
    if "GARANTIA" in tipo_upper:
        return "INFORME FUERA DE GARANTIA"
    elif "TECNICO" in tipo_upper:
        return "INFORME TECNICO"
    elif "PROVEEDOR" in tipo_upper:
        return "RECLAMO AL PROVEEDOR"
    return tipo_rep

LBL = {
    "orden": "Orden", "fac": "Factura", "cliente": "Cliente",
    "fec_fac": "Fecha factura", "prod": "Articulo", "serie": "Serie", "realizador": "Realizado por",
    "fec_rep": "Fecha reclamo", "revisador": "Revisado por", "evidencia": "EVIDENCIA DE IMÁGENES",
    "figura": "Figura", "marca": "Marca", "modelo": "Modelo", "repuesto": "Repuesto",
    "codigo": "Código", "cantidad": "Cantidad", "reporte": "Reporte"
}

# --- 3. FUNCIONES DE GENERACIÓN ---
def agregar_marca_agua(canvas, doc):
    watermark_file = "watermark.png"
    if os.path.exists(watermark_file):
        try:
            canvas.saveState()
            canvas.setFillAlpha(0.12)
            canvas.drawImage(watermark_file, 0, 0, width=canvas._pagesize[0], height=canvas._pagesize[1], mask='auto', preserveAspectRatio=True, anchor='c')
            canvas.restoreState()
        except:
            pass

def generar_pdf(datos, secciones_activas, lista_imgs):
    l = LBL
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.5*inch, rightMargin=0.5*inch)
    color_azul = colors.HexColor("#0056b3")
    
    est_titulo = ParagraphStyle('T', fontSize=16, alignment=1, fontName='Helvetica-Bold', textColor=color_azul)
    est_sec = ParagraphStyle('S', fontSize=10, fontName='Helvetica-Bold', textColor=colors.white, backColor=color_azul, borderPadding=2, spaceBefore=8)
    est_txt = ParagraphStyle('TXT', fontSize=9, fontName='Helvetica', leading=11)
    est_firma = ParagraphStyle('F', fontSize=10, fontName='Helvetica-Bold', alignment=1)
    est_fig = ParagraphStyle('FIG', fontSize=10, fontName='Helvetica-Bold', alignment=1, spaceBefore=4)
    
    story = []

    # Cabecera (Logos)
    logo_izq_path, logo_der_path = "logo.png", "logo_derecho.png"
    col_izq, col_der = [], []
    if os.path.exists(logo_izq_path): col_izq.append(RLImage(logo_izq_path, width=1.4*inch, height=0.55*inch))
    if os.path.exists(logo_der_path):
        img_der = RLImage(logo_der_path, width=1.4*inch, height=0.55*inch)
        img_der.hAlign = 'RIGHT'
        col_der.append(img_der)

    if col_izq or col_der:
        header_table = Table([[col_izq, col_der]], colWidths=[3.7*inch, 3.7*inch])
        header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
        story.append(header_table)
    
    story.append(Spacer(1, 10))
    
    # Título dinámico basado en la opción seleccionada
    titulo_principal = obtener_titulos_por_tipo(datos['tipo_reporte_original'])
    story.append(Paragraph(titulo_principal, est_titulo))
    story.append(Spacer(1, 15))
    
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", "nan", ""] else datos['factura']
    es_reclamo = "RECLAMO AL PROVEEDOR" in str(datos['tipo_reporte_original']).upper()
    
    if es_reclamo:
        rep_txt = f"<font color='red'>{datos['tipo_reporte']}</font>"
        info = [
            [Paragraph(f"<b>{l['orden']}:</b>", est_txt), Paragraph(f"{datos['orden']}", est_txt), Paragraph(f"<b>{l['fec_rep']}:</b>", est_txt), Paragraph(f"{datos['fecha_reporte']}", est_txt)],
            [Paragraph(f"<b>{l['cliente']}:</b>", est_txt), Paragraph(f"{datos['cliente']}", est_txt), Paragraph(f"<b>{l['prod']}:</b>", est_txt), Paragraph(f"{datos['producto']}", est_txt)],
            [Paragraph(f"<b>{l['fac']}:</b>", est_txt), Paragraph(f"{fac_txt}", est_txt), Paragraph(f"<b>{l['marca']}:</b>", est_txt), Paragraph(f"{datos['marca']}", est_txt)],
            [Paragraph(f"<b>{l['fec_fac']}:</b>", est_txt), Paragraph(f"{datos['fecha_factura']}", est_txt), Paragraph(f"<b>{l['modelo']}:</b>", est_txt), Paragraph(f"{datos['modelo']}", est_txt)],
            [Paragraph(f"<b>{l['repuesto']}:</b>", est_txt), Paragraph(f"{datos['repuesto']}", est_txt), Paragraph(f"<b>{l['codigo']}:</b>", est_txt), Paragraph(f"{datos['codigo']}", est_txt)],
            [Paragraph(f"<b>{l['cantidad']}:</b>", est_txt), Paragraph(f"{datos['cantidad']}", est_txt), Paragraph(f"<b>{l['reporte']}:</b>", est_txt), Paragraph(rep_txt, est_txt)]
        ]
        t = Table(info, colWidths=[1.1*inch, 2.6*inch, 1.1*inch, 2.6*inch])
    else:
        info = [
            [Paragraph(f"<b>{l['orden']}:</b> {datos['orden']}", est_txt), Paragraph(f"<b>{l['fac']}:</b> {fac_txt}", est_txt)],
            [Paragraph(f"<b>{l['cliente']}:</b> {datos['cliente']}", est_txt), Paragraph(f"<b>{l['fec_fac']}:</b> {datos['fecha_factura']}", est_txt)],
            [Paragraph(f"<b>{l['prod']}:</b> {datos['producto']}", est_txt), Paragraph(f"<b>{l['serie']}:</b> {datos['serie']}", est_txt)],
            [Paragraph(f"<b>{l['realizador']}:</b> {datos['realizador']}", est_txt), Paragraph(f"<b>{l['fec_rep']}:</b> {datos['fecha_reporte']}", est_txt)]
        ]
        t = Table(info, colWidths=[3.7*inch, 3.7*inch])
        
    t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Secciones Dinámicas
    for tit, cont in secciones_activas:
        story.append(Paragraph(tit, est_sec))
        story.append(Paragraph(cont.replace('\n', '<br/>'), est_txt))
        story.append(Spacer(1, 5))

    # Imágenes
    if lista_imgs:
        story.append(Paragraph(l['evidencia'], est_sec))
        story.append(Spacer(1, 10))
        datos_cuadricula, fila_actual = [], []
        
        for idx, i in enumerate(lista_imgs):
            try:
                img_stream = BytesIO(i['imagen_raw'])
                img_obj = RLImage(img_stream, width=3.4*inch, height=2.2*inch)
                celda = [img_obj, Spacer(1, 4), Paragraph(f"{l['figura']} {idx+1}. {i['descripcion']}", est_fig)]
                fila_actual.append(celda)
                if len(fila_actual) == 2:
                    datos_cuadricula.append(fila_actual)
                    fila_actual = []
            except Exception:
                fila_actual.append([Paragraph(f"Error imagen {idx+1}", est_txt)])
                
        if fila_actual:
            fila_actual.append("")
            datos_cuadricula.append(fila_actual)
            
        if datos_cuadricula:
            t_grid = Table(datos_cuadricula, colWidths=[3.7*inch, 3.7*inch])
            t_grid.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            story.append(t_grid)

    story.append(Spacer(1, 60))
    t_firmas = Table([[Paragraph(f"{l['realizador']}:", est_firma), Paragraph(f"{l['revisador']}:", est_firma)], 
                      [Paragraph(datos['realizador'], est_firma), Paragraph(datos['tecnico'], est_firma)]], colWidths=[3.7*inch, 3.7*inch])
    story.append(t_firmas)
    
    doc.build(story, onFirstPage=agregar_marca_agua, onLaterPages=agregar_marca_agua)
    buffer.seek(0)
    return buffer.read()

def generar_txt_contenido(datos, secciones_activas):
    l = LBL
    titulo_txt = obtener_titulos_por_tipo(datos['tipo_reporte_original'])
    fac_txt = "STOCK" if str(datos['factura']).strip() in ["0", "nan", ""] else datos['factura']
    
    txt = f"{titulo_txt}\n" + "="*30 + "\n\n"
    txt += f"{l['cliente']}: {datos['cliente']}\n"
    txt += f"{l['fac']}: {fac_txt}\n"
    txt += f"{l['fec_fac']}: {datos['fecha_factura']}\n"
    txt += f"{l['orden']}: {datos['orden']}\n"
    txt += f"{l['prod']}: {datos['producto']}\n"
    
    if "RECLAMO AL PROVEEDOR" in str(datos['tipo_reporte_original']).upper():
        txt += f"{l['marca']}: {datos['marca']}\n"
        txt += f"{l['modelo']}: {datos['modelo']}\n"
        txt += f"{l['repuesto']}: {datos['repuesto']}\n"
        txt += f"{l['codigo']}: {datos['codigo']}\n"
        txt += f"{l['cantidad']}: {datos['cantidad']}\n"
    else:
        txt += f"{l['serie']}: {datos['serie']}\n"

    txt += f"{l['revisador']}: {datos['tecnico']}\n\n"
    txt += f"TIPO DE REPORTE: {datos['tipo_reporte']}\n\n"
    
    for tit, cont in secciones_activas:
        txt += f"--- {tit} ---\n{cont}\n\n"

    txt += f"Atentamente,\n{datos['realizador']}\nCoordinador Postventa"
    return txt

# --- 4. INTERFAZ ---
st.title("🚀 Reportes Técnicos")

orden_id = st.text_input("Ingrese número de Orden")
c_v, s_v, p_v, f_v, ff_v = "", "", "", "", date.today()

if orden_id:
    res = df_db[df_db['Orden'] == orden_id]
    if not res.empty:
        row = res.iloc[0]
        c_v, s_v, p_v, f_v = str(row.get('Cliente','')), str(row.get('Serie','')), str(row.get('Producto','')), str(row.get('Fac_Min',''))
        try: ff_v = pd.to_datetime(str(row.get('Fec_Fac_Min',''))).date()
        except: ff_v = date.today()

st.markdown("### Datos del Reporte")
col1, col2 = st.columns(2)
with col1:
    tipo_rep = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)
    f_realizador = st.selectbox("Realizado por", options=LISTA_REALIZADORES)
    f_cliente = st.text_input("Cliente", value=c_v)
    f_prod = st.text_input("Artículo / Producto", value=p_v)
with col2:
    f_tecnico = st.selectbox("Revisado por (Técnico)", options=LISTA_TECNICOS)
    f_fac = st.text_input("Factura", value=f_v)
    f_fec_fac = st.date_input("Fecha Factura", value=ff_v)
    f_fec_rep = st.date_input("Fecha del Reporte", value=date.today())
    f_serie = st.text_input("Serie", value=s_v)

# --- CAMPOS DINAMICOS PARA RECLAMO AL PROVEEDOR ---
f_marca, f_modelo, f_repuesto, f_codigo, f_cantidad = "", "", "", "", 1

if tipo_rep == "RECLAMO AL PROVEEDOR":
    st.markdown("### 📝 Datos de Reclamo al Proveedor")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        f_marca = st.text_input("Marca")
        f_modelo = st.text_input("Modelo")
        f_repuesto = st.text_input("Repuesto (Ej. CONGELADOR HORIZONTAL)")
    with col_r2:
        f_codigo = st.text_input("Código")
        f_cantidad = st.number_input("Cantidad", min_value=1, value=1)
st.markdown("---")

st.markdown("### 📝 Contenido del Reporte (Selecciona qué incluir)")
def_rf = f"Ingresa a servicio técnico {f_prod}. Se observa el uso continuo del artículo."
def_re = "Se procede a revisar el sistema de alimentación de energía y sus líneas de conexión.\nSe procede a revisar el sistema electrónico del equipo.\nSe procede a revisar el sistema mecanico de equipo"
texto_concl_default = TEXTOS_CONCLUSIONES.get(tipo_rep, "")

c_chk1, c_txt1 = st.columns([1, 10])
with c_chk1: inc_rf = st.checkbox("Incluir", value=True, key="c1")
with c_txt1: f_rev_fisica = st.text_area("Revisión Física", value=def_rf)

c_chk2, c_txt2 = st.columns([1, 10])
with c_chk2: inc_ing = st.checkbox("Incluir", value=True, key="c2")
with c_txt2: f_ingreso_tec = st.text_area("Ingresa a servicio técnico", value="Revisión inicial del equipo.")

c_chk3, c_txt3 = st.columns([1, 10])
with c_chk3: inc_re = st.checkbox("Incluir", value=True, key="c3")
with c_txt3: f_rev_electro = st.text_area("Revisión electro-electrónica-mecanica", value=def_re)

# Sección de Observaciones con Plantillas de Negación de Garantía
c_chk4, c_txt4 = st.columns([1, 10])
with c_chk4: inc_obs = st.checkbox("Incluir", value=True, key="c4")
with c_txt4: 
    st.selectbox("Plantillas de Observación (Opcional)", options=list(PLANTILLAS_OBSERVACIONES.keys()), key="sel_plantilla_obs", on_change=actualizar_observacion)
    f_obs = st.text_area("Observaciones", value=st.session_state.obs_text, height=120)

c_chk5, c_txt5 = st.columns([1, 10])
with c_chk5: inc_con = st.checkbox("Incluir", value=True, key="c5")
with c_txt5: f_concl = st.text_area("Conclusiones", value=texto_concl_default, height=100)

st.markdown("---")
st.markdown("### 📸 Evidencia Fotográfica")
uploaded_files = st.file_uploader("Subir imágenes", type=['jpg','png','jpeg'], accept_multiple_files=True)

lista_imgs_temp = [] 
if uploaded_files:
    for idx, file in enumerate(uploaded_files):
        c_img, c_desc = st.columns([1, 3])
        with c_img:
            st.image(file, use_container_width=True)
        with c_desc:
            desc = st.text_input(f"Descripción Imagen #{idx+1}", value="Evidencia técnica.", key=f"desc_{idx}")
            lista_imgs_temp.append({"file": file, "desc": desc})

st.markdown("---")

if st.button("💾 GENERAR ARCHIVOS (PDF Y TXT)", use_container_width=True):
    with st.spinner("Generando documentos..."):
        
        imgs_procesadas_es = []
        for item in lista_imgs_temp:
            try:
                p_img = PilImage.open(item['file'])
                if p_img.mode != 'RGB': p_img = p_img.convert('RGB')
                img_byte = BytesIO()
                p_img.save(img_byte, format='JPEG', quality=95)
                img_raw = img_byte.getvalue() 
                
                desc_es = item['desc']
                imgs_procesadas_es.append({"imagen_raw": img_raw, "descripcion": desc_es})
            except Exception as e:
                st.error(f"Error procesando imagen: {e}")

        # --- DATOS EN ESPAÑOL ---
        secciones_es = []
        titulos_es = ["Revisión Física", "Ingresa a servicio técnico", "Revisión electro-electrónica-mecanica", "Observaciones", "Conclusiones"]
        
        if inc_rf: secciones_es.append((titulos_es[0], f_rev_fisica))
        if inc_ing: secciones_es.append((titulos_es[1], f_ingreso_tec))
        if inc_re: secciones_es.append((titulos_es[2], f_rev_electro))
        if inc_obs: secciones_es.append((titulos_es[3], f_obs))
        if inc_con: secciones_es.append((titulos_es[4], f_concl))

        datos_es = {
            "orden": orden_id, "cliente": f_cliente, "factura": f_fac, "fecha_factura": f_fec_fac,
            "producto": f_prod, "serie": f_serie, "tecnico": f_tecnico, "realizador": f_realizador,
            "fecha_reporte": f_fec_rep, "tipo_reporte": tipo_rep, "tipo_reporte_original": tipo_rep,
            "marca": f_marca, "modelo": f_modelo, "repuesto": f_repuesto, "codigo": f_codigo, "cantidad": f_cantidad
        }

        st.session_state.pdf_es = generar_pdf(datos_es, secciones_es, imgs_procesadas_es)
        st.session_state.txt_es = generar_txt_contenido(datos_es, secciones_es)
        
        st.success("✅ ¡Los archivos PDF y TXT fueron generados exitosamente!")

if st.session_state.pdf_es:
    st.markdown("### 📥 Descargar Documentos")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Descargar PDF", data=st.session_state.pdf_es, file_name=f"{f_prod}_{f_cliente}_{orden_id}.pdf", mime="application/pdf", use_container_width=True)
    with c2:
        st.download_button("🔤 Descargar TXT", data=st.session_state.txt_es, file_name=f"Status_{orden_id}.txt", mime="text/plain", use_container_width=True)
