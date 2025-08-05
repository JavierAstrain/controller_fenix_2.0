
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from google.oauth2.service_account import Credentials
from openai import OpenAI
from io import BytesIO

st.set_page_config(layout="wide", page_title="Controller Financiero IA")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.markdown("## 🔐 Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username == st.secrets["USER"] and password == st.secrets["PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.authenticated:
    login()
    st.stop()

col1, col2, col3 = st.columns([1, 2, 1])

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

def generar_grafico_torta(df, columna_categoria, columna_valor, titulo):
    resumen = df.groupby(columna_categoria)[columna_valor].sum()
    fig, ax = plt.subplots()
    resumen.plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_title(titulo)
    ax.set_ylabel("")
    st.pyplot(fig)

def generar_grafico_barras(df, columna_categoria, columna_valor, titulo):
    resumen = df.groupby(columna_categoria)[columna_valor].sum().reset_index()
    fig, ax = plt.subplots()
    ax.bar(resumen[columna_categoria], resumen[columna_valor])
    ax.set_title(titulo)
    ax.set_ylabel(columna_valor)
    ax.set_xlabel(columna_categoria)
    st.pyplot(fig)

def mostrar_tabla_resumen(df, columna_categoria, columna_valor):
    resumen = df.groupby(columna_categoria)[columna_valor].sum().reset_index()
    st.markdown("### 📋 Tabla resumen")
    st.dataframe(resumen)

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

with col2:
    if data:
        st.markdown("### 📊 Vista previa de datos")
        for name, df in data.items():
            st.markdown(f"#### 🧾 Hoja: {name}")
            st.dataframe(df.head(10))

with col3:
    st.markdown("### 🤖 Consultar con IA")
    pregunta = st.text_area("Haz una pregunta sobre los datos")
    if st.button("Responder") and pregunta and data:
        contenido = ""
        for name, df in data.items():
            contenido += f"Hoja: {name}\n{df.head(50).to_string(index=False)}\n\n"

        prompt = (
            "Eres un controller financiero experto. Analiza los siguientes datos de un taller "
            "de desabolladura y pintura de vehículos livianos y pesados:\n\n"
            f"{contenido}\n"
            f"Pregunta: {pregunta}\n\n"
            "Responde con análisis detallado. Si es útil y detectas que el usuario lo solicita, "
            "responde usando este formato markdown:\n"
            "Si hay un gráfico de torta, responde con: `grafico_torta:<columna_categoria>|<columna_valor>|<titulo>`\n"
            "Si hay un gráfico de barras, responde con: `grafico_barras:<columna_categoria>|<columna_valor>|<titulo>`\n"
            "Si deseas mostrar tabla resumen, responde con: `tabla_resumen:<columna_categoria>|<columna_valor>`\n"
        )

        respuesta = ask_gpt(prompt)
        st.markdown(respuesta)

        if "grafico_torta:" in respuesta:
            partes = respuesta.split("grafico_torta:")[1].split("|")
            generar_grafico_torta(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
        if "grafico_barras:" in respuesta:
            partes = respuesta.split("grafico_barras:")[1].split("|")
            generar_grafico_barras(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
        if "tabla_resumen:" in respuesta:
            partes = respuesta.split("tabla_resumen:")[1].split("|")
            mostrar_tabla_resumen(df, partes[0].strip(), partes[1].strip())
