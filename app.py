import streamlit as st
import pandas as pd
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import io
import base64

# --- Autenticación desde secrets ---
USER = st.secrets["USER"]
PASSWORD = st.secrets["PASSWORD"]
GOOGLE_CREDENTIALS = st.secrets["GOOGLE_CREDENTIALS"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# --- Cliente OpenAI ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Inicio de sesión ---
st.set_page_config(page_title="Controller Financiero IA", page_icon="📊")
st.title("📊 Controller Financiero IA")

with st.expander("🔐 Iniciar sesión", expanded=True):
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username == USER and password == PASSWORD:
            st.session_state["authenticated"] = True
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.get("authenticated"):
    st.stop()

# --- Carga de datos ---
archivo = st.file_uploader("Sube un archivo Excel o conecta Google Sheets", type=["xlsx"])
df_dict = {}

if archivo:
    xls = pd.ExcelFile(archivo)
    for hoja in xls.sheet_names:
        df_dict[hoja] = xls.parse(hoja)
    st.success("Archivo Excel cargado con éxito")
else:
    st.info("O conecta una planilla de Google Sheets con ID")
    sheet_id = st.text_input("ID de Google Sheet")
    if sheet_id:
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(GOOGLE_CREDENTIALS, scopes=scope)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        for hoja in sh.worksheets():
            df = pd.DataFrame(hoja.get_all_records())
            df_dict[hoja.title] = df
        st.success("Planilla Google cargada con éxito")

if not df_dict:
    st.stop()

# --- Mostrar hojas disponibles ---
st.subheader("📄 Hojas cargadas")
for nombre, df in df_dict.items():
    st.markdown(f"### {nombre}")
    st.dataframe(df.head())

# --- Consulta del usuario ---
st.subheader("🤖 Consulta al Controller Financiero IA")
pregunta = st.text_area("Escribe tu consulta sobre la información financiera")

if st.button("Responder") and pregunta:
    # Preparar contenido del libro completo
    contexto = ""
    for nombre, df in df_dict.items():
        contexto += f"\n--- HOJA: {nombre} ---\n"
        contexto += df.head(20).to_string(index=False)

    prompt = [
        {"role": "system", "content": "Eres un controller financiero experto en gestión de talleres de desabolladura y pintura automotriz. Debes responder con análisis reales, correctos, y puedes usar gráficos si es necesario. Entrega recomendaciones profesionales y ordenadas."},
        {"role": "user", "content": f"Datos del archivo:\n{contexto}\n\nPregunta: {pregunta}"}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=prompt,
            temperature=0.2
        )
        respuesta = response.choices[0].message.content
        st.markdown("### Respuesta")
        st.markdown(respuesta)

        # Gráfico automático según algunas palabras clave
        if "gráfico" in respuesta.lower():
            for nombre, df in df_dict.items():
                if "tipo de cliente" in df.columns and "facturación" in df.columns:
                    fig, ax = plt.subplots()
                    datos = df.groupby("tipo de cliente")["facturación"].sum()
                    datos.plot(kind="pie", autopct='%1.1f%%', ax=ax)
                    ax.set_ylabel("")
                    st.pyplot(fig)
                    break

    except Exception as e:
        st.error(f"Error al consultar OpenAI: {e}")
