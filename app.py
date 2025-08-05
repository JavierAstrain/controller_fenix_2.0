import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import openai
import json
import io
from google.oauth2 import service_account
import gspread
from googleapiclient.discovery import build

st.set_page_config(page_title="Controller Financiero IA", layout="wide")

# Login simple
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Controller Financiero IA")
    st.subheader("Iniciar sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if username == "adm" and password == "adm":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Credenciales incorrectas")
    st.stop()

st.title("📊 Controller Financiero IA")

# Subir archivo Excel o conectar Google Sheet
fuente_datos = st.radio("Fuente de datos:", ["Excel", "Google Sheets"])
df = None

if fuente_datos == "Excel":
    archivo = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])
    if archivo:
        excel = pd.read_excel(archivo, sheet_name=None)
        st.success("Archivo cargado correctamente.")
elif fuente_datos == "Google Sheets":
    url = st.text_input("Pega la URL de tu Google Sheet")
    if url:
        try:
            creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
            creds = service_account.Credentials.from_service_account_info(creds_dict)
            gc = gspread.authorize(creds)
            sheet_id = url.split("/d/")[1].split("/")[0]
            sh = gc.open_by_key(sheet_id)
            excel = {ws.title: pd.DataFrame(ws.get_all_records()) for ws in sh.worksheets()}
            st.success("Google Sheet conectado correctamente.")
        except Exception as e:
            st.error(f"Error al conectar Google Sheets: {e}")
            st.stop()

# Mostrar hojas
if 'excel' in locals():
    hoja = st.selectbox("Selecciona una hoja para visualizar", list(excel.keys()))
    df = excel[hoja]
    st.dataframe(df, use_container_width=True)

# Pregunta a la IA
if df is not None:
    pregunta = st.text_area("Haz una pregunta sobre los datos cargados:")
    if st.button("Responder"):
        try:
            all_dfs_str = "\n\n".join([f"Hoja: {nombre}\n{contenido.to_string(index=False)}" for nombre, contenido in excel.items()])
            prompt = f"""
Actúa como un controller financiero experto en el rubro automotriz de desabolladura y pintura de vehículos pesados y livianos.
Analiza el siguiente libro financiero (múltiples hojas) y responde con precisión, explicaciones claras, gráficos si es necesario y recomendaciones reales.
Datos:
{all_dfs_str}
Pregunta del usuario: {pregunta}
"""
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un controller financiero experto en gestión de talleres automotrices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )
            respuesta = response.choices[0].message.content
            st.markdown("### 🧠 Respuesta")
            st.markdown(respuesta)
        except Exception as e:
            st.error(f"❌ Error al consultar OpenAI: {e}")
