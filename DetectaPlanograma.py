import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# CONFIG PAGE
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# 🎨 CSS FUTURISTA (HUD)
# -------------------------
st.markdown("""
<style>

/* 🌌 Fondo */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at center, #020617 0%, #000000 100%);
    background-image: 
        linear-gradient(rgba(0,255,255,0.08) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,255,0.08) 1px, transparent 1px);
    background-size: 40px 40px;
}

/* Header */
[data-testid="stHeader"] {
    background: transparent;
}

/* Texto */
html, body {
    color: white;
}

/* Título */
.title {
    font-size: 48px;
    font-weight: 700;
    background: linear-gradient(90deg, #00f5ff, #facc15);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.subtitle {
    color: #9ca3af;
}

/* Inputs */
input {
    background: rgba(0,0,0,0.6) !important;
    border: 1px solid rgba(0,255,255,0.3) !important;
    color: white !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(0,0,0,0.6);
    border: 1px solid rgba(0,255,255,0.3);
    border-radius: 10px;
}

/* Botón */
.stButton>button {
    background: linear-gradient(90deg, #facc15, #00f5ff);
    color: black;
    font-weight: bold;
    border-radius: 25px;
    box-shadow: 0 0 20px rgba(0,255,255,0.5);
}

/* Card HUD */
.hud-card {
    background: rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(0,255,255,0.3);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 0 30px rgba(0,255,255,0.2);
}

/* Imagen marco */
.image-frame {
    padding: 10px;
    border-radius: 15px;
    border: 2px solid rgba(0,255,255,0.4);
    box-shadow: 
        0 0 20px rgba(0,255,255,0.3),
        inset 0 0 20px rgba(0,255,255,0.2);
}

/* Scan */
.scan-line {
    position: absolute;
    width: 100%;
    height: 2px;
    background: #00f5ff;
    animation: scan 2s infinite linear;
}

@keyframes scan {
    0% { top: 0%; }
    100% { top: 100%; }
}

/* Métrica */
.metric {
    font-size: 70px;
    font-weight: bold;
    background: linear-gradient(90deg, #facc15, #00f5ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
colH1, colH2 = st.columns([1,1])

with colH1:
    st.markdown("""
        <div class="title">AI Vision System</div>
        <div class="subtitle">Smart detection. Real-time insights.</div>
    """, unsafe_allow_html=True)

with colH2:
    st.image("https://images.unsplash.com/photo-1677442136019-21780ecad995", width=350)

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

    with col1:

        st.markdown('<div class="hud-card">', unsafe_allow_html=True)

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

                st.markdown('<div class="image-frame">', unsafe_allow_html=True)
                st.markdown('<div style="position:relative">', unsafe_allow_html=True)

                st.image(image_boxes, width=550)

                st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)
                st.markdown('</div></div>', unsafe_allow_html=True)

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
                    <div style="text-align:center">
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

        st.markdown('</div>', unsafe_allow_html=True)