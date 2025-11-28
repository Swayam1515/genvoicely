# app.py — FINAL & PERFECT (Download flow 100% correct)
import streamlit as st
from PIL import Image
from ocr import ocr_extract
from pdf_gen import generate_pdf
from datetime import datetime

st.set_page_config(page_title="Genvoicely", page_icon="Invoice", layout="centered")

# Header
st.markdown("<h1 style='text-align: center; color: #00FF00; font-size: 60px; font-weight: 800; margin-bottom: 0;'>Genvoicely</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 22px; color: #555; margin-top: 10px; margin-bottom: 50px;'>Upload any bill photo → Get GST invoice in seconds</p>", unsafe_allow_html=True)

# Inputs
col1, col2 = st.columns(2)
with col1:
    client_name = st.text_input("Your Company Name", "Swayam Enterprises")
with col2:
    client_gstin = st.text_input("Your GSTIN", "27ABCDE1234F1Z5")

st.markdown("<br>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Bill Photo (Hotel / Restaurant / Shop)", type=['jpg', 'jpeg', 'png'])

# Initialize session state
if "pdf_ready" not in st.session_state:
    st.session_state.pdf_ready = None
if "downloaded" not in st.session_state:
    st.session_state.downloaded = False

if uploaded_file:
    image = Image.open(uploaded_file)
    st.caption("Bill uploaded and processed successfully")

    with st.spinner("Reading bill with AI..."):
        data = ocr_extract(image)

    st.success("Bill read successfully!")

    if st.button("Generate GST Invoice", type="primary", use_container_width=True):
        with st.spinner("Generating invoice..."):
            pdf = generate_pdf(data, client_name, client_gstin)

        st.success("Invoice is ready!")
        st.balloons()

        # Store PDF in session state
        st.session_state.pdf_ready = pdf
        st.session_state.downloaded = False  # Reset download flag

# Show download button only if PDF is ready
if st.session_state.pdf_ready:
    if st.download_button(
        label="Download GST Invoice",
        data=st.session_state.pdf_ready,
        file_name=f"Genvoicely_Invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        key="final_download"
    ):
        # This runs ONLY when user actually clicks download
        if not st.session_state.downloaded:
            st.session_state.downloaded = True
            st.success("Invoice downloaded successfully!")
            st.markdown("<h3 style='text-align: center; color: #16a34a;'>You just saved 15+ minutes of manual work</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 20px; color: #166534;'>Your productive time is priceless</p>", unsafe_allow_html=True)
            st.balloons()

# Clean, Professional Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; padding: 40px 20px; color: #555; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
        <p style="font-size: 18px; margin: 8px 0; color: #666;">
            Made in India with ❤️ | Genvoicely AI
        </p>
        <p style="font-size: 28px; font-weight: bold; margin: 15px 0; color: #FFFFFF;">
            Swayam Deshmukh
        </p>
        <p style="font-size: 18px; margin: 8px 0; color: #444;">
            Python • Computer Vision • Full-Stack AI Engineer
        </p>
        
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br><br>", unsafe_allow_html=True)