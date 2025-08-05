import streamlit as st
import pandas as pd
import gspread
import json
import plotly.express as px
from google.oauth2.service_account import Credentials
import openai
import io

# Configuración inicial
# ------------------- CONFIGURACIÓN INICIAL -------------------
st.set_page_config(page_title="Controller Financiero IA", layout="wide")
st.title("📊 Controller Financiero IA")

# Autenticación simple
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
# ------------------- LOGIN SIMPLE -------------------
if "logueado" not in st.session_state:
    st.session_state["logueado"] = False

if not st.session_state["autenticado"]:
    st.title("🔐 Iniciar sesión")
if not st.session_state["logueado"]:
    st.image("https://cdn-icons-png.flaticon.com/512/456/456212.png", width=50)
    st.header("Iniciar sesión")
    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if usuario == "adm" and contraseña == "adm":
            st.session_state["autenticado"] = True
            st.success("Inicio de sesión exitoso")
    password = st.text_input("Contraseña", type="password")
    if st.button("🔐 Entrar"):
        if usuario == "adm" and password == "adm":
            st.session_state["logueado"] = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

st.title("📊 Controller Financiero IA")

# Cargar credenciales
# ------------------- CARGA DE CREDENCIALES -------------------
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
gc = gspread.authorize(creds)

openai.api_key = st.secrets["OPENAI_API_KEY"]

# Sesión para historial
# ------------------- FUNCIÓN OPENAI -------------------
def consultar_openai(mensaje_usuario):
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un controller financiero experto."},
                {"role": "user", "content": mensaje_usuario}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error al consultar OpenAI: {e}"

# ------------------- SESIÓN PARA HISTORIAL -------------------
if "historial" not in st.session_state:
    st.session_state["historial"] = []

# Carga de datos
# ------------------- CARGA DE DATOS -------------------
st.subheader("1. Cargar Planilla Financiera")
opcion = st.radio("¿Desde dónde quieres cargar tus datos?", ["Excel", "Google Sheets"])

@@ -68,60 +81,62 @@
        except Exception as e:
            st.error(f"No se pudo cargar: {e}")

# ------------------- FUNCIONALIDAD SI HAY DATOS -------------------
if df is not None and not df.empty:
    st.success("✅ Datos cargados correctamente")
    st.dataframe(df.head())

    # Botones inteligentes
    st.subheader("2. Acciones Inteligentes")
    col1, col2, col3 = st.columns(3)

    def consultar_openai(pregunta, df):
        try:
            csv = df.to_csv(index=False)
            prompt = f"Eres un controller financiero. Analiza la siguiente tabla y responde profesionalmente: {pregunta}\n\nDatos:\n{csv}"
            respuesta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return respuesta.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error al consultar OpenAI: {e}"

    with col1:
        if st.button("📈 Analizar Rentabilidad"):
            pregunta = "¿Cuál es la rentabilidad general de la empresa?"
            respuesta = consultar_openai(pregunta, df)
            csv = df.to_csv(index=False)
            prompt = f"Analiza esta tabla financiera y responde: {pregunta}

{csv}"
            respuesta = consultar_openai(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col2:
        if st.button("📉 Ver meses con pérdida"):
            pregunta = "¿Cuáles son los meses en que se registraron pérdidas?"
            respuesta = consultar_openai(pregunta, df)
            pregunta = "¿Cuáles son los meses con pérdida?"
            csv = df.to_csv(index=False)
            prompt = f"Analiza esta tabla financiera y responde: {pregunta}

{csv}"
            respuesta = consultar_openai(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    with col3:
        if st.button("💡 Recomendaciones de mejora"):
            pregunta = "¿Qué recomendaciones puedes dar para mejorar la rentabilidad o reducir costos?"
            respuesta = consultar_openai(pregunta, df)
            pregunta = "¿Qué recomendaciones financieras darías para mejorar la rentabilidad?"
            csv = df.to_csv(index=False)
            prompt = f"Analiza esta tabla financiera y responde: {pregunta}

{csv}"
            respuesta = consultar_openai(prompt)
            st.markdown("### 💬 Respuesta")
            st.write(respuesta)
            st.session_state["historial"].append((pregunta, respuesta))

    # Pregunta libre
    st.subheader("3. Pregunta libre")
    pregunta = st.text_input("Haz una pregunta financiera basada en tus datos")
    if pregunta:
        respuesta = consultar_openai(pregunta, df)
        csv = df.to_csv(index=False)
        prompt = f"Analiza esta tabla y responde: {pregunta}

{csv}"
        respuesta = consultar_openai(prompt)
        st.markdown("### 💬 Respuesta")
        st.write(respuesta)
        st.session_state["historial"].append((pregunta, respuesta))

    # Gráfico automático
    st.subheader("4. Visualización de Datos")
    columnas_numericas = df.select_dtypes(include=["number"]).columns.tolist()
    columnas_categoria = df.select_dtypes(exclude=["number"]).columns.tolist()
@@ -140,7 +155,6 @@ def consultar_openai(pregunta, df):

        st.plotly_chart(fig)

    # Exportar historial
    st.subheader("5. Historial de conversación")
    if st.button("💾 Exportar historial en CSV"):
        if st.session_state["historial"]:
