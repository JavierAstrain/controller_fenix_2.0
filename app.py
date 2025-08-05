import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import gspread
import json
from io import BytesIO
from openai import OpenAI
from google.oauth2.service_account import Credentials

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
with st.sidebar:
    st.markdown("### 📁 Subir archivo")
    tipo_fuente = st.radio("Fuente de datos", ["Excel", "Google Sheets"])
    data = None

    if tipo_fuente == "Excel":
        file = st.file_uploader("Sube un archivo Excel", type=["xlsx", "xls"])
        if file:
            data = pd.read_excel(file, sheet_name=None)
    else:
        url = st.text_input("URL de Google Sheet")
        if url and st.button("Conectar"):
            creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
            scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
            client = gspread.authorize(creds)
            sheet = client.open_by_url(url)
            data = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in sheet.worksheets()}

# --- FUNCIONES ---
def ask_openai(prompt):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content

def generar_grafico_torta(df, columna, valores):
    resumen = df.groupby(columna)[valores].sum()
    fig, ax = plt.subplots()
    resumen.plot.pie(ax=ax, autopct='%1.1f%%')
    ax.set_ylabel("")
    ax.set_title(f"Distribución de {valores} por {columna}")
    st.pyplot(fig)

def generar_tabla(df, columnas):
    st.markdown("#### 📋 Tabla generada automáticamente")
    st.dataframe(df[columns])

# --- VISUALIZACIÓN CENTRAL ---
if data:
    st.markdown("### 📊 Vista previa de datos")
    for nombre, df in data.items():
        st.markdown(f"#### 🧾 Hoja: {nombre}")
        st.dataframe(df.head(15))

# --- CONSULTAS CON IA ---
st.markdown("### 🤖 Consultas al Controller Financiero IA")
pregunta = st.text_area("Haz una pregunta específica (ej. '¿Cuál es el ingreso mensual promedio por tipo de cliente?')")
if st.button("Responder") and pregunta and data:
    st.markdown("#### 💬 Respuesta del Controller Financiero IA")

    contenido = ""
    for name, df in data.items():
        contenido += f"\nHoja: {name}\n"
        contenido += df.head(50).to_string(index=False)

    prompt = (
        "Actúa como un controller financiero experto en talleres de desabolladura y pintura de vehículos pesados y livianos.\n"
        "Con base en los siguientes datos cargados desde un libro Excel/Google Sheets, responde de manera profesional, detallada y útil para la toma de decisiones.\n"
        "Puedes generar gráficos de torta, barras, líneas y tablas si consideras que ayudan al análisis. También entrega recomendaciones claras.\n"
        f"\n\n{contenido}\n\n"
        f"Consulta: {pregunta}\n"
        "Responde directamente con base en los datos. Si es útil, entrega un gráfico automáticamente."
    )

    try:
        respuesta = ask_openai(prompt)
        st.markdown(respuesta)
        # Aquí puedes analizar si el modelo sugiere un gráfico o tabla y ejecutarlo si es posible (requiere más parsing si quieres automatizarlo completamente)
    except Exception as e:
        st.error(f"❌ Error al consultar OpenAI: {e}")

