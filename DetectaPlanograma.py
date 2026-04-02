import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import io

# -------------------------
# CONFIGURACIÓN PÁGINA
# -------------------------
st.set_page_config(page_title="AI Planogram Detector", layout="wide")

# -------------------------
# CSS FUTURISTA + SCAN
# -------------------------
st.markdown("""
<style>

/* Fondo futurista real */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 20% 20%, #0f172a, #020617 60%);
}

/* Quitar blanco */
[data-testid="stHeader"] {
    background: transparent;
}

/* Título */
h1 {
    text-align: center;
    color: #00f5ff;
}

/* Cards */
.card {
    background: rgba(255,255,255,0.04);
    border-radius: 20px;
    padding: 20px;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(0,255,255,0.2);
    box-shadow: 0 0 30px rgba(0,255,255,0.15);
}

/* Métrica */
.metric {
    font-size: 60px;
    font-weight: bold;
    color: #00f5ff;
    text-shadow: 0 0 20px rgba(0,255,255,0.7);
}

/* Botón */
.stButton>button {
    background: linear-gradient(90deg, #00f5ff, #6366f1);
    border: none;
    color: black;
    font-weight: bold;
    border-radius: 10px;
}

/* Scan effect */
.scan-container {
    position: relative;
}

.scan-line {
    position: absolute;
    width: 100%;
    height: 3px;
    background: rgba(0,255,255,0.8);
    box-shadow: 0 0 15px #00f5ff;
    animation: scan 2.5s infinite linear;
}

@keyframes scan {
    0% { top: 0%; }
    100% { top: 100%; }
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# CONFIG API
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
# HEADER
# -------------------------
st.markdown("<h1>🤖 AI Planogram Analyzer</h1>", unsafe_allow_html=True)

# -------------------------
# INPUTS
# -------------------------
tienda = st.text_input("🏪 Nombre de la tienda")
uploaded_file = st.file_uploader("📸 Sube una imagen", type=["jpg", "png", "jpeg"])

# -------------------------
# FUNCIÓN DIBUJAR CAJAS
# -------------------------
def dibujar_cajas(image, predictions):
    draw = ImageDraw.Draw(image)

    for p in predictions:
        x = p["x"]
        y = p["y"]
        w = p["width"]
        h = p["height"]
        label = p["class"]

        # Convertir a coordenadas
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        # Dibujar rectángulo
        draw.rectangle([x1, y1, x2, y2], outline="cyan", width=3)

        # Texto
        draw.text((x1, y1 - 10), label, fill="cyan")

    return image

# -------------------------
# MAIN
# -------------------------
if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if st.button("🚀 Analizar Imagen"):

            if tienda == "":
                st.warning("⚠️ Ingresa el nombre de la tienda")
            else:
                with st.spinner("🧠 Analizando con IA..."):

                    try:
                        # Enviar imagen
                        response = requests.post(
                            MODEL_URL,
                            params={"api_key": API_KEY},
                            files={"file": uploaded_file.getvalue()}
                        )

                        data = response.json()
                        predictions = data.get("predictions", [])
                        conteo = len(predictions)

                        # Dibujar cajas
                        image_con_cajas = dibujar_cajas(image.copy(), predictions)

                        # Mostrar con efecto scan
                        st.markdown('<div class="scan-container">', unsafe_allow_html=True)
                        st.image(image_con_cajas, caption="📸 Detección IA", width=500)
                        st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # -------------------------
                        # RESULTADOS
                        # -------------------------
                        with col2:
                            st.markdown('<div class="card">', unsafe_allow_html=True)

                            if len(predictions) > 0:
                                productos = [p["class"] for p in predictions]
                                conteo_por_producto = pd.Series(productos).value_counts()
                                producto_principal = conteo_por_producto.idxmax()
                            else:
                                producto_principal = "No identificado"

                            st.markdown(f"""
                                <div style="text-align:center;">
                                    <p>Producto detectado</p>
                                    <h2 style="color:#6366f1;">{producto_principal}</h2>
                                    <p>Total detectado</p>
                                    <div class="metric">{conteo}</div>
                                </div>
                            """, unsafe_allow_html=True)

                            if len(predictions) > 0:
                                st.write("### 📊 Detalle por producto")
                                st.dataframe(conteo_por_producto)

                            # Guardar en Sheets
                            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            nueva_fila = [tienda, fecha, producto_principal, conteo]
                            sheet.append_row(nueva_fila)

                            st.success("✅ Reporte guardado")

                            st.markdown('</div>', unsafe_allow_html=True)

                    except Exception as e:
                        st.error("❌ Error en el proceso")
                        st.write(e)

        else:
            # Mostrar imagen inicial sin detección
            st.image(image, caption="📸 Imagen cargada", width=500)

        st.markdown('</div>', unsafe_allow_html=True)