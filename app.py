import streamlit as st
from fpdf import FPDF
from fpdf import FPDF
from fpdf.fonts import find_font_path, FreeSerifFont # Importación necesaria para la fuente
import tempfile
import tempfile
import os
from datetime import date
from io import BytesIO

# --- Configuración de la página ---
st.set_page_config(page_title="Generador de Reportes Técnicos", layout="centered")

# --- Configuración de la Fuente UTF-8 ---
# CRÍTICO: Buscamos la ruta de FreeSerif (debe estar disponible si instalamos fonttools)
try:
    font_path = find_font_path("FreeSerif")
except FileNotFoundError:
    # Esto ocurre si fonttools no está instalado correctamente, pero lo ignoramos para permitir que FPDF siga con su fuente base
    font_path = None
    st.warning("Advertencia: No se encontró la fuente FreeSerif. Los caracteres especiales podrían causar errores.")


# --- Lógica del PDF ---
class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        if font_path:
            # Añadir la fuente FreeSerif y su versión Bold para soporte completo UTF-8
            self.add_font("FreeSerif", style="", fname=font_path)
            # Nota: Asumimos que la versión bold está en la misma ubicación con el sufijo 'Bold'
            self.add_font("FreeSerif", style="B", fname=font_path.replace('.ttf', 'Bold.ttf'))
            self.font_family = "FreeSerif"
        else:
            self.font_family = "Arial" # Si falla, usamos Arial como fallback

    def header(self):
        if os.path.exists("logo.png"):
            self.image('logo.png', 10, 8, 30) 
            self.ln(25) 
        else:
            self.ln(10)

        # Usar la fuente FreeSerif/Arial para el encabezado
        self.set_font(self.font_family, 'B', 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_family, '', 8) # Usar FreeSerif/Arial para el pie de página
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(datos, imagenes):
    pdf = PDF()
    pdf.add_page()
    # Usar la fuente definida en __init__
    pdf.set_font(pdf.font_family, size=12) 

    # 1. Información del Cliente
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "1. Información del Cliente y Equipo", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    # Datos del cliente y equipo
    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.cell(40, 10, "Cliente:", 0, 0)
    pdf.set_font(pdf.font_family, '', 12)
    pdf.cell(0, 10, datos['cliente'], 0, 1)
    
    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.cell(40, 10, "Fecha:", 0, 0)
    pdf.set_font(pdf.font_family, '', 12)
    pdf.cell(0, 10, str(datos['fecha']), 0, 1)

    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.cell(40, 10, "Dispositivo:", 0, 0)
    pdf.set_font(pdf.font_family, '', 12)
    pdf.cell(0, 10, datos['equipo'], 0, 1)

    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.cell(40, 10, "Técnico:", 0, 0)
    pdf.set_font(pdf.font_family, '', 12)
    pdf.cell(0, 10, datos['tecnico'], 0, 1)
    pdf.ln(5)

    # 2. Detalles Técnicos
    pdf.cell(0, 10, "2. Diagnóstico y Solución", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    # Falla Reportada
    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.multi_cell(0, 5, "Falla Reportada:")
    pdf.set_font(pdf.font_family, '', 12)
    pdf.multi_cell(0, 5, datos['falla'])
    pdf.ln(3)

    # Trabajo Realizado
    pdf.set_font(pdf.font_family, 'B', 12)
    pdf.multi_cell(0, 5, "Trabajo Realizado:")
    pdf.set_font(pdf.font_family, '', 12)
    pdf.multi_cell(0, 5, datos['solucion'])
    pdf.ln(5)

    # 3. Costo Total
    pdf.set_font(pdf.font_family, 'B', 14)
    pdf.cell(100, 10, "COSTO TOTAL DEL SERVICIO:", 0, 0)
    pdf.cell(0, 10, f"${datos['costo']:.2f}", 0, 1)
    pdf.ln(5)

    # 4. Evidencia Fotográfica (Imágenes)
    if any(imagenes.values()): 
        pdf.cell(0, 10, "4. Evidencia Fotográfica", 0, 1, 'L', fill=True)
        pdf.ln(5)
        
        for descripcion, archivo_img in imagenes.items():
            temp_path = None
            if archivo_img is not None:
                pdf.set_font(pdf.font_family, 'B', 12)
                pdf.cell(0, 10, descripcion, 0, 1)
                
                try:
                    archivo_img.seek(0)
                    
                    suffix = os.path.splitext(archivo_img.name)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(archivo_img.read())
                        temp_path = temp_file.name
                    
                    pdf.image(temp_path, w=100) 
                    
                except Exception as e:
                    pdf.set_font(pdf.font_family, '', 10)
                    pdf.cell(0, 10, f"(Error al cargar imagen. Detalle: {type(e).__name__})", 0, 1)
                    st.warning(f"Advertencia: No se pudo incluir la imagen '{descripcion}' en el PDF. ({type(e).__name__})")
                
                finally:
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
                
                pdf.ln(5)

    # 5. Firmas
    pdf.ln(10)
    pdf.set_font(pdf.font_family, '', 10)
    pdf.cell(90, 10, "_______________________", ln=0, align='C')
    pdf.cell(90, 10, "_______________________", ln=1, align='C')
    pdf.cell(90, 5, "Firma del Técnico", ln=0, align='C')
    pdf.cell(90, 5, "Firma del Cliente", ln=1, align='C')

    # **CRÍTICO PARA STREAMLIT**: devolver los bytes con dest='B'
    return pdf.output(dest='B')

# --- Interfaz del Formulario (Streamlit) ---
st.title("🛠️ Generador de Reporte Técnico")
st.markdown("---")

with st.form("formulario_reporte"):
    st.subheader("Datos Generales")
    col1, col2 = st.columns(2)
    
    with col1:
        cliente = st.text_input("Nombre del Cliente", key="cliente")
        equipo = st.text_input("Equipo / Modelo", key="equipo")
    
    with col2:
        fecha = st.date_input("Fecha del Servicio", key="fecha", value=date.today())
        tecnico = st.text_input("Nombre del Técnico", key="tecnico")

    st.subheader("Detalles del Servicio")
    falla = st.text_area("Falla Reportada / Problema", key="falla")
    solucion = st.text_area("Diagnóstico y Solución Aplicada", key="solucion")
    costo = st.number_input("Costo Total ($)", min_value=0.0, key="costo")
    
    st.markdown("### 📸 Evidencia Fotográfica (Opcional)")
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        img_antes = st.file_uploader("Foto del Estado Inicial (Antes)", type=['jpg', 'png', 'jpeg'], key="img_antes")
    with col_img2:
        img_despues = st.file_uploader("Foto del Resultado (Después)", type=['jpg', 'png', 'jpeg'], key="img_despues")

    submitted = st.form_submit_button("✅ Generar Reporte PDF")

# --- Generación y Descarga ---
if submitted:
    if not cliente or not equipo or not tecnico or not falla or not solucion:
        st.error("Por favor, complete los campos obligatorios: Cliente, Equipo, Técnico, Falla y Solución.")
    else:
        # Preparar datos
        datos_formulario = {
            "cliente": cliente,
            "equipo": equipo,
            "fecha": fecha,
            "tecnico": tecnico,
            "falla": falla,
            "solucion": solucion,
            "costo": costo
        }
        
        imgs_para_pdf = {
            "Estado Inicial (Antes)": img_antes,
            "Resultado Final (Después)": img_despues
        }

        # Generar PDF
        with st.spinner('Generando PDF...'):
            try:
                pdf_bytes = generar_pdf(datos_formulario, imgs_para_pdf)
                st.success("¡Reporte generado con éxito! Puede descargarlo a continuación.")
                
                nombre_archivo = f"Reporte_{cliente.replace(' ', '_')}_{date.today()}.pdf"
                st.download_button(
                    label="📥 Descargar PDF Final",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error CRÍTICO al generar el PDF. Detalle: {type(e).__name__}. Esto suele indicar un problema con caracteres no soportados o fallo de la librería FPDF.")

