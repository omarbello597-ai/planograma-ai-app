import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import base64

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# FONDO (TU IMAGEN)
# -------------------------
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64("fondo.png")

# -------------------------
# CSS COMPLETO (TODO JUNTO)
# -------------------------
st.markdown(f"""
<style>

/* 🌌 FONDO */
[data-testid="stAppViewContainer"] {{
    background: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

/* ❌ ELIMINAR CAPAS GRISES */
.main {{
    background-color: transparent !important;
}}

.block-container {{
    background-color: transparent !important;
    padding: 2rem;
}}

[data-testid="stHeader"] {{
    background: transparent;
}}

/* TEXTO */
html, body {{
    color: white;
}}

/* INPUT TRANSPARENTE */
div[data-baseweb="input"] > div {{
    background-color: transparent !important;
}}

div[data-baseweb="input"] input {{
    background-color: transparent !important;
    color: white !important;
}}

/* BORDE INPUT */
div[data-baseweb="input"] {{
    border: 1px solid rgba(0,255,255,0.5);
    border-radius: 8px;
}}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {{
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(0,255,255,0.4);
    border-radius: 10px;
}}

/* BOTÓN */
.stButton>button {{
    background: linear-gradient(90deg, #facc15, #00f5ff);
    border-radius: 10px;
    height: 40px;
}}

/* SCANNER */
.scan-container {{
    position: relative;
    display: inline-block;
}}

.scan-line {{
    position: absolute;
    width: 100%;
    height: 3px;
    background: lime;
    box-shadow: 0 0 15px lime;
    animation: scan 2s infinite linear;
}}

@keyframes scan {{
    0% {{ top: 0%; }}
    100% {{ top: 100%; }}
}}

</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="margin-top:120px; margin-left:40px;">
<h2 style='color:#00f5ff;'>🤖 Category Management - AI Vision System</h2>
<p style='color:#9ca3af;'>Smart detection. Real-time insights.</p>
</div>
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
# INPUTS (ALINEADOS)
# -------------------------
st.markdown('<div style="margin-left:40px; max-width:900px;">', unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

with col1:
    tienda = st.text_input("🏪 Tienda")

with col2:
    uploaded_file = st.file_uploader("📸 Imagen", type=["jpg","png","jpeg"])

st.markdown('</div>', unsafe_allow_html=True)

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
        label = p["class"]

        x1 = x - w/2
        y1 = y - h/2
        x2 = x + w/2
        y2 = y + h/2

        draw.rectangle([x1,y1,x2,y2], outline="lime", width=3)
        draw.text((x1, y1-10), label, fill="lime")

    return image

# -------------------------
# MAIN
# -------------------------
if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns([1.2,1])

    if st.button("🚀 Analizar"):

        with st.spinner("Analizando..."):

            response = requests.post(
                MODEL_URL,
                params={"api_key": API_KEY},
                files={"file": uploaded_file.getvalue()}
            )

            data = response.json()
            predictions = data.get("predictions", [])
            conteo = len(predictions)

            image_boxes = dibujar_cajas(image.copy(), predictions)

            # IMAGEN + SCANNER
            with col1:
                st.markdown('<div class="scan-container">', unsafe_allow_html=True)
                st.image(image_boxes, width=500)
                st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # RESULTADOS
            with col2:

                if predictions:
                    productos = [p["class"] for p in predictions]
                    producto = pd.Series(productos).value_counts().idxmax()

                    confianza = round(
                        sum([p["confidence"] for p in predictions]) / len(predictions), 2
                    )
                else:
                    producto = "N/A"
                    confianza = 0

                st.markdown(f"""
                <div style="text-align:center;">
                    <p style="color:#9ca3af;">Producto</p>
                    <h2 style="color:#00f5ff;">{producto}</h2>

                    <p style="color:#9ca3af;">Total</p>
                    <h1 style="color:#facc15;">{conteo}</h1>

                    <p style="color:#9ca3af;">Confianza</p>
                    <h3 style="color:lime;">{confianza}</h3>
                </div>
                """, unsafe_allow_html=True)

                fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([tienda, fecha, producto, conteo])

                st.success("✅ Guardado")

    else:
        st.image(image, width=400)