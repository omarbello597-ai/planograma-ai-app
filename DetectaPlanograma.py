import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_KEY = "6Ln0uRwFG6fRkoQBO6Oq"
MODEL_URL = "https://detect.roboflow.com/planograma_ai_simz_v1/2"

st.title("📸 Auditoría de Góndola - Simoniz Verde")

#🏪 Input tienda

tienda = st.text_input("Nombre de la tienda")

#📸 Subir imagen

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
    conteo = len(data["predictions"])

    st.success(f"Productos detectados: {conteo}")

    # 📊 Guardar resultado
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame([{
        "tienda": tienda,
        "fecha": fecha,
        "productos_detectados": conteo
    }])

    df.to_csv("reporte.csv", mode='a', header=False, index=False)

    st.success("Guardado en reporte ✅")
