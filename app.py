import streamlit as st
from fpdf import FPDF
import tempfile
import os
from datetime import date
from io import BytesIO

# --- Configuración de la página ---
st.set_page_config(page_title="Generador de Reportes Técnicos", layout="centered")

# --- Lógica del PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image('logo.png', 10, 8, 30) 
            self.ln(25) 
        else:
            self.ln(10)

        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'REPORTE DE SERVICIO TÉCNICO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(datos, imagenes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Información del Cliente
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "1. Información del Cliente y Equipo", 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    # ... (Resto de la información de Cliente/Equipo)
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

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Técnico:", 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, datos['tecnico'], 0, 1)
    pdf.ln(5)

    # 2. Detalles Técnicos
    pdf.cell(0, 10, "2. Diagnóstico y Solución", 0, 1, 'L', fill=True)
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 5, "Falla Reportada:")
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 5, datos['falla'])
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 5, "Trabajo Realizado:")
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 5, datos['solucion'])
    pdf.ln(5)

    # 3. Costo Total
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(100, 10, "COSTO TOTAL DEL SERVICIO:", 0, 0)
    pdf.cell(0, 10, f"${datos['costo']:.2f}", 0, 1)
    pdf.ln(5)

    # 4. Evidencia Fotográfica (Imágenes)
    if any(imagenes.values()): 
        pdf.cell(0, 10, "4. Evidencia Fotográfica", 0, 1, 'L', fill=True)
        pdf.ln(5)
        
        for descripcion, archivo_img in imagenes.items():
            if archivo_img is not None:
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, descripcion, 0, 1)
                
                temp_path = None # Inicializamos la ruta temporal
                try:
                    # Crear archivo temporal para la imagen
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                        # Necesitamos reiniciar el puntero para leer los bytes desde el inicio
                        archivo_img.seek(0)
                        temp_file.write(archivo_img.read())
                        temp_path = temp_file.name
                    
                    # Insertar imagen 
                    pdf.image(temp_path, w=100) 
                    
                except Exception as e:
                    # Si falla la imagen, simplemente lo notifica y continúa
                    pdf.cell(0, 10, f"(Error al cargar imagen: {type(e).__name__})", 0, 1)
                
                finally:
                    # Borrar archivo temporal si existe
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
                
                pdf.ln(5)

    # 5. Firmas
    pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    pdf.cell(90, 10, "_______________________", ln=0, align='C')
    pdf.cell(90, 10, "_______________________", ln=1, align='C')
    pdf.cell(90, 5, "Firma del Técnico", ln=0, align='C')
    pdf.cell(90, 5, "Firma del Cliente", ln=1, align='C')


    # Corrección final: devuelve los bytes para Streamlit
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
        
        # Preparar imágenes
        imgs_para_pdf = {
            "Estado Inicial (Antes)": img_antes,
            "Resultado Final (Después)": img_despues
        }

        # Generar PDF
        with st.spinner('Generando PDF...'):
            try:
                pdf_bytes = generar_pdf(datos_formulario, imgs_para_pdf)
                st.success("¡Reporte generado con éxito! Puede descargarlo a continuación.")
                
                # Botón de Descarga
                nombre_archivo = f"Reporte_{cliente.replace(' ', '_')}_{date.today()}.pdf"
                st.download_button(
                    label="📥 Descargar PDF Final",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf"
                )
            except Exception as e:
                # Si falla algo desconocido, mostramos el error general
                st.error(f"Error al generar el PDF. Revise el log. Detalle: {type(e).__name__}")
