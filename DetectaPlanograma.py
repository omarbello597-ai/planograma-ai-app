import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import base64
from io import BytesIO
import time

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# SESSION STATE
# -------------------------
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None

if "image_pil" not in st.session_state:
    st.session_state.image_pil = None

# -------------------------
# MAPEO PRODUCTOS
# -------------------------
MAPEO_PRODUCTOS = {
    "simoniz_verde": "Refrigerante Galón verde Simoniz"
}

# -------------------------
# SCANNER NIVEL NASA 🚀
# -------------------------
def mostrar_scanner_overlay(image, image_placeholder):

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    html = f"""
    <style>
    .container {{
        position: relative;
        width: 350px;
    }}

    .container img {{
        width: 100%;
        border-radius: 10px;
    }}

    .radar {{
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 10px;
        overflow: hidden;
    }}

    /* Círculo radar */
    .radar::before {{
        content: "";
        position: absolute;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 2px solid rgba(0,255,0,0.3);
    }}

    /* Línea de barrido */
    .radar-sweep {{
        position: absolute;
        width: 100%;
        height: 100%;
        background: conic-gradient(
            rgba(0,255,0,0.4) 0deg,
            rgba(0,255,0,0.1) 30deg,
            transparent 60deg
        );
        border-radius: 50%;
        animation: radarRotate 2s linear forwards;
    }}

    /* Glow central */
    .radar::after {{
        content: "";
        position: absolute;
        width: 10px;
        height: 10px;
        background: lime;
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        box-shadow: 0 0 20px lime;
    }}

    @keyframes radarRotate {{
        from {{
            transform: rotate(0deg);
        }}
        to {{
            transform: rotate(360deg);
        }}
    }}
    </style>

    <div class="container">
        <img src="data:image/jpeg;base64,{img_base64}">
        <div class="radar">
            <div class="radar-sweep"></div>
        </div>
    </div>
    """

    image_placeholder.markdown(html, unsafe_allow_html=True)

# -------------------------
# PROCESAR IMAGEN
# -------------------------
def procesar_imagen(uploaded_file):
    try:
        file_bytes = uploaded_file.getvalue()

        if not file_bytes or len(file_bytes) < 1000:
            st.error("⚠️ Error al cargar la imagen")
            return None, None

        image = Image.open(BytesIO(file_bytes))
        image = image.convert("RGB")
        image = image.resize((800, 800))

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)

        return image, buffer.getvalue()

    except Exception as e:
        st.error("❌ Error procesando imagen")
        st.write(e)
        return None, None

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
st.markdown("<h2 style='color:#00f5ff;'>🤖 AI Vision System</h2>", unsafe_allow_html=True)

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
tienda = st.text_input("🏪 Nombre de la tienda")

uploaded_file = st.file_uploader(
    "📸 Toma o sube una foto",
    type=["jpg", "jpeg", "png", "heic", "heif"]
)

# -------------------------
# PROCESAR IMAGEN
# -------------------------
if uploaded_file is not None:

    image, image_bytes = procesar_imagen(uploaded_file)

    if image is not None:
        st.session_state.image_pil = image
        st.session_state.image_bytes = image_bytes

# -------------------------
# PLACEHOLDER
# -------------------------
image_placeholder = st.empty()

if st.session_state.image_pil is not None:
    image_placeholder.image(st.session_state.image_pil, width=350)

# -------------------------
# BOTÓN ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if st.session_state.image_bytes is None:
        st.warning("Sube una imagen primero")

    else:

        # 🚀 SCANNER NIVEL NASA
        mostrar_scanner_overlay(st.session_state.image_pil, image_placeholder)
        time.sleep(2)

        # -------------------------
        # LLAMADA API
        # -------------------------
        response = requests.post(
            MODEL_URL,
            params={"api_key": API_KEY},
            files={
                "file": ("image.jpg", st.session_state.image_bytes, "image/jpeg")
            }
        )

        data = response.json()
        predictions = data.get("predictions", [])

        conteo = len(predictions)

        if conteo > 0:
            productos = [
                MAPEO_PRODUCTOS.get(p["class"], p["class"])
                for p in predictions
            ]
            producto = pd.Series(productos).value_counts().idxmax()

            confianza = round(
                sum([p["confidence"] for p in predictions]) / conteo, 2
            )
        else:
            producto = "No detectado"
            confianza = 0

        # -------------------------
        # DIBUJAR CAJAS
        # -------------------------
        img = st.session_state.image_pil.copy()
        draw = ImageDraw.Draw(img)

        for p in predictions:
            x, y, w, h = p["x"], p["y"], p["width"], p["height"]

            x1, y1 = x - w/2, y - h/2
            x2, y2 = x + w/2, y + h/2

            clase = p["class"]
            nombre = MAPEO_PRODUCTOS.get(clase, clase)

            draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)
            draw.text((x1, y1 - 15), nombre, fill="lime")

        # RESULTADO FINAL
        image_placeholder.image(img, width=350)

        # -------------------------
        # RESULTADOS
        # -------------------------
        st.markdown(f"""
        <div style="margin-left:400px; margin-top:-300px;">

        <p>Producto</p>
        <h3>{producto}</h3>

        <p>Total</p>
        <h1 style="color:#facc15;">{conteo}</h1>

        <p>Confianza</p>
        <h3 style="color:lime;">{confianza}</h3>

        </div>
        """, unsafe_allow_html=True)

        # -------------------------
        # GUARDAR
        # -------------------------
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([tienda, fecha, producto, conteo])

        st.success("✅ Guardado correctamente")