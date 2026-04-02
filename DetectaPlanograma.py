import streamlit as st
import requests
from PIL import Image
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# CONFIGURACIÓN PÁGINA
# -------------------------
st.set_page_config(page_title="AI Planogram Detector", layout="wide")

# -------------------------
# CSS FUTURISTA
# -------------------------
st.markdown("""
<style>

/* Fondo general */
body {
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: white;
}

/* Título */
h1 {
    text-align: center;
    font-weight: 700;
    color: #00f5ff;
}

/* Tarjetas tipo glass */
.card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 25px rgba(0,255,255,0.2);
}

/* Métrica grande */
.metric {
    font-size: 60px;
    font-weight: bold;
    color: #00f5ff;
}

/* Botón */
.stButton>button {
    background: linear-gradient(90deg, #00f5ff, #6366f1);
    border: none;
    color: black;
    font-weight: bold;
    border-radius: 10px;
    padding: 10px 20px;
}

/* Inputs */
input {
    background-color: #020617 !important;
    color: white !important;
}

/* Texto centrado */
.center {
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# CONFIGURACIÓN API
# -------------------------
API_KEY = "6Ln0uRwFG6fRkoQBO6Oq"
MODEL_URL = "https://detect.roboflow.com/planograma_ai_simz_v1/2"

# -------------------------
# GOOGLE SHEETS
# -------------------------
creds_dict = st.secrets["gcp_service_account"]

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ],
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1ulcTkLd4iG36zZYV4wSplQaLmixXdjPlOKPcyeTdAHc").worksheet("Hoja 1")

# -------------------------
# HEADER
# -------------------------
st.markdown("<h1>🤖 AI Planogram Analyzer</h1>", unsafe_allow_html=True)

# -------------------------
# INPUTS
# -------------------------
tienda = st.text_input("🏪 Nombre de la tienda")
uploaded_file = st.file_uploader("📸 Sube una imagen", type=["jpg", "png", "jpeg"])

# -------------------------
# PROCESO PRINCIPAL
# -------------------------
if uploaded_file is not None:
    image = Image.open(uploaded_file)

    col1, col2 = st.columns([1.5, 1])

    # -------------------------
    # IMAGEN
    # -------------------------
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image(image, caption="📸 Imagen cargada", use_column_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------------------
    # RESULTADOS
    # -------------------------
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if st.button("🚀 Analizar Imagen"):

            if tienda == "":
                st.warning("⚠️ Ingresa el nombre de la tienda")
            else:
                with st.spinner("🧠 Analizando con IA..."):

                    try:
                        # Enviar a Roboflow
                        response = requests.post(
                            MODEL_URL,
                            params={"api_key": API_KEY},
                            files={"file": uploaded_file.getvalue()}
                        )

                        data = response.json()
                        predictions = data.get("predictions", [])
                        conteo = len(predictions)

                        # Obtener tipos de producto detectados
                        if len(predictions) > 0:
                            productos = [p["class"] for p in predictions]
                            conteo_por_producto = pd.Series(productos).value_counts()
                            producto_principal = conteo_por_producto.idxmax()
                        else:
                            producto_principal = "No identificado"

                        # -------------------------
                        # VISUAL RESULTADO
                        # -------------------------
                        st.markdown(f"""
                            <div class="center">
                                <p>Producto detectado</p>
                                <h2 style="color:#6366f1;">{producto_principal}</h2>
                                <p>Total detectado</p>
                                <div class="metric">{conteo}</div>
                            </div>
                        """, unsafe_allow_html=True)

                        # Mostrar detalle por producto
                        if len(predictions) > 0:
                            st.write("### 📊 Detalle por producto")
                            st.dataframe(conteo_por_producto)

                        # -------------------------
                        # GUARDAR EN GOOGLE SHEETS
                        # -------------------------
                        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        nueva_fila = [tienda, fecha, producto_principal, conteo]

                        sheet.append_row(nueva_fila)

                        st.success("✅ Reporte guardado en Google Sheets")

                    except Exception as e:
                        st.error("❌ Error en el proceso")
                        st.write(e)

        st.markdown('</div>', unsafe_allow_html=True)