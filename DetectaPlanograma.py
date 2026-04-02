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
# FONDO
# -------------------------
def get_base64(file):
    with open(file, "rb") as f:
        return base64.b64encode(f.read()).decode()

img_base64 = get_base64("fondo.png")

st.markdown(f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: url("data:image/png;base64,{img_base64}");
    background-size: cover;
    background-position: center;
}}

.main, .block-container {{
    background: transparent !important;
}}

.block-container {{
    padding-top: 1rem;
}}

html, body {{
    color: white;
}}

div[data-baseweb="base-input"] {{
    background: transparent !important;
    border: 1px solid rgba(0,255,255,0.6);
    border-radius: 8px;
}}

div[data-baseweb="base-input"] input {{
    background: transparent !important;
    color: white !important;
}}

[data-testid="stFileUploader"] {{
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(0,255,255,0.4);
    border-radius: 10px;
}}

.stButton>button {{
    background: linear-gradient(90deg, #facc15, #00f5ff);
    border-radius: 12px;
    height: 45px;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="margin-top:60px; margin-left:60px;">
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
# INPUTS
# -------------------------
st.markdown('<div style="margin-left:60px; max-width:900px;">', unsafe_allow_html=True)

col1, col2 = st.columns([1,1])

with col1:
    tienda = st.text_input("🏪 Nombre de la tienda")

with col2:
    uploaded_file = st.file_uploader("📸 Subir imagen", type=["jpg","png","jpeg"])

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# BOTÓN ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if uploaded_file is None:
        st.warning("Sube una imagen primero")

    else:

        image = Image.open(uploaded_file).convert("RGB")

        # -------------------------
        # LLAMADA A ROBOFLOW
        # -------------------------
        response = requests.post(
            MODEL_URL,
            params={"api_key": API_KEY},
            files={"file": uploaded_file.getvalue()}
        )

        data = response.json()
        predictions = data.get("predictions", [])

        conteo = len(predictions)

        if predictions:
            productos = [p["class"] for p in predictions]
            producto = pd.Series(productos).value_counts().idxmax()
            confianza = round(sum([p["confidence"] for p in predictions]) / len(predictions), 2)
        else:
            producto = "N/A"
            confianza = 0

        # -------------------------
        # DIBUJAR CAJAS
        # -------------------------
        img = image.copy()
        draw = ImageDraw.Draw(img)

        for p in predictions:
            x, y, w, h = p["x"], p["y"], p["width"], p["height"]
            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2

            draw.rectangle([x1,y1,x2,y2], outline="lime", width=3)

        # -------------------------
        # MOSTRAR RESULTADOS
        # -------------------------
        col1, col2 = st.columns([1.2,1])

        with col1:
            st.image(img, width=420)

        with col2:
            st.markdown(f"""
            <div style="margin-left:70px; margin-top:30px;">

            <p style="color:#9ca3af;">Producto</p>
            <h2 style="color:white; font-size:28px">{producto}</h2>

            <p style="color:#9ca3af;">Total</p>
            <h1 style="color:#facc15;font-size:28px">{conteo}</h1>

            <p style="color:#9ca3af;">Confianza</p>
            <h3 style="color:lime;font-size:18px">{confianza}</h3>

            </div>
            """, unsafe_allow_html=True)

        # -------------------------
        # GUARDAR EN SHEETS
        # -------------------------
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tienda, fecha, producto, conteo])

        st.success("✅ Guardado en Google Sheets")