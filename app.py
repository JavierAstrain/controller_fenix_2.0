
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

st.set_page_config(page_title="Controller Financiero Fénix", layout="wide")

st.title("🤖 Controller Financiero Inteligente")
st.markdown("Este sistema analiza tus datos financieros y responde como un experto en gestión y control financiero del taller.")

@st.cache_data
def load_excel(file):
    return pd.read_excel(file, sheet_name=None)

def analizar_contexto_y_mostrar(tabla, tipo):
    fig, ax = plt.subplots()
    if tipo == "torta":
        ax.pie(tabla.iloc[:, 1], labels=tabla.iloc[:, 0], autopct="%1.1f%%", startangle=90)
        ax.set_title("Distribución del Monto Principal Neto por Tipo de Cliente")
        st.pyplot(fig)
    elif tipo == "barras":
        ax.bar(tabla.iloc[:, 0], tabla.iloc[:, 1])
        ax.set_ylabel("Monto")
        ax.set_title("Comparativa por Categoría")
        st.pyplot(fig)
    elif tipo == "linea":
        ax.plot(tabla.iloc[:, 0], tabla.iloc[:, 1], marker="o")
        ax.set_ylabel("Monto")
        ax.set_title("Evolución en el Tiempo")
        plt.xticks(rotation=45)
        st.pyplot(fig)

def responder_como_controller(pregunta, hoja_df):
    if "grafico de torta" in pregunta and "tipo de cliente" in pregunta:
        if "TIPO CLIENTE" in hoja_df.columns and "MONTO PRINCIPAL NETO" in hoja_df.columns:
            resumen = hoja_df.groupby("TIPO CLIENTE")["MONTO PRINCIPAL NETO"].sum().reset_index()
            total = resumen["MONTO PRINCIPAL NETO"].sum()
            mayor = resumen.loc[resumen["MONTO PRINCIPAL NETO"].idxmax()]
            st.markdown(f"""
            ### 📊 Análisis Financiero
            El gráfico de torta muestra la distribución de los ingresos netos según tipo de cliente. El cliente que genera mayor ingreso es **{mayor["TIPO CLIENTE"]}**, con ${mayor["MONTO PRINCIPAL NETO"]:,}, representando un **{(mayor["MONTO PRINCIPAL NETO"]/total*100):.2f}%** del total.

            Se recomienda:
            - Fortalecer relaciones con clientes de tipo **{mayor["TIPO CLIENTE"]}**.
            - Evaluar estrategias de diversificación si un solo tipo representa más del 60% del ingreso.
            """)
            analizar_contexto_y_mostrar(resumen, "torta")
        else:
            st.error("No se encontraron columnas 'TIPO CLIENTE' y 'MONTO PRINCIPAL NETO' en la hoja seleccionada.")
    elif "tabla" in pregunta and ":" in pregunta:
        try:
            hoja, columnas = pregunta.split(":")
            hoja = hoja.strip()
            columnas = [c.strip() for c in columnas.split("|")]
            if hoja in hojas:
                df = hojas[hoja]
                tabla = df[columnas].groupby(columnas[0])[columnas[1]].sum().reset_index()
                st.markdown(f"### 📊 Tabla de {columnas[1]} por {columnas[0]}")
                st.dataframe(tabla)
                analizar_contexto_y_mostrar(tabla, "barras")
            else:
                st.error("La hoja especificada no existe.")
        except Exception as e:
            st.error(f"Error al procesar la tabla: {e}")
    else:
        st.warning("Haz una pregunta más específica relacionada a tus datos, como por ejemplo:
- Hazme un gráfico de torta del monto principal neto por tipo de cliente
- tabla:FACTURACION|TIPO CLIENTE|MONTO PRINCIPAL NETO")

# Subida de archivo
archivo = st.file_uploader("📤 Sube tu archivo Excel", type=["xlsx"])
if archivo:
    hojas = load_excel(archivo)
    hoja_seleccionada = st.selectbox("Selecciona la hoja a analizar", list(hojas.keys()))
    df = hojas[hoja_seleccionada]
    st.markdown("### Vista previa de los datos")
    st.dataframe(df.head(50))

    pregunta = st.text_area("✍️ Escribe tu pregunta financiera", placeholder="Ej: hazme un gráfico de torta del monto principal neto por tipo de cliente")
    if st.button("📊 Analizar"):
        responder_como_controller(pregunta.lower(), df)
