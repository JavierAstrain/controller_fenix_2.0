import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt
import seaborn as sns
import json
from io import BytesIO
from google.oauth2.service_account import Credentials
import gspread

# Configuración inicial
st.set_page_config(page_title="Controller Financiero IA", layout="wide")
st.title("📊 Controller Financiero IA")

# --- LOGIN SIMPLE ---
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.subheader("🔐 Iniciar sesión")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if user == "adm" and password == "adm":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

# --- API KEY ---
openai.api_key = st.secrets["OPENAI_API_KEY"]

# --- CARGAR DATOS ---
df = None

st.subheader("1. Cargar datos financieros")
opcion = st.radio("Selecciona fuente de datos:", ["Subir Excel", "Google Sheets"])

if opcion == "Subir Excel":
    archivo = st.file_uploader("Sube tu archivo Excel", type=[".xlsx", ".xls"])
    if archivo:
        df = pd.read_excel(archivo, sheet_name=None)

elif opcion == "Google Sheets":
    gs_url = st.text_input("Pega el enlace para compartir de Google Sheets")
    if gs_url:
        try:
            creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
            scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet_id = gs_url.split("/d/")[1].split("/")[0]
            spreadsheet = client.open_by_key(sheet_id)
            df = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
            st.success("Google Sheets cargado correctamente")
        except Exception as e:
            st.error(f"Error al leer Google Sheet: {e}")

if not df:
    st.info("Por favor, carga una planilla para comenzar")
    st.stop()

# --- VISUALIZACION DE HOJAS ---
st.subheader("2. Vista previa de datos")
nombre_hoja = st.selectbox("Selecciona la hoja a visualizar", list(df.keys()))
df_hoja = df[nombre_hoja]
st.dataframe(df_hoja, use_container_width=True)

# --- CONSULTAS CON IA ---
st.subheader("3. Asistente financiero experto")

pregunta = st.text_area("Haz tu consulta financiera sobre todo el archivo cargado:")

if st.button("💬 Responder con IA") and pregunta:
    try:
        contenido = ""
        for nombre, data in df.items():
            contenido += f"\n\nSheet: {nombre}\n{data.to_csv(index=False)}"

        prompt = (
            f"Actúa como un controller financiero experto en negocios de desabolladura y pintura automotriz. "
            f"Analiza la siguiente información contable en CSV de un taller con datos financieros reales. "
            f"Responde con información verídica, sugerencias de mejora, y recomendaciones para el dueño.\n"
            f"Datos completos de todas las hojas:\n{contenido}\n\nPregunta del usuario: {pregunta}"
        )

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )

        respuesta = response["choices"][0]["message"]["content"]
        st.markdown("#### 📌 Respuesta experta:")
        st.write(respuesta)

    except Exception as e:
        st.error(f"⚠️ Error al consultar OpenAI: {e}")

# --- GRAFICOS ---
st.subheader("4. Visualización de datos")

col1, col2 = st.columns(2)
with col1:
    hoja_graf = st.selectbox("Selecciona hoja para gráfico", list(df.keys()), key="graf")
    col_x = st.selectbox("Eje X", df[hoja_graf].columns)
    col_y = st.selectbox("Eje Y", df[hoja_graf].columns)
with col2:
    tipo_graf = st.selectbox("Tipo de gráfico", ["Barra", "Línea", "Dispersión"])

if st.button("📊 Generar gráfico"):
    try:
        plt.figure(figsize=(10, 4))
        if tipo_graf == "Barra":
            sns.barplot(x=col_x, y=col_y, data=df[hoja_graf])
        elif tipo_graf == "Línea":
            sns.lineplot(x=col_x, y=col_y, data=df[hoja_graf])
        elif tipo_graf == "Dispersión":
            sns.scatterplot(x=col_x, y=col_y, data=df[hoja_graf])
        plt.xticks(rotation=45)
        st.pyplot(plt)
    except Exception as e:
        st.error(f"Error al generar el gráfico: {e}")
