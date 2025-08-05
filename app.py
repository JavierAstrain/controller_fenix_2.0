import streamlit as st
import pandas as pd
import gspread
import json
import plotly.express as px
import requests
from google.oauth2.service_account import Credentials

# Configuración inicial
st.set_page_config(page_title="Controller Financiero IA", layout="wide")
st.title("📊 Controller Financiero Inteligente con DeepSeek (via Together.ai)")

# Cargar credenciales
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

TOGETHER_API_KEY = st.secrets["TOGETHER_API_KEY"]

# Sesión para historial
if "historial" not in st.session_state:
    st.session_state["historial"] = []

def preguntar_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=payload)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error consultando DeepSeek: {e}"

# Carga de datos
st.subheader("1. Cargar Planilla Financiera")
opcion = st.radio("¿Desde dónde quieres cargar tus datos?", ["Excel", "Google Sheets"])

df = None
hojas = []

if opcion == "Excel":
    archivo = st.file_uploader("Sube tu archivo Excel (.xlsx)", type=["xlsx"])
    if archivo:
        hojas = pd.ExcelFile(archivo).sheet_names
        hoja = st.selectbox("Selecciona una hoja", hojas)
        df = pd.read_excel(archivo, sheet_name=hoja)

elif opcion == "Google Sheets":
    url = st.text_input("Pega el enlace de tu Google Sheet")
    if url and "/d/" in url:
        try:
            sheet_id = url.split("/d/")[1].split("/")[0]
            sh = gc.open_by_key(sheet_id)
            hojas = [ws.title for ws in sh.worksheets()]
            hoja = st.selectbox("Selecciona una hoja", hojas)
            ws = sh.worksheet(hoja)
            df = pd.DataFrame(ws.get_all_records())
        except Exception as e:
            st.error(f"No se pudo cargar: {e}")

if df is not None and not df.empty:
    st.success("✅ Datos cargados correctamente")
    st.dataframe(df.head())

    # Botones inteligentes
    st.subheader("2. Acciones Inteligentes")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📈 Analizar Rentabilidad"):
            pregunta = "¿Cuál es la rentabilidad general de la empresa?"
            csv = df.to_csv(index=False)
            prompt = f"Eres un controller financiero. Analiza la siguiente tabla y responde profesionalmente: {pregunta}\n\nDatos:\n{csv}"
            respuesta = preguntar_deepseek(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col2:
        if st.button("📉 Ver meses con pérdida"):
            pregunta = "¿Cuáles son los meses en que se registraron pérdidas?"
            csv = df.to_csv(index=False)
            prompt = f"Eres un controller financiero. Analiza la siguiente tabla y responde profesionalmente: {pregunta}\n\nDatos:\n{csv}"
            respuesta = preguntar_deepseek(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col3:
        if st.button("💡 Recomendaciones de mejora"):
            pregunta = "¿Qué recomendaciones puedes dar para mejorar la rentabilidad o reducir costos?"
            csv = df.to_csv(index=False)
            prompt = f"Eres un controller financiero. Analiza la siguiente tabla y responde profesionalmente: {pregunta}\n\nDatos:\n{csv}"
            respuesta = preguntar_deepseek(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    # Pregunta libre
    st.subheader("3. Pregunta libre")
    pregunta = st.text_input("Haz una pregunta financiera basada en tus datos")
    if pregunta:
        csv = df.to_csv(index=False)
        prompt = f"Eres un experto financiero. Analiza la siguiente tabla y responde: {pregunta}\n\nDatos:\n{csv}"
        respuesta = preguntar_deepseek(prompt)
        st.markdown("### 💬 Respuesta")
        st.write(respuesta)
        st.session_state["historial"].append((pregunta, respuesta))

    # Gráfico automático
    st.subheader("4. Visualización de Datos")
    columnas_numericas = df.select_dtypes(include=["number"]).columns.tolist()
    columnas_categoria = df.select_dtypes(exclude=["number"]).columns.tolist()

    if columnas_numericas and columnas_categoria:
        colx = st.selectbox("Eje X (categoría)", columnas_categoria)
        coly = st.selectbox("Eje Y (valor numérico)", columnas_numericas)
        tipo = st.selectbox("Tipo de gráfico", ["Barras", "Líneas", "Torta"])

        if tipo == "Barras":
            fig = px.bar(df, x=colx, y=coly)
        elif tipo == "Líneas":
            fig = px.line(df, x=colx, y=coly)
        elif tipo == "Torta":
            fig = px.pie(df, names=colx, values=coly)

        st.plotly_chart(fig)

    # Exportar historial
    st.subheader("5. Historial de conversación")
    if st.button("💾 Exportar historial en CSV"):
        if st.session_state["historial"]:
            historial_df = pd.DataFrame(st.session_state["historial"], columns=["Pregunta", "Respuesta"])
            csv_bytes = historial_df.to_csv(index=False).encode()
            st.download_button("📥 Descargar historial", data=csv_bytes, file_name="historial_controller.csv", mime="text/csv")
        else:
            st.info("Aún no hay historial para exportar.")
