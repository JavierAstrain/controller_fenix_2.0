import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials
from openai import OpenAI
import openai
import os
import json

# --- CREDENCIALES STREAMLIT ---
USER = st.secrets["USER"]
PASSWORD = st.secrets["PASSWORD"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# --- AUTENTICACION ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔐 Controller Financiero IA")
    st.subheader("🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username == USER and password == PASSWORD:
            st.session_state.authenticated = True
            st.success("Acceso concedido")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- FUNCIONES DE CARGA DE ARCHIVOS ---
def cargar_datos():
    tipo = st.radio("Selecciona el origen del archivo:", ("Excel", "Google Sheets"))
    if tipo == "Excel":
        archivo = st.file_uploader("Sube tu archivo Excel", type=[".xlsx", ".xls"])
        if archivo is not None:
            return pd.read_excel(archivo, sheet_name=None)
    else:
        google_json = st.text_area("Pega las credenciales de Google (formato JSON)")
        sheet_url = st.text_input("URL de Google Sheet")
        if google_json and sheet_url:
            try:
                creds = Credentials.from_service_account_info(json.loads(google_json), scopes=["https://www.googleapis.com/auth/spreadsheets"])
                client = gspread.authorize(creds)
                sheet = client.open_by_url(sheet_url)
                return {ws.title: pd.DataFrame(ws.get_all_records()) for ws in sheet.worksheets()}
            except Exception as e:
                st.error(f"Error al cargar Google Sheet: {e}")
    return None

# --- FUNCION DE RESPUESTA INTELIGENTE ---
def responder_pregunta(pregunta, datos):
    contenido = f"""
Actúa como un controller financiero experto en talleres de desabolladura y pintura.
Tienes acceso a las siguientes hojas del archivo:
{', '.join(datos.keys())}.
Responde con inteligencia, usando lenguaje profesional, y si se requiere, genera tablas o gráficos automáticamente. Si no puedes responder, di claramente el motivo.

Pregunta del usuario:
{pregunta}
"""
    hojas_como_texto = ""
    for nombre, df in datos.items():
        hojas_como_texto += f"\n\n### Hoja: {nombre}\n{df.head(20).to_string(index=False)}"

    prompt = contenido + hojas_como_texto

    client = OpenAI(api_key=OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        respuesta = response.choices[0].message.content
        st.markdown(respuesta)
        generar_visualizaciones(pregunta, datos)
    except Exception as e:
        st.error(f"Error al consultar OpenAI: {e}")

# --- FUNCION DE VISUALIZACION AUTOMATICA ---
def generar_visualizaciones(pregunta, datos):
    pregunta_lower = pregunta.lower()

    if "tipo de cliente" in pregunta_lower and "factura" in pregunta_lower:
        hoja = datos.get("Ventas") or list(datos.values())[0]
        if "Tipo de Cliente" in hoja.columns and "Monto Facturado Neto" in hoja.columns:
            resumen = hoja.groupby("Tipo de Cliente")["Monto Facturado Neto"].sum()
            st.write("### Gráfico de Monto Facturado Neto por Tipo de Cliente")
            fig, ax = plt.subplots()
            resumen.plot.pie(autopct='%1.1f%%', ax=ax)
            ax.set_ylabel("")
            st.pyplot(fig)

    elif "tabla" in pregunta_lower or "detalle" in pregunta_lower:
        hoja = list(datos.values())[0]
        st.write("### Tabla resumen (primeras 15 filas)")
        st.dataframe(hoja.head(15))

# --- APP PRINCIPAL ---
st.title("📊 Controller Financiero IA")
st.markdown("Esta herramienta analiza archivos financieros de talleres de desabolladura y pintura, responde preguntas y genera visualizaciones inteligentes.")

datos = cargar_datos()

if datos:
    pregunta = st.text_area("Haz tu pregunta financiera")
    if st.button("Responder"):
        responder_pregunta(pregunta, datos)
