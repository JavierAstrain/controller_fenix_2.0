import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from google.oauth2.service_account import Credentials
from openai import OpenAI
from analizador import analizar_datos_taller

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

# --- MEMORIA DE CONVERSACIÓN ---
if "historial" not in st.session_state:
    st.session_state.historial = []

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
    messages = [{"role": "system", "content": "Eres un controller financiero experto de un taller de desabolladura y pintura."}]
    for h in st.session_state.historial:
        messages.append({"role": "user", "content": h["pregunta"]})
        messages.append({"role": "assistant", "content": h["respuesta"]})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
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

        if st.button("📊 Análisis General Automático"):
            analisis = analizar_datos_taller(data)
            texto_analisis = json.dumps(analisis, indent=2, ensure_ascii=False)

            prompt = f"""
Contexto del negocio: Taller Fénix especializado en desabolladura y pintura de vehículos livianos y pesados.

Actúa como un controller financiero senior. Evalúa los siguientes datos calculados del negocio, entregados por un motor de análisis real:

{texto_analisis}

Entrega:
- Un análisis financiero profesional.
- Visualizaciones sugeridas si corresponde.
- Recomendaciones prácticas y accionables para la gerencia.
- No inventes datos. Solo interpreta lo que se entrega.
"""
            respuesta = ask_gpt(prompt)
            st.markdown(respuesta)
            st.session_state.historial.append({"pregunta": "Análisis general", "respuesta": respuesta})

        if st.button("Responder") and pregunta:
            contenido = ""
            for name, df in data.items():
                contenido += f"Hoja: {name}\n{df.head(50).to_string(index=False)}\n\n"

            prompt = f"""
Datos disponibles:\n\n{contenido}\n
Pregunta del usuario: {pregunta}\n
Tu rol es responder como controller financiero con análisis, visualización (si aplica) y recomendaciones.
Si es útil, usa alguno de estos formatos para visualizar:
- grafico_torta:col_categoria|col_valor|titulo
- grafico_barras:col_categoria|col_valor|titulo
- tabla:col_categoria|col_valor
""".strip()

            respuesta = ask_gpt(prompt)
            st.markdown(respuesta)
            st.session_state.historial.append({"pregunta": pregunta, "respuesta": respuesta})
