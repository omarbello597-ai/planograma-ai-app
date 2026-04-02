import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import base64

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

html, body {{
    color: white;
}}
</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER
# -------------------------
st.markdown("""
<div style="margin-top:150px; margin-left:60px;">
<h2 style='color:#00f5ff;'>🤖 Category Management - AI Vision System</h2>
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
col1, col2 = st.columns(2)

with col1:
    tienda = st.text_input("Tienda")

with col2:
    uploaded_file = st.file_uploader("Imagen", type=["jpg","png","jpeg"])

# -------------------------
# BOTÓN (SOLO PROCESA)
# -------------------------
if st.button("Analizar"):

    if uploaded_file is None:
        st.warning("Sube una imagen primero")
    else:

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

        # GUARDAR ESTADO
        st.session_state.resultado = {
            "conteo": conteo,
            "producto": producto,
            "confianza": confianza,
            "predictions": predictions
        }

        st.session_state.imagen = image

        # GUARDAR EN SHEET
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tienda, fecha, producto, conteo])

        st.success("Guardado")

# -------------------------
# 🔥 MOSTRAR RESULTADOS SIEMPRE
# -------------------------
if st.session_state.resultado:

    col1, col2 = st.columns(2)

    # Imagen
    with col1:
        img = st.session_state.imagen.copy()
        draw = ImageDraw.Draw(img)

        for p in st.session_state.resultado["predictions"]:
            x, y, w, h = p["x"], p["y"], p["width"], p["height"]
            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2

            draw.rectangle([x1,y1,x2,y2], outline="lime", width=3)

        st.image(img, width=500)

    # Resultado
    with col2:
        r = st.session_state.resultado

        st.markdown(f"""
<div style="
    text-align:left;
    margin-left:60px;
    margin-top:40px;
">

<p style="color:#9ca3af; font-size:14px;">Producto</p>
<h2 style="color:white;">{r['producto']}</h2>

<p style="color:#9ca3af; font-size:14px;">Total</p>
<h1 style="color:#facc15;">{r['conteo']}</h1>

<p style="color:#9ca3af; font-size:14px;">Confianza</p>
<h3 style="color:lime;">{r['confianza']}</h3>

</div>
""", unsafe_allow_html=True)