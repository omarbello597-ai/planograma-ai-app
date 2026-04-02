import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# 🎨 CSS CORREGIDO
# -------------------------
st.markdown("""
<style>

/* Fondo NEGRO FORZADO */
html, body, [class*="css"]  {
    background-color: #000000 !important;
    color: white !important;
}

/* Contenedor principal */
[data-testid="stAppViewContainer"] {
    background: #000000 !important;
}

/* Header */
[data-testid="stHeader"] {
    background: transparent;
}

/* Título */
.title {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(90deg, #00f5ff, #facc15);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Inputs */
input {
    background: #0a0a0a !important;
    border: 1px solid rgba(0,255,255,0.3) !important;
    color: white !important;
}

/* Uploader */
[data-testid="stFileUploader"] {
    background: #0a0a0a;
    border: 1px solid rgba(0,255,255,0.3);
}

/* Botón */
.stButton>button {
    background: linear-gradient(90deg, #facc15, #00f5ff);
    color: black;
    font-weight: bold;
    border-radius: 20px;
}

/* Card */
.hud-card {
    background: rgba(0,0,0,0.7);
    border: 1px solid rgba(0,255,255,0.3);
    border-radius: 15px;
    padding: 20px;
}

/* Imagen */
.image-frame {
    border: 2px solid rgba(0,255,255,0.4);
    padding: 10px;
    border-radius: 10px;
}

/* Métrica */
.metric {
    font-size: 70px;
    font-weight: bold;
    color: #facc15;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div class="title">AI Vision System</div>
<p style="color:#9ca3af;">Smart detection. Real-time insights.</p>
""", unsafe_allow_html=True)

# -------------------------
# API
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
# INPUTS
# -------------------------
st.markdown("### 📸 Upload & Analyze")

tienda = st.text_input("Nombre de la tienda")
uploaded_file = st.file_uploader("Sube imagen", type=["jpg","png","jpeg"])

# -------------------------
# FUNCION CAJAS
# -------------------------
def dibujar_cajas(image, predictions):
    draw = ImageDraw.Draw(image)

    for p in predictions:
        x = p["x"]
        y = p["y"]
        w = p["width"]
        h = p["height"]

        x1 = x - w/2
        y1 = y - h/2
        x2 = x + w/2
        y2 = y + h/2

        draw.rectangle([x1,y1,x2,y2], outline="#00f5ff", width=3)

    return image

# -------------------------
# MAIN
# -------------------------
if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns([1.2,1])

    if st.button("Analyze Image"):

        with st.spinner("Analyzing..."):

            response = requests.post(
                MODEL_URL,
                params={"api_key": API_KEY},
                files={"file": uploaded_file.getvalue()}
            )

            data = response.json()
            predictions = data.get("predictions", [])
            conteo = len(predictions)

            image_boxes = dibujar_cajas(image.copy(), predictions)

            # -------------------------
            # IMAGEN
            # -------------------------
            with col1:
                st.markdown('<div class="image-frame">', unsafe_allow_html=True)
                st.image(image_boxes, width=550)
                st.markdown('</div>', unsafe_allow_html=True)

            # -------------------------
            # RESULTADOS
            # -------------------------
            with col2:
                st.markdown('<div class="hud-card">', unsafe_allow_html=True)

                if predictions:
                    productos = [p["class"] for p in predictions]
                    conteo_por_producto = pd.Series(productos).value_counts()
                    producto = conteo_por_producto.idxmax()

                    confianza = round(
                        sum([p["confidence"] for p in predictions]) / len(predictions), 2
                    )
                else:
                    producto = "N/A"
                    confianza = 0

                st.markdown(f"""
                <div style="text-align:center;">
                    <p style="color:#9ca3af;">Detected Product</p>
                    <h2 style="color:#00f5ff;">{producto}</h2>

                    <p style="color:#9ca3af;">Total</p>
                    <div class="metric">{conteo}</div>

                    <p style="color:#9ca3af;">Confidence</p>
                    <h3 style="color:#facc15;">{confianza}</h3>
                </div>
                """, unsafe_allow_html=True)

                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([tienda, fecha, producto, conteo])

                st.success("Saved")

                st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.image(image, width=500)