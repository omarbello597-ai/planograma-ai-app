import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

🔑 CONFIG

API_KEY = "6Ln0uRwFG6fRkoQBO6Oq"
MODEL_URL = "https://detect.roboflow.com/planograma_ai_simz_v1/2"

📊 GOOGLE SHEETS CONFIG

SHEET_ID = "112ZjqVV5EeCIiZIeBrian2KRcyc7I0BMpq3MB8xGr90"

scope = ["https://spreadsheets.google.com/feeds",
"https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(SHEET_ID).sheet1

st.title("📸 Auditoría de Góndola - Simoniz Verde")

🏪 Input tienda

tienda = st.text_input("Nombre de la tienda")

📸 Subir imagen

uploaded_file = st.file_uploader("Sube una foto", type=["jpg", "png"])

if uploaded_file is not None:
st.image(uploaded_file, caption="Imagen subida", use_column_width=True)

if st.button("Analizar"):
    files = {"file": uploaded_file.getvalue()}
    response = requests.post(
        f"{MODEL_URL}?api_key={API_KEY}",
        files=files
    )

    data = response.json()

    if "predictions" in data:
        conteo = len(data["predictions"])
        st.success(f"Productos detectados: {conteo}")

        # 📅 Fecha
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 📥 Guardar en Google Sheets
        sheet.append_row([tienda, fecha, conteo])

        st.success("Guardado en Google Sheets ✅")

    else:
        st.error("Error en detección")
        st.write(data)