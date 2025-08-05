import streamlit as st
import pandas as pd
import gspread
import openai
import json
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
import openai

# Autenticación simple
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.image("https://img.icons8.com/fluency/96/lock.png", width=60)
    st.title("Iniciar sesión")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if usuario == "adm" and contraseña == "adm":
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()
import io

# Configuración inicial
# --- TÍTULO ---
st.set_page_config(page_title="Controller Financiero IA", layout="wide")
st.title("📊 Controller Financiero IA")

# Cargar credenciales
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Historial
if "historial" not in st.session_state:
    st.session_state["historial"] = []
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

# Carga de datos
st.subheader("1. Cargar Planilla Financiera")
opcion = st.radio("¿Desde dónde quieres cargar tus datos?", ["Excel", "Google Sheets"])
# --- SUBIDA O CONEXIÓN DE ARCHIVO ---
st.sidebar.header("📂 Cargar datos")
source_type = st.sidebar.radio("Selecciona fuente de datos:", ["Excel", "Google Sheets"])

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

if source_type == "Excel":
    file = st.sidebar.file_uploader("Sube tu archivo Excel", type=["xlsx", "xls"])
    if file:
        df = pd.read_excel(file, sheet_name=None)
elif source_type == "Google Sheets":
    sheet_url = st.sidebar.text_input("Pega el enlace de Google Sheets")
    if sheet_url:
        try:
            sheet_id = url.split("/d/")[1].split("/")[0]
            sh = gc.open_by_key(sheet_id)
            hojas = [ws.title for ws in sh.worksheets()]
            hoja = st.selectbox("Selecciona una hoja", hojas)
            ws = sh.worksheet(hoja)
            df = pd.DataFrame(ws.get_all_records())
            creds = Credentials.from_service_account_info(json.loads(st.secrets["GOOGLE_CREDENTIALS"]))
            client = gspread.authorize(creds)
            sheet_id = sheet_url.split("/d/")[1].split("/")[0]
            spreadsheet = client.open_by_key(sheet_id)
            df = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in spreadsheet.worksheets()}
            st.sidebar.success("Conexión exitosa.")
        except Exception as e:
            st.error(f"No se pudo cargar: {e}")
            st.sidebar.error(f"Error de autenticación: {e}")

if df is not None and not df.empty:
    st.success("✅ Datos cargados correctamente")
    st.dataframe(df.head())
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

    st.subheader("2. Acciones Inteligentes")
    col1, col2, col3 = st.columns(3)
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

    def consultar_openai(pregunta, data):
        try:
            prompt = f"Analiza esta tabla financiera y responde: {pregunta}\n\n{data}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un controller financiero."},
                    {"role": "user", "content": prompt},
                ]
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )
            return response["choices"][0]["message"]["content"]
            respuesta = response.choices[0].message["content"]
            st.success("✅ Análisis completado")
            st.markdown(respuesta)
        except Exception as e:
            return f"⚠️ Error al consultar OpenAI: {e}"

    with col1:
        if st.button("📈 Analizar Rentabilidad"):
            pregunta = "¿Cuál es la rentabilidad general de la empresa?"
            respuesta = consultar_openai(pregunta, df.to_csv(index=False))
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col2:
        if st.button("📉 Ver meses con pérdida"):
            pregunta = "¿Cuáles son los meses con pérdida?"
            respuesta = consultar_openai(pregunta, df.to_csv(index=False))
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col3:
        if st.button("💡 Recomendaciones de mejora"):
            pregunta = "¿Qué recomendaciones das para mejorar la rentabilidad?"
            respuesta = consultar_openai(pregunta, df.to_csv(index=False))
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    # Pregunta libre
    st.subheader("3. Pregunta libre")
    pregunta_libre = st.text_input("Haz una pregunta financiera basada en tus datos")
    if pregunta_libre:
        respuesta = consultar_openai(pregunta_libre, df.to_csv(index=False))
        st.markdown("### 💬 Respuesta")
        st.write(respuesta)
        st.session_state["historial"].append((pregunta_libre, respuesta))

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

            st.error(f"⚠️ Error al consultar OpenAI: {e}")
