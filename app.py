# --- Lógica del PDF ---
# ... (Clase PDF sin cambios) ...

def generar_pdf(datos, imagenes):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # 1. Información del Cliente
    # ... (Resto del código de cliente/equipo) ...
    
    # 2. Detalles Técnicos
    # ... (Resto del código de falla/solución) ...

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
                    # El objeto FileUploader de Streamlit tiene un método .read() para obtener los bytes
                    temp_file.write(archivo_img.read()) 
                    temp_path = temp_file.name
                
                # Insertar imagen (Asegúrate de que el ancho sea apropiado)
                try:
                    pdf.image(temp_path, w=100) 
                except Exception as e:
                    pdf.cell(0, 10, f"(Error al cargar imagen: {e})", 0, 1)
                
                pdf.ln(5)
                # Borrar archivo temporal
                os.remove(temp_path)

    # -------------------------------------------------------------
    # CAMBIO CRÍTICO AQUÍ: Usamos dest='B' para obtener bytes binarios.
    # -------------------------------------------------------------
    return pdf.output(dest='B')
