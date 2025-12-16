import streamlit as st
from fpdf import FPDF
import tempfile
import os

# --- Configuración de la página ---
st.set_page_config(page_title="Generador de Reportes Técnicos", layout="centered")

# --- Lógica del PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Reporte de Servicio Técnico', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def generar_pdf(datos, imagenes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Información del Cliente
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "1. Información del Cliente y Equipo", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Cliente:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, datos['cliente'], 0, 1)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Fecha:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(datos['fecha']), 0, 1)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Dispositivo:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, datos['equipo'], 0, 1)
    pdf.ln(5)

    # 2. Detalles Técnicos
    pdf.cell(0, 10, "2. Diagnóstico y Solución", 0, 1, 'L', fill=True)
    pdf.ln(2)
    pdf.multi_cell(0, 10, f"Falla Reportada: {datos['falla']}")
    pdf.ln(2)
    pdf.multi_cell(0, 10, f"Trabajo Realizado: {datos['solucion']}")
    pdf.ln(5)

    # 3. Evidencia Fotográfica (Imágenes)
    if imagenes:
        pdf.cell(0, 10, "3. Evidencia Fotográfica", 0, 1, 'L', fill=True)
        pdf.ln(5)
        
        # FPDF necesita una ruta de archivo, no bytes. Guardamos temporalmente.
        for descripcion, archivo_img in imagenes.items():
            if archivo_img is not None:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, descripcion, 0, 1)
                
                # Crear archivo temporal para la imagen
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    temp_file.write(archivo_img.read())
                    temp_path = temp_file.name
                
                # Insertar imagen (Ancho 100mm)
                try:
                    pdf.image(temp_path, w=100)
                except:
                    pdf.cell(0, 10, "(Error al cargar imagen)", 0, 1)
                
                pdf.ln(5)
                # Borrar archivo temporal
                os.remove(temp_path)

    # Retornar el binario del PDF
    return pdf.output(dest='S').encode('latin-1')

# --- Interfaz del Formulario (Streamlit) ---
st.title("🛠️ Crear Reporte Técnico")
st.markdown("Llena los datos y adjunta fotos para generar el PDF.")

with st.form("formulario_reporte"):
    col1, col2 = st.columns(2)
    
    with col1:
        cliente = st.text_input("Nombre del Cliente")
        equipo = st.text_input("Equipo / Modelo")
        costo = st.number_input("Costo Total ($)", min_value=0.0)
    
    with col2:
        fecha = st.date_input("Fecha del Servicio")
        tecnico = st.text_input("Nombre del Técnico")
    
    falla = st.text_area("Falla Reportada / Problema")
    solucion = st.text_area("Diagnóstico y Solución Aplicada")
    
    st.markdown("### 📸 Carga de Imágenes")
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        img_antes = st.file_uploader("Foto del Estado Inicial (Antes)", type=['jpg', 'png', 'jpeg'])
    with col_img2:
        img_despues = st.file_uploader("Foto del Resultado (Después)", type=['jpg', 'png', 'jpeg'])

    # Botón de envío del formulario
    submitted = st.form_submit_button("Generar Reporte PDF")

# --- Generación y Descarga ---
if submitted:
    if not cliente or not equipo:
        st.error("Por favor completa al menos el nombre del cliente y el equipo.")
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
        
        # Preparar imágenes
        imgs_para_pdf = {
            "Estado Inicial": img_antes,
            "Resultado Final": img_despues
        }

        # Generar PDF
        pdf_bytes = generar_pdf(datos_formulario, imgs_para_pdf)
        
        st.success("¡Reporte generado con éxito!")
        
        # Botón de Descarga
        st.download_button(
            label="📥 Descargar PDF Final",
            data=pdf_bytes,
            file_name=f"Reporte_{cliente.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )