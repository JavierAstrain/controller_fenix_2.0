import json
from google.oauth2.service_account import Credentials
from openai import OpenAI
from io import BytesIO
import io

st.set_page_config(layout="wide", page_title="Controller Financiero IA")

@@ -28,8 +28,10 @@ def login():
    login()
    st.stop()

# --- FUNCIONES ---
# --- LAYOUT ---
left, center, right = st.columns([1, 2, 2])

# --- FUNCIONES ---
def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

@@ -50,33 +52,27 @@ def ask_gpt(prompt):
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
def render_graphic(df, tipo, categoria, valor, titulo):
    fig, ax = plt.subplots()
    resumen.plot(kind="barh", ax=ax)
    ax.set_title(titulo)
    ax.set_xlabel(col_valor)
    st.pyplot(fig)
    agrupado = df.groupby(categoria)[valor].sum()

def mostrar_tabla(df, col_categoria, col_valor):
    resumen = df.groupby(col_categoria)[col_valor].sum().reset_index()
    st.markdown("### 📊 Tabla Resumen")
    st.dataframe(resumen)
    if tipo == "torta":
        ax.pie(agrupado, labels=agrupado.index, autopct='%1.1f%%')
        ax.set_title(titulo)
    elif tipo == "barra":
        agrupado.plot(kind="bar", ax=ax)
        ax.set_title(titulo)
        ax.set_ylabel(valor)
        ax.set_xlabel(categoria)

# --- INTERFAZ EN COLUMNAS ---
col1, col2, col3 = st.columns([1, 2, 1])
data = None
    st.pyplot(fig)

with col1:
# --- PANEL IZQUIERDO: CARGA DE DATOS ---
with left:
    st.markdown("### 📁 Subir archivo")
    tipo_fuente = st.radio("Fuente de datos", ["Excel", "Google Sheets"])
    data = None

    if tipo_fuente == "Excel":
        file = st.file_uploader("Sube un archivo Excel", type=["xlsx", "xls"])
        if file:
@@ -86,53 +82,48 @@ def mostrar_tabla(df, col_categoria, col_valor):
        if url and st.button("Conectar"):
            data = load_gsheet(st.secrets["GOOGLE_CREDENTIALS"], url)

with col2:
# --- PANEL CENTRAL: VISTA DE DATOS ---
with center:
    if data:
        st.markdown("### 📄 Vista previa")
        st.markdown("### 📊 Vista previa de datos")
        for name, df in data.items():
            st.markdown(f"#### 📘 Hoja: {name}")
            st.markdown(f"#### 📄 Hoja: {name}")
            st.dataframe(df.head(10))

with col3:
    if data:
        st.markdown("### 🤖 Consulta con IA")
        pregunta = st.text_area("Pregunta")
        if st.button("Responder") and pregunta:
            contenido = ""
            for name, df in data.items():
                contenido += f"Hoja: {name}\n{df.head(50).to_string(index=False)}\n\n"

            prompt = (
                "Eres un controller financiero experto. Analiza los siguientes datos de un taller "
                "de desabolladura y pintura de vehículos livianos y pesados:\n\n"
                f"{contenido}\n"
                f"Pregunta: {pregunta}\n\n"
                "Responde con análisis detallado y genera instrucciones de visualización si es útil.\n"
                "Si deseas un gráfico, usa el formato: grafico_torta:columna_categoria|columna_valor|titulo\n"
                "Para gráfico de barras usa: grafico_barras:columna_categoria|columna_valor|titulo\n"
                "Para una tabla usa: tabla:columna_categoria|columna_valor"
            )

            respuesta = ask_gpt(prompt)
            st.markdown(respuesta)

            # Procesar visualizaciones
            for linea in respuesta.splitlines():
                if "grafico_torta:" in linea:
                    partes = linea.replace("grafico_torta:", "").split("|")
                    if len(partes) == 3:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_grafico_torta(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
                if "grafico_barras:" in linea:
                    partes = linea.replace("grafico_barras:", "").split("|")
                    if len(partes) == 3:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_grafico_barras(df, partes[0].strip(), partes[1].strip(), partes[2].strip())
                if "tabla:" in linea:
                    partes = linea.replace("tabla:", "").split("|")
                    if len(partes) == 2:
                        for hoja, df in data.items():
                            if partes[0].strip() in df.columns and partes[1].strip() in df.columns:
                                mostrar_tabla(df, partes[0].strip(), partes[1].strip())
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
