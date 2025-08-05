
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from google.oauth2.service_account import Credentials
from openai import OpenAI
from io import BytesIO

st.set_page_config(layout="wide", page_title="Controller Financiero IA")

# --- LOGIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.markdown("## 🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username == st.secrets["USER"] and password == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- LAYOUT EN COLUMNAS ---
col1, col2, col3 = st.columns([1, 2, 1])

# --- FUNCIONES ---
def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

def load_gsheet(json_keyfile, sheet_url):
    creds_dict = json.loads(json_keyfile)
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url)
    return {ws.title: pd.DataFrame(ws.get_all_records()) for ws in sheet.worksheets()}

def ask_gpt(prompt):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

def generar_grafico(df, columna_categoria, columna_valor, titulo):
    fig, ax = plt.subplots()
    df.groupby(columna_categoria)[columna_valor].sum().plot(kind="bar", ax=ax)
    ax.set_title(titulo)
    ax.set_ylabel(columna_valor)
    ax.set_xlabel(columna_categoria)
    st.pyplot(fig)

# --- CARGA DE DATOS ---
with col1:
    st.markdown("### 📁 Subir archivo")
    tipo_fuente = st.radio("Fuente de datos", ["Excel", "Google Sheets"])
    data = None

    if tipo_fuente == "Excel":
        file = st.file_uploader("Sube un archivo Excel", type=["xlsx", "xls"])
        if file:
            data = load_excel(file)
    else:
        url = st.text_input("URL de Google Sheet")
        if url and st.button("Conectar"):
            data = load_gsheet(st.secrets["GOOGLE_CREDENTIALS"], url)

# --- MOSTRAR TABLAS ---
with col2:
    if data:
        st.markdown("### 📊 Vista previa de datos")
        for name, df in data.items():
            st.markdown(f"#### 🧾 Hoja: {name}")
            st.dataframe(df.head(10))

# --- CONSULTAS CON IA ---
with col3:
    st.markdown("### 🤖 Consultar con IA")
    pregunta = st.text_area("Haz una pregunta sobre los datos")
    if st.button("Responder") and pregunta and data:
        contenido = ""
        for name, df in data.items():
            contenido += f"Hoja: {name}
{df.head(50).to_string(index=False)}
"

        prompt = (
            "Eres un controller financiero experto. Analiza los siguientes datos de un taller "
            "de desabolladura y pintura de vehículos:
"
            f"{contenido}

"
            f"Pregunta: {pregunta}

"
            "Responde con análisis detallado, gráfico si es útil, y una tabla si aplica. "
            "Sé profesional, claro y enfocado en decisiones estratégicas."
        )

        respuesta = ask_gpt(prompt)
        st.markdown(respuesta)
