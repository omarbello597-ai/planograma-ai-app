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
    background-position: center;
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
<div style="margin-top:60px; margin-left:60px;">
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
col1, col2 = st.columns([1,1])

with col1:
    tienda = st.text_input("🏪 Nombre de la tienda")

with col2:
    uploaded_file = st.file_uploader("📸 Subir imagen", type=["jpg","png","jpeg"])

# -------------------------
# PREVIEW INMEDIATO
# -------------------------
if uploaded_file is not None:
    st.session_state.imagen = Image.open(uploaded_file).convert("RGB")

if st.session_state.imagen is not None:
    st.image(st.session_state.imagen, width=350)

# -------------------------
# BOTÓN ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if uploaded_file is None:
        st.warning("Sube una imagen primero")

    else:

        image = st.session_state.imagen

        # 🔥 OPCIONAL: reducir tamaño (mejora detección y performance)
        image = image.resize((800, 800))

        # 🔥 FIX ROBUSTO PARA WEB + CELULAR
        response = requests.post(
            MODEL_URL,
            params={"api_key": API_KEY},
            files={"file": ("image.jpg", uploaded_file.getvalue(), "image/jpeg")}
        )

        data = response.json()

        # 🔴 DEBUG (puedes quitar luego)
        st.write("Respuesta del modelo:", data)

        predictions = data.get("predictions")

        if predictions is None:
            st.error("❌ Error en la respuesta del modelo")
            st.stop()

        conteo = len(predictions)

        st.write(f"🔍 Predicciones detectadas: {conteo}")

        if conteo > 0:
            productos = [p["class"] for p in predictions]
            producto = pd.Series(productos).value_counts().idxmax()
            confianza = round(
                sum([p["confidence"] for p in predictions]) / len(predictions), 2
            )
        else:
            producto = "No detectado"
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

            draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)

        # -------------------------
        # RESULTADOS
        # -------------------------
        col1, col2 = st.columns([1.2,1])

        with col1:
            st.image(img, width=350)

        with col2:
            st.markdown(f"""
            <div style="margin-left:60px; line-height:1.2;">

            <p>Producto</p>
            <h2>{producto}</h2>

            <p>Total</p>
            <h1 style="color:#facc15;">{conteo}</h1>

            <p>Confianza</p>
            <h3 style="color:lime;">{confianza}</h3>

            </div>
            """, unsafe_allow_html=True)

        # -------------------------
        # GUARDAR EN SHEETS
        # -------------------------
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tienda, fecha, producto, conteo])

        st.success("✅ Guardado en Google Sheets")