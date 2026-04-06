import streamlit as st
import pandas as pd
from datetime import date
from io import BytesIO, StringIO
import os
from groq import Groq

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    st.error("🔑 Error: Configure la API Key en los Secrets de Streamlit.")
    st.stop()

# --- 2. PERSONAL Y OPCIONES ---
LISTA_TECNICOS = ["Tec. Xavier Ramón", "Tec. Juan Diego Quezada", "Tec. Javier Quiguango", "Tec. Wilson Quiguango", "Tec. Carlos Jama", "Tec. Manuel Vera", "Tec. Juan Farez", "Tec. Santiago Farez"]
LISTA_REALIZADORES = ["Ing. Henry Beltran", "Ing. Pablo Lopez", "Ing. Christian Calle", "Ing. Guillermo Ortiz"]
OPCIONES_REPORTE = ["FUERA DE GARANTIA", "INFORME TECNICO", "RECLAMO AL PROVEEDOR"]

# --- 3. ESTADOS DE SESIÓN (Persistencia de datos) ---
if 'resumen_ia' not in st.session_state:
    st.session_state.resumen_ia = {"rev": "", "obs": "", "con": ""}

# --- 4. INTERFAZ ---
st.title("📥 Generador de Reportes Técnicos")

# Selección de Tipo (Influye en las conclusiones)
f_tipo = st.selectbox("Tipo de Reporte", options=OPCIONES_REPORTE)

col1, col2 = st.columns(2)
with col1:
    f_orden = st.text_input("Orden #")
    f_cliente = st.text_input("Cliente")
    f_realizador = st.selectbox("Realizado por", LISTA_REALIZADORES)
with col2:
    f_prod = st.text_input("Producto")
    f_tecnico = st.selectbox("Revisado por", LISTA_TECNICOS)
    f_fec = st.date_input("Fecha", value=date.today())

f_daño = st.text_area("🔧 Diagnóstico de Entrada")

if st.button("🤖 Generar con IA"):
    if f_daño:
        with st.spinner("Analizando según tipo de reporte..."):
            # Lógica de conclusión basada en el tipo de informe
            if f_tipo == "RECLAMO AL PROVEEDOR":
                meta = "Enfatizar falla de fabricación para reposición."
            elif f_tipo == "FUERA DE GARANTIA":
                meta = "Enfatizar desgaste por uso o daño externo no cubierto."
            else:
                meta = "Dictamen técnico estándar."

            prompt = (f"Producto: {f_prod}. Falla: {f_daño}. Tipo: {f_tipo}. Objetivo: {meta}. "
                      "Estructura: REVISION_TEC, OBSERVACIONES, CONCLUSIONES. Sin asteriscos.")
            
            resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            clean = resp.choices[0].message.content.strip()
            
            if "REVISION_TEC:" in clean:
                st.session_state.resumen_ia["rev"] = clean.split("REVISION_TEC:")[1].split("OBSERVACIONES:")[0].strip()
                st.session_state.resumen_ia["obs"] = clean.split("OBSERVACIONES:")[1].split("CONCLUSIONES:")[0].strip()
                st.session_state.resumen_ia["con"] = clean.split("CONCLUSIONES:")[1].strip()
            st.rerun()

# Mostrar campos generados (Permite edición manual antes de bajar)
st.text_area("2. Revisión Técnica", value=st.session_state.resumen_ia["rev"])
st.text_area("3. Observaciones", value=st.session_state.resumen_ia["obs"])
st.text_area("4. Conclusiones", value=st.session_state.resumen_ia["con"])

# --- 5. OPCIÓN DE DESCARGA ---
st.divider()
if st.session_state.resumen_ia["con"]: # Solo habilita si hay contenido
    # Creamos el archivo en memoria (Buffer)
    reporte_txt = (
        f"TIPO: {f_tipo}\nORDEN: {f_orden}\nCLIENTE: {f_cliente}\nPRODUCTO: {f_prod}\n"
        f"FECHA: {f_fec}\n----------------------------------\n"
        f"REVISIÓN: {st.session_state.resumen_ia['rev']}\n\n"
        f"OBSERVACIONES: {st.session_state.resumen_ia['obs']}\n\n"
        f"CONCLUSIONES: {st.session_state.resumen_ia['con']}\n\n"
        f"Realizado por: {f_realizador} | Revisado por: {f_tecnico}"
    )
    
    # Botón de descarga eficiente
    st.download_button(
        label="📥 Descargar Reporte (TXT)",
        data=reporte_txt,
        file_name=f"Reporte_{f_orden}_{f_tipo.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )
