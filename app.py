import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from google.oauth2.service_account import Credentials
from openai import OpenAI
import io

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

# --- LAYOUT ---
left, center, right = st.columns([1, 2, 2])

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

def render_graphic(df, tipo, categoria, valor, titulo):
    fig, ax = plt.subplots()
    agrupado = df.groupby(categoria)[valor].sum()

    if tipo == "torta":
        ax.pie(agrupado, labels=agrupado.index, autopct='%1.1f%%')
        ax.set_title(titulo)
    elif tipo == "barra":
        agrupado.plot(kind="bar", ax=ax)
        ax.set_title(titulo)
        ax.set_ylabel(valor)
        ax.set_xlabel(categoria)

    st.pyplot(fig)

# --- PANEL IZQUIERDO: CARGA DE DATOS ---
with left:
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

# --- PANEL CENTRAL: VISTA DE DATOS ---
with center:
    if data:
        st.markdown("### 📊 Vista previa de datos")
        for name, df in data.items():
            st.markdown(f"#### 📄 Hoja: {name}")
            st.dataframe(df.head(10))

# --- PANEL DERECHO: CONSULTA CON IA ---
with right:
    st.markdown("### 🤖 Consulta Financiera")
    pregunta = st.text_area("Haz una pregunta basada en los datos")
    if st.button("Responder") and pregunta and data:
        contenido = ""
        for name, df in data.items():
            contenido += f"### Hoja: {name}\n{df.head(50).to_string(index=False)}\n\n"

        prompt = (
            "Actúa como un controller financiero profesional para un taller automotriz de desabolladura y pintura. "
            "Analiza los datos entregados a continuación y responde en lenguaje profesional y estratégico, "
            "evitando explicar cómo hiciste el análisis. Si se puede representar con un gráfico (torta, barras, líneas) "
            "o tabla, indícalo con un marcador especial en el formato:\n"
            "grafico_torta:CATEGORIA|VALOR|TITULO\n"
            "grafico_barra:CATEGORIA|VALOR|TITULO\n"
            "tabla:HOJA|COLUMNAS\n\n"
            f"{contenido}\n"
            f"Pregunta: {pregunta}"
        )

        respuesta = ask_gpt(prompt)
        st.markdown("### 📈 Análisis y Respuesta")
        for line in respuesta.splitlines():
            if line.startswith("grafico_torta:") or line.startswith("grafico_barra:"):
                tipo, contenido = line.split(":")
                categoria, valor, titulo = contenido.split("|")
                for name, df in data.items():
                    if categoria in df.columns and valor in df.columns:
                        render_graphic(df, tipo.replace("grafico_", ""), categoria, valor, titulo)
            elif line.startswith("tabla:"):
                _, hoja, columnas = line.split(":")
                cols = [col.strip() for col in columnas.split(",")]
                if hoja in data:
                    st.dataframe(data[hoja][cols])
            else:
                st.markdown(line)
