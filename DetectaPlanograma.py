import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import base64
from io import BytesIO

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
# FUNCIÓN PROCESAMIENTO (🔥 CLAVE)
# -------------------------
def procesar_imagen(uploaded_file):

    try:
        file_bytes = uploaded_file.getvalue()

        # Validar archivo
        if not file_bytes or len(file_bytes) < 1000:
            st.error("⚠️ Error al cargar la imagen. Intenta nuevamente.")
            return None, None

        image = Image.open(BytesIO(file_bytes))

        # 🔥 Convertir SIEMPRE
        image = image.convert("RGB")

        # 🔥 Redimensionar (clave móvil)
        image = image.resize((800, 800))

        # 🔥 Convertir a JPEG optimizado
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
st.markdown("""
<div style="margin-top:40px;">
<h2 style='color:#00f5ff;'>🤖 AI Vision System</h2>
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
tienda = st.text_input("🏪 Nombre de la tienda")

uploaded_file = st.file_uploader(
    "📸 Toma o sube una foto",
    type=["jpg", "jpeg", "png", "heic", "heif"]
)

# -------------------------
# PROCESAR Y GUARDAR IMAGEN
# -------------------------
if uploaded_file is not None:

    image, image_bytes = procesar_imagen(uploaded_file)

    if image is not None:
        st.session_state.image_pil = image
        st.session_state.image_bytes = image_bytes

# -------------------------
# PREVIEW (SIEMPRE)
# -------------------------
if st.session_state.image_pil is not None:
    st.image(st.session_state.image_pil, width=350)

# -------------------------
# BOTÓN ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if st.session_state.image_bytes is None:
        st.warning("Sube una imagen primero")

    else:

        with st.spinner("Analizando imagen..."):

            try:
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
                    productos = [p["class"] for p in predictions]
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
                    draw.rectangle([x1, y1, x2, y2], outline="lime", width=3)

                # -------------------------
                # RESULTADOS
                # -------------------------
                st.image(img, width=350)

                st.markdown(f"""
                <div style="line-height:1.2;">

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

            except Exception as e:
                st.error("❌ Error en análisis")
                st.write(e)