import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import base64
from io import BytesIO
import time
import io

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
# SUBIR A DRIVE (FIX FINAL 🔥)
# -------------------------
def subir_imagen_drive(image_pil, nombre_archivo):
    try:
        drive_service = build('drive', 'v3', credentials=creds)

        img_bytes = io.BytesIO()
        image_pil.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        # 🔥 PON AQUÍ TU ID DE CARPETA
        FOLDER_ID = "1zepZlzuhfCBMy3xUrLDduSRiOV350tf_"

        file_metadata = {
            'name': nombre_archivo,
            'parents': [FOLDER_ID]
        }

        media = MediaIoBaseUpload(img_bytes, mimetype='image/jpeg')

        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    except Exception as e:
        st.error(f"Error subiendo imagen a Drive: {e}")
        return None

# -------------------------
# SCANNER VISUAL
# -------------------------
def mostrar_scanner_overlay(image, image_placeholder):
    image_placeholder.image(image, width=350)

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
# CONFIG MODELO (AJUSTA SI CAMBIA)
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

        # -------------------------
        # GUARDAR
        # -------------------------
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{tienda}_{fecha}.jpg"

        # 🔥 Guarda imagen con detecciones
        file_id = subir_imagen_drive(img, nombre_archivo)

        link = f"https://drive.google.com/uc?id={file_id}" if file_id else ""

        sheet.append_row([
            tienda,
            fecha,
            producto,
            conteo,
            mercaderista,
            link
        ])

        st.success("✅ Guardado correctamente con imagen 🚀")
