import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
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

# --- LAYOUT EN COLUMNAS ---
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

# --- MOSTRAR TABLAS ---
st.markdown("### 📊 Vista previa de datos")
if data:
    for name, df in data.items():
        st.markdown(f"#### 🧾 Hoja: {name}")
        st.dataframe(df.head(10))

# --- CONSULTAS CON IA ---
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
        "Responde con análisis detallado, gráfico si es útil, y una tabla si aplica. "
        "Sé profesional, claro y enfocado en decisiones estratégicas. Si detectas columnas categóricas con montos o cantidades, puedes generar automáticamente un gráfico. "
        "Si detectas comparaciones que se pueden mostrar como tabla, crea una con pandas."
    )

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    respuesta = response.choices[0].message.content
    st.markdown("#### 💬 Respuesta de IA")
    st.markdown(respuesta)

    # INTENTA DETECTAR TABLAS
    if "|" in respuesta:
        try:
            import io
            df_table = pd.read_csv(io.StringIO(respuesta), sep="|")
            st.markdown("#### 📋 Tabla generada")
            st.dataframe(df_table)
        except Exception:
            pass

    # GRAFICO AUTOMÁTICO SI DETECTA CLAVES
    if "grafico de torta" in respuesta.lower():
        for name, df in data.items():
            posibles_columnas = [c for c in df.columns if df[c].nunique() < 20 and df[c].dtype == object]
            posibles_valores = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if posibles_columnas and posibles_valores:
                col_cat = posibles_columnas[0]
                col_val = posibles_valores[0]
                resumen = df.groupby(col_cat)[col_val].sum()
                fig, ax = plt.subplots()
                resumen.plot.pie(autopct='%1.1f%%', ax=ax)
                ax.set_ylabel("")
                ax.set_title(f"Distribución de {col_val} por {col_cat}")
                st.pyplot(fig)
                break
