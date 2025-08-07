
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from google.oauth2.service_account import Credentials
from openai import OpenAI

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
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

if not st.session_state.authenticated:
    login()
    st.stop()

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

def mostrar_grafico_torta(df, col_categoria, col_valor, titulo):
    resumen = df.groupby(col_categoria)[col_valor].sum()
    fig, ax = plt.subplots()
    ax.pie(resumen, labels=resumen.index, autopct='%1.1f%%', startangle=90)
    ax.set_title(titulo)
    st.pyplot(fig)

def mostrar_grafico_barras(df, col_categoria, col_valor, titulo):
    resumen = df.groupby(col_categoria)[col_valor].sum().sort_values()
    fig, ax = plt.subplots()
    resumen.plot(kind="barh", ax=ax)
    ax.set_title(titulo)
    ax.set_xlabel(col_valor)
    st.pyplot(fig)

def mostrar_tabla(df, col_categoria, col_valor):
    resumen = df.groupby(col_categoria)[col_valor].sum().reset_index()
    st.markdown("### 📊 Tabla Resumen")
    st.dataframe(resumen)

# --- INTERFAZ EN COLUMNAS ---
col1, col2, col3 = st.columns([1, 2, 1])
data = None

with col1:
    st.markdown("### 📁 Subir archivo")
    tipo_fuente = st.radio("Fuente de datos", ["Excel", "Google Sheets"])
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
        st.markdown("### 📄 Vista previa")
        for name, df in data.items():
            st.markdown(f"#### 📘 Hoja: {name}")
            st.dataframe(df.head(10))

with col3:
    if data:
        st.markdown("### 🤖 Consulta con IA")
        pregunta = st.text_area("Pregunta")
        if st.button("Responder") and pregunta:
            contenido = ""
            for name, df in data.items():
                contenido += f"Hoja: {name}\n{df.head(50).to_string(index=False)}\n\n"

            prompt = f"""
Actúa como un controller financiero experto de un taller de desabolladura y pintura. Tu tarea es analizar los datos que se te entregan y responder con:

1. Un análisis financiero claro y profesional.
2. Si corresponde, sugiere visualizaciones en alguno de estos formatos:
   - grafico_torta:col_categoria|col_valor|titulo
   - grafico_barras:col_categoria|col_valor|titulo
   - tabla:col_categoria|col_valor
3. Entrega al menos una recomendación o decisión sugerida de gestión.

No inventes información. Usa solo los datos que te entrego. No expliques cómo responder, solo hazlo como experto.

Datos disponibles:\n\n{contenido}\n
Pregunta del usuario: {pregunta}
""".strip()

            respuesta = ask_gpt(prompt)
            st.markdown(respuesta)

            for linea in respuesta.splitlines():
                if "grafico_torta:" in linea:
                    partes = linea.replace("grafico_torta:", "").split("|")
                    if len(partes) == 3:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_grafico_torta(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
                if "grafico_barras:" in linea:
                    partes = linea.replace("grafico_barras:", "").split("|")
                    if len(partes) == 3:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_grafico_barras(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
                if "tabla:" in linea:
                    partes = linea.replace("tabla:", "").split("|")
                    if len(partes) == 2:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_tabla(df, partes[0].strip(), partes[1].strip())
