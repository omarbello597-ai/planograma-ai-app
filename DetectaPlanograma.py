import streamlit as st
import requests
from PIL import Image, ImageDraw
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# CONFIG PAGE
# -------------------------
st.set_page_config(page_title="AI Vision System", layout="wide")

# -------------------------
# 🎨 ESTILO NEGRO + AMARILLO
# -------------------------
st.markdown("""
<style>

/* Fondo negro premium */
[data-testid="stAppViewContainer"] {
    background-color: #000000;
}

/* Quitar header blanco */
[data-testid="stHeader"] {
    background: transparent;
}

/* Tipografía */
html, body, [class*="css"] {
    color: white;
}

/* Título principal */
.title {
    font-size: 48px;
    font-weight: 700;
    color: white;
}

.subtitle {
    font-size: 20px;
    color: #facc15;
}

/* Cards elegantes */
.card {
    background: #0a0a0a;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(250,204,21,0.2);
}

/* Métrica */
.metric {
    font-size: 60px;
    font-weight: bold;
    color: #facc15;
}

/* Botón */
.stButton>button {
    background: #facc15;
    color: black;
    font-weight: bold;
    border-radius: 8px;
}

/* Scan effect */
.scan-container {
    position: relative;
}

.scan-line {
    position: absolute;
    width: 100%;
    height: 2px;
    background: #facc15;
    animation: scan 2s infinite linear;
}

@keyframes scan {
    0% { top: 0%; }
    100% { top: 100%; }
}

</style>
""", unsafe_allow_html=True)

# -------------------------
# HEADER ESTILO IA
# -------------------------
colH1, colH2 = st.columns([1,1])

with colH1:
    st.markdown("""
        <div class="title">AI Vision System</div>
        <div class="subtitle">Smart detection. Real-time insights.</div>
    """, unsafe_allow_html=True)

with colH2:
    st.image("https://images.unsplash.com/photo-1677442136019-21780ecad995", width=350)

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
# INPUTS
# -------------------------
st.markdown("### 📸 Upload & Analyze")

tienda = st.text_input("Nombre de la tienda")
uploaded_file = st.file_uploader("Sube imagen", type=["jpg","png","jpeg"])

# -------------------------
# FUNCIÓN CAJAS
# -------------------------
def dibujar_cajas(image, predictions):
    draw = ImageDraw.Draw(image)

    for p in predictions:
        x = p["x"]
        y = p["y"]
        w = p["width"]
        h = p["height"]

        x1 = x - w/2
        y1 = y - h/2
        x2 = x + w/2
        y2 = y + h/2

        draw.rectangle([x1,y1,x2,y2], outline="#facc15", width=3)

    return image

# -------------------------
# MAIN
# -------------------------
if uploaded_file:

    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns([1.2,1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)

        if st.button("Analyze Image"):

            with st.spinner("Analyzing..."):

                response = requests.post(
                    MODEL_URL,
                    params={"api_key": API_KEY},
                    files={"file": uploaded_file.getvalue()}
                )

                data = response.json()
                predictions = data.get("predictions", [])
                conteo = len(predictions)

                image_boxes = dibujar_cajas(image.copy(), predictions)

                st.markdown('<div class="scan-container">', unsafe_allow_html=True)
                st.image(image_boxes, width=500)
                st.markdown('<div class="scan-line"></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="card">', unsafe_allow_html=True)

                    if predictions:
                        productos = [p["class"] for p in predictions]
                        conteo_por_producto = pd.Series(productos).value_counts()
                        producto = conteo_por_producto.idxmax()
                    else:
                        producto = "N/A"

                    st.markdown(f"""
                    <div style="text-align:center">
                        <h3>Detected Product</h3>
                        <h2 style="color:#facc15;">{producto}</h2>
                        <p>Total</p>
                        <div class="metric">{conteo}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([tienda, fecha, producto, conteo])

                    st.success("Saved")

                    st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.image(image, width=500)

        st.markdown('</div>', unsafe_allow_html=True)