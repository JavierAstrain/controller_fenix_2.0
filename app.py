
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO
import tempfile

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Controller Financiero IA", page_icon="📊")
st.title("📊 Controller Financiero IA")

# --- LOGIN SIMPLE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.subheader("🔐 Iniciar sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user == "adm" and password == "adm":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- CARGA DE ARCHIVO ---
st.subheader("📁 Subir archivo financiero")

dataframes = {}
uploaded_file = st.file_uploader("Sube un archivo Excel", type=["xlsx"])
gsheet_url = st.text_input("O ingresa una URL de Google Sheets (con acceso de lectura público)")

if uploaded_file:
    excel = pd.ExcelFile(uploaded_file)
    for sheet in excel.sheet_names:
        dataframes[sheet] = excel.parse(sheet)
    st.success(f"📄 {len(dataframes)} hojas cargadas desde Excel.")
elif gsheet_url:
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("gspread_key.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(gsheet_url)
        for worksheet in sheet.worksheets():
            df = pd.DataFrame(worksheet.get_all_records())
            dataframes[worksheet.title] = df
        st.success(f"📄 {len(dataframes)} hojas cargadas desde Google Sheets.")
    except Exception as e:
        st.error(f"❌ Error al leer Google Sheets: {e}")
        st.stop()
else:
    st.info("Sube un archivo o ingresa un link para comenzar.")
    st.stop()

# --- CONFIGURAR OPENAI ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- CONSULTAS ---
st.subheader("💬 Consultar a IA financiera")
pregunta = st.text_area("Escribe tu consulta financiera:")

if st.button("Responder"):
    with st.spinner("Pensando como controller financiero..."):
        # Preparamos los datos
        full_text = ""
        for name, df in dataframes.items():
            full_text += f"--- Hoja: {name} ---\n"
            full_text += df.head(20).to_csv(index=False) + "\n"

        prompt = f"""
Actúa como un controller financiero experto y profesional en gestión. Tu cliente es un taller de desabolladura y pintura de vehículos livianos y pesados. Recibirás una base de datos en formato tabla, proveniente de Excel o Google Sheets, y deberás:

1. Leer, comprender y analizar los datos de todas las hojas.
2. Responder de forma clara, profesional y con cálculos reales.
3. Sugerir gráficos automáticamente cuando ayuden a visualizar mejor los datos (indica tipo y variables).
4. Generar insights, comparaciones y recomendaciones como experto.
5. Realizar proyecciones si se solicita.

Datos disponibles:
{full_text}

Pregunta del usuario:
{pregunta}

Responde en español con el formato más útil posible para el cliente.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            respuesta = response["choices"][0]["message"]["content"]
            st.markdown("### 📢 Respuesta")
            st.markdown(respuesta)

            # Intentar generar gráfico si la IA lo sugiere
            if "gráfico de torta" in respuesta.lower() or "gráfico circular" in respuesta.lower():
                for sheet_name, df in dataframes.items():
                    if "cliente" in df.columns and "monto" in df.columns:
                        fig, ax = plt.subplots()
                        df.groupby("cliente")["monto"].sum().plot(kind="pie", autopct='%1.1f%%', ax=ax)
                        ax.set_ylabel("")
                        st.pyplot(fig)
                        break
            elif "gráfico de barras" in respuesta.lower():
                for sheet_name, df in dataframes.items():
                    if "cliente" in df.columns and "monto" in df.columns:
                        fig, ax = plt.subplots()
                        df.groupby("cliente")["monto"].sum().plot(kind="bar", ax=ax)
                        st.pyplot(fig)
                        break

        except Exception as e:
            st.error(f"❌ Error al consultar OpenAI: {e}")
