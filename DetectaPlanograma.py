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
# SESSION STATE
# -------------------------
if "resultado" not in st.session_state:
    st.session_state.resultado = None

if "imagen" not in st.session_state:
    st.session_state.imagen = None

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
}}

.main, .block-container {{
    background: transparent !important;
}}

[data-testid="stHeader"] {{
    background: transparent;
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
}}

.stButton>button {{
    background: linear-gradient(90deg, #facc15, #00f5ff);
    border-radius: 12px;
    height: 45px;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="margin-top:180px; margin-left:60px;">
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
    tienda = st.text_input("🏪 Tienda")

with col2:
    uploaded_file = st.file_uploader("📸 Imagen", type=["jpg","png","jpeg"])

st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# FUNCION BOXES
# -------------------------
def dibujar_cajas(image, predictions):
    draw = ImageDraw.Draw(image)

    for p in predictions:
        x, y, w, h = p["x"], p["y"], p["width"], p["height"]
        x1, y1 = x - w/2, y - h/2
        x2, y2 = x + w/2, y + h/2

        draw.rectangle([x1,y1,x2,y2], outline="lime", width=3)

    return image

# -------------------------
# BOTON ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if uploaded_file is not None:

        image = Image.open(uploaded_file).convert("RGB")

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

        # guardar estado
        st.session_state.resultado = {
            "conteo": conteo,
            "producto": producto,
            "confianza": confianza,
            "predictions": predictions
        }

        st.session_state.imagen = image

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tienda, fecha, producto, conteo])

# -------------------------
# MOSTRAR RESULTADO SI EXISTE
# -------------------------
if st.session_state.resultado and st.session_state.imagen:

    col1, col2 = st.columns([1.2,1])

    img = dibujar_cajas(
        st.session_state.imagen.copy(),
        st.session_state.resultado["predictions"]
    )

    with col1:
        st.image(img, width=500)

    with col2:
        r = st.session_state.resultado

        st.markdown(f"""
        <div style="text-align:center;">
            <p style="color:#9ca3af;">Producto</p>
            <h2 style="color:#00f5ff;">{r['producto']}</h2>

            <p style="color:#9ca3af;">Total</p>
            <h1 style="color:#facc15;">{r['conteo']}</h1>

            <p style="color:#9ca3af;">Confianza</p>
            <h3 style="color:lime;">{r['confianza']}</h3>
        </div>
        """, unsafe_allow_html=True)

        st.success("✅ Guardado")