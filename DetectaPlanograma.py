import streamlit as st
import requests
from PIL import Image
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# CONFIGURACIÓN
# -------------------------

API_KEY = "6Ln0uRwFG6fRkoQBO6Oq"
MODEL_URL = "https://detect.roboflow.com/planograma_ai_simz_v1/2"

# -------------------------
# GOOGLE SHEETS CONEXIÓN
# -------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# 👉 Cambia esto por el nombre de tu hoja
sheet = client.open("Reporte_Mercaderistas").sheet1

# -------------------------
# INTERFAZ
# -------------------------

st.title("📸 Detector de Planograma")

tienda = st.text_input("Nombre de la tienda")

uploaded_file = st.file_uploader("Sube una imagen", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_column_width=True)

    if st.button("Analizar"):
        with st.spinner("Analizando..."):

            # Enviar a Roboflow
            response = requests.post(
                MODEL_URL,
                params={"api_key": API_KEY},
                files={"file": uploaded_file.getvalue()}
            )

            data = response.json()

            # Manejo seguro
            predictions = data.get("predictions", [])
            conteo = len(predictions)

            st.success(f"Se detectaron {conteo} productos")

            # -------------------------
            # GUARDAR EN GOOGLE SHEETS
            # -------------------------

            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            nueva_fila = [tienda, fecha, conteo]

            sheet.append_row(nueva_fila)

            st.success("Reporte guardado en Google Sheets ✅")