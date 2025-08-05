
import streamlit as st
import pandas as pd
import openai
import json
import gspread
from google.oauth2.service_account import Credentials
import io

# --- TÍTULO ---
st.set_page_config(page_title="Controller Financiero IA", layout="wide")
st.title("📊 Controller Financiero IA")

# --- AUTENTICACIÓN SIMPLE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔒 Iniciar sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user == "adm" and password == "adm":
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

# --- SUBIDA O CONEXIÓN DE ARCHIVO ---
st.sidebar.header("📂 Cargar datos")
source_type = st.sidebar.radio("Selecciona fuente de datos:", ["Excel", "Google Sheets"])

df = None

if source_type == "Excel":
    file = st.sidebar.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])
    if file:
        df = pd.read_excel(file, sheet_name=None)
elif source_type == "Google Sheets":
    sheet_url = st.sidebar.text_input("Pega el enlace de Google Sheets")
    if sheet_url:
        try:
            creds = Credentials.from_service_account_info(json.loads(st.secrets["GOOGLE_CREDENTIALS"]))
            client = gspread.authorize(creds)
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            spreadsheet = client.open_by_key(sheet_id)
            df = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
            st.sidebar.success("Conexión exitosa.")
        except Exception as e:
            st.sidebar.error(f"Error de autenticación: {e}")

if not df:
    st.warning("Por favor carga un archivo o conecta una hoja de Google.")
    st.stop()

# --- SELECCIÓN DE HOJA ---
hoja = st.selectbox("Selecciona una hoja para analizar", list(df.keys()))
data = df[hoja]
st.dataframe(data)

# --- PREGUNTA MANUAL O INTELIGENTE ---
st.subheader("🧠 Acciones Inteligentes")

col1, col2 = st.columns(2)
with col1:
    if st.button("📈 Analizar Rentabilidad"):
        st.session_state.user_prompt = "¿Cuál es la rentabilidad mensual y total del negocio?"
with col2:
    if st.button("📉 Ver meses con pérdida"):
        st.session_state.user_prompt = "¿Qué meses presentan pérdida y por qué?"

# Campo de pregunta personalizada
user_input = st.text_area("✍️ Pregunta libre", placeholder="Haz una pregunta sobre el negocio...", height=100)
if user_input:
    st.session_state.user_prompt = user_input

# --- PROCESAR PREGUNTA CON OPENAI ---
if "user_prompt" in st.session_state:
    st.subheader("💬 Respuesta")
    with st.spinner("Analizando con IA..."):

        openai.api_key = st.secrets["OPENAI_API_KEY"]

        # Construcción del prompt
        csv_preview = data.to_csv(index=False)
        prompt = f"""
Eres un Controller Financiero experto en gestión de talleres de desabolladura y pintura. 
Analiza los siguientes datos financieros y responde de forma clara, útil y fundamentada, para ayudar a los dueños del negocio a tomar decisiones acertadas.

Datos:
{csv_preview}

Pregunta: {st.session_state.user_prompt}
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            respuesta = response.choices[0].message["content"]
            st.success("✅ Análisis completado")
            st.markdown(respuesta)
        except Exception as e:
            st.error(f"⚠️ Error al consultar OpenAI: {e}")
