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
st.set_page_config(page_title="CATEGORY MANAGEMENT - AI Vision System", layout="wide")

# -------------------------
# 🎨 FONDO FUTURISTA
# -------------------------
st.markdown("""
<style>

/* Fondo con imagen IA */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.9)),
    url("https://images.unsplash.com/photo-1677442136019-21780ecad995");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

/* Quitar header blanco */
[data-testid="stHeader"] {
    background: transparent;
}

/* Texto general */
html, body {
    color: white;
}

/* Inputs */
input {
    background-color: rgba(0,0,0,0.6) !important;
    color: white !important;
    border: 1px solid rgba(0,255,255,0.3) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: rgba(0,0,0,0.6);
    border: 1px solid rgba(0,255,255,0.3);
    border-radius: 10px;
    padding: 10px;
}

/* Botón */
.stButton>button {
    background: linear-gradient(90deg, #facc15, #00f5ff);
    color: black;
    font-weight: bold;
    border-radius: 10px;
}

/* Contenedor principal tipo glass */
.block-container {
    background: rgba(0,0,0,0.5);
    padding: 20px;
    border-radius: 15px;
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
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp_service_account"]

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=scope,
)

client = gspread.authorize(creds)

sheet = client.open_by_key("1ulcTkLd4iG36zZYV4wSplQaLmixXdjPlOKPcyeTdAHc").worksheet("Hoja 1")

# -------------------------
# INTERFAZ
# -------------------------
st.markdown("""
<h1 style='color:#00f5ff;'>🤖 AI Vision System</h1>
<p style='color:#9ca3af;'>Smart detection. Real-time insights.</p>
""", unsafe_allow_html=True)

tienda = st.text_input("🏪 Nombre de la tienda")

uploaded_file = st.file_uploader("📸 Sube una imagen", type=["jpg", "png", "jpeg"])

# -------------------------
# PROCESO
# -------------------------
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_column_width=True)

    if st.button("🚀 Analizar"):
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

                st.success(f"Se detectaron {conteo} productos")

                # -------------------------
                # GUARDAR EN GOOGLE SHEETS
                # -------------------------
                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                nueva_fila = [tienda, fecha, conteo]

                sheet.append_row(nueva_fila)

                st.success("✅ Reporte guardado en Google Sheets")

            except Exception as e:
                st.error("❌ Error al guardar en Google Sheets")
                st.write(e)