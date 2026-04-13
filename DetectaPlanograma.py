import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader
from io import BytesIO
import time
import io

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# CLOUDINARY CONFIG 🔥
# -------------------------
cloudinary.config(
    cloud_name="dax3fphba",
    api_key="382884411682566",
    api_secret="zemqZpfISOWypf6JzA1RM_wps7Q"
)

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
# PROCESAR IMAGEN
# -------------------------
def procesar_imagen(uploaded_file):
    try:
        image = Image.open(uploaded_file).convert("RGB")
        img_bytes = BytesIO()
        image.save(img_bytes, format="JPEG")
        return image, img_bytes.getvalue()
    except:
        return None, None

# -------------------------
# SUBIR A CLOUDINARY 🚀
# -------------------------
def subir_imagen_cloudinary(image_pil, nombre_archivo):
    try:
        img_bytes = io.BytesIO()
        image_pil.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        response = cloudinary.uploader.upload(
            img_bytes,
            public_id=nombre_archivo
        )

        return response['secure_url']

    except Exception as e:
        st.error(f"Error subiendo imagen: {e}")
        return None

# -------------------------
# SCANNER VISUAL
# -------------------------
# def mostrar_scanner_overlay(image, image_placeholder):
 #   image_placeholder.image(image, width=350)
def mostrar_scanner_overlay(image, image_placeholder):
    import base64
    from io import BytesIO
    import streamlit.components.v1 as components

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    html = f"""
    <div style="position: relative; width: 350px;">
        <img src="data:image/jpeg;base64,{img_base64}" 
             style="width:100%; border-radius:10px; display:block;"/>

        <div style="
            position:absolute;
            top:0;
            left:0;
            width:100%;
            height:100%;
            border-radius:10px;
            overflow:hidden;
        ">

            <div style="
                position:absolute;
                width:100%;
                height:100%;
                background: radial-gradient(circle, rgba(0,255,0,0.25) 0%, transparent 70%);
                animation: pulse 1.5s infinite;
            "></div>

            <div style="
                position:absolute;
                top:0;
                left:0;
                width:100%;
                height:4px;
                background: linear-gradient(90deg, transparent, #00ff00, transparent);
                animation: scan 2s linear infinite;
            "></div>

        </div>
    </div>

    <style>
    @keyframes scan {{
        0% {{ top: 0%; }}
        100% {{ top: 100%; }}
    }}

    @keyframes pulse {{
        0% {{ opacity: 0.2; }}
        50% {{ opacity: 0.9; }}
        100% {{ opacity: 0.2; }}
    }}
    </style>
    """

    components.html(html, height=350)


# -------------------------
# GOOGLE SHEETS
# -------------------------
creds_dict = st.secrets["gcp_service_account"]

creds = Credentials.from_service_account_info(
    creds_dict,
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets"
    ],
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1ulcTkLd4iG36zZYV4wSplQaLmixXdjPlOKPcyeTdAHc").worksheet("Hoja 1")

# -------------------------
# INPUTS
# -------------------------
tienda = st.text_input("🏪 Nombre de la tienda")
mercaderista = st.text_input("👤 Nombre del mercaderista")

uploaded_file = st.file_uploader(
    "📸 Toma o sube una foto",
    type=["jpg", "jpeg", "png"]
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
# CONFIG MODELO
# -------------------------
MODEL_URL = "https://detect.roboflow.com/planograma_ai_simz_v1/2"
API_KEY = "6Ln0uRwFG6fRkoQBO6Oq"

# -------------------------
# BOTÓN ANALIZAR
# -------------------------
if st.button("🚀 Analizar"):

    if st.session_state.image_bytes is None:
        st.warning("Sube una imagen primero")

    else:

        mostrar_scanner_overlay(st.session_state.image_pil, image_placeholder)
        time.sleep(1)

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

        image_placeholder.image(img, width=350)
        st.success(f"🔍 Se detectaron {conteo} Refrigerantes verdes Simoniz")


        # -------------------------
        # GUARDAR
        # -------------------------
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{tienda}_{fecha}"

        # 🔥 Subir a Cloudinary
        link = subir_imagen_cloudinary(img, nombre_archivo)

        sheet.append_row([
            tienda,
            fecha,
            producto,
            conteo,
            mercaderista,
            link
        ])

        st.success("✅ Guardado correctamente con imagen 🚀")
