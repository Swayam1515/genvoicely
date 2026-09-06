# streamlit_app.py — GenVoicely Elite Invoice Intelligence
import io
import time
from datetime import datetime
from html import escape

import pandas as pd
from PIL import Image
import streamlit as st

from ocr import ocr_extract
from pdf_gen import generate_pdf

st.set_page_config(
    page_title="GenVoicely — AI Invoice Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Adaptive Dual-Theme SaaS Design System
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Base Font Override */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Core Variables utilizing Streamlit's Native Theme Hooks */
:root {
    --gv-border: rgba(130, 130, 130, 0.2);
    --gv-radius: 12px;
    --gv-accent: #4F46E5;
    --gv-accent-hover: #4338CA;
}

/* Max Width Override */
.block-container { max-width: 1300px; padding-top: 2rem; padding-bottom: 4rem; }

/* Typography & Branding */
.gv-brand {
    font-size: 24px; font-weight: 800; letter-spacing: -0.05em;
    display: flex; align-items: center; gap: 8px; margin-bottom: 5px;
}
.gv-brand-icon {
    background: linear-gradient(135deg, #4F46E5, #9333EA);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* Hero Section */
.gv-hero-wrapper {
    text-align: center; padding: 60px 20px;
    animation: fadeInUp 0.6s ease-out forwards;
}
.gv-hero-title {
    font-size: 48px; 
    font-weight: 800; 
    letter-spacing: -0.04em; 
    margin-bottom: 16px;
    color: var(--text-color);
}
}
.gv-hero-subtitle {
    font-size: 18px; opacity: 0.7; max-width: 600px; margin: 0 auto 40px auto;
    line-height: 1.5;
}

/* Metric Cards - Adaptive */
.gv-metric-card {
    background-color: var(--secondary-background-color);
    border: 1px solid var(--gv-border);
    border-radius: var(--gv-radius); padding: 24px;
    transition: all 0.2s ease; position: relative; overflow: hidden;
}
.gv-metric-card:hover {
    transform: translateY(-2px);
    border-color: var(--text-color);
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.gv-metric-label {
    font-size: 12px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; opacity: 0.6; margin-bottom: 8px;
}
.gv-metric-value { font-size: 28px; font-weight: 800; }
.gv-metric-accent {
    position: absolute; top: 0; left: 0; width: 100%; height: 3px;
    background: linear-gradient(90deg, #4F46E5, #9333EA); opacity: 0;
    transition: opacity 0.3s ease;
}
.gv-metric-card:hover .gv-metric-accent { opacity: 1; }

/* File Uploader Customization (Theme Agnostic) */
div[data-testid="stFileUploader"] {
    border: 2px dashed var(--gv-border) !important;
    border-radius: var(--gv-radius) !important;
    background-color: transparent !important;
    transition: all 0.2s ease; padding: 2rem;
}
div[data-testid="stFileUploader"]:hover {
    border-color: var(--gv-accent) !important;
    background-color: var(--secondary-background-color) !important;
}

/* Button Refinements */
.stButton>button {
    border-radius: 8px; font-weight: 600; transition: all 0.2s ease;
    border: 1px solid var(--gv-border); min-height: 44px;
}
.stButton>button[kind="primary"] {
    background: var(--gv-accent); color: #FFFFFF; border: none;
}
.stButton>button[kind="primary"]:hover {
    background: var(--gv-accent-hover);
    transform: translateY(-1px);
}

/* Status Chips (Universal contrast) */
.gv-status {
    display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px;
    border-radius: 20px; font-size: 12px; font-weight: 600;
}
.gv-status.success { background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2); }
.gv-status.warning { background: rgba(245, 158, 11, 0.1); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.2); }

/* Custom Frame for Image Previews */
.gv-image-frame {
    border: 1px solid var(--gv-border);
    border-radius: 12px; padding: 8px;
    background-color: var(--secondary-background-color);
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

/* Animations */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
DEFAULT_CLIENT = {"name": "Swayam Enterprises", "gstin": "27ABCDE1234F1Z5"}

defaults = {
    "page": "Home",
    "extracted_data": None,
    "processing_time": 0.0,
    "pdf_buffer": None,
    "source_bytes": None,
    "source_name": None,
    "source_mime": None,
    "client_name": DEFAULT_CLIENT["name"],
    "client_gstin": DEFAULT_CLIENT["gstin"],
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

def reset_invoice():
    for key in ["extracted_data", "processing_time", "pdf_buffer", "source_bytes", "source_name", "source_mime"]:
        st.session_state[key] = None

def safe_float(value, default=0.0):
    try: return float(value)
    except (TypeError, ValueError): return default

def format_money(value):
    return f"₹{safe_float(value):,.2f}"

# ---------------------------------------------------------------------------
# Sidebar Layout
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="gv-brand"><span class="gv-brand-icon">✦</span> GenVoicely</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size: 13px; opacity: 0.6; margin-bottom: 24px;">Autonomous Document Intelligence</div>', unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        ["Home", "Validation Engine", "Invoice Archive", "Client Registry"],
        index=["Home", "Validation Engine", "Invoice Archive", "Client Registry"].index(st.session_state.page),
        label_visibility="collapsed",
    )
    st.session_state.page = page

    st.markdown("<hr style='border:none;border-top:1px solid rgba(130, 130, 130, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background-color: var(--secondary-background-color); border: 1px solid rgba(130, 130, 130, 0.2); border-radius: 8px; padding: 12px;">
            <div style="font-size: 11px; font-weight: 700; color: #4F46E5; margin-bottom: 4px;">SYSTEM STATUS</div>
            <div style="font-size: 13px; font-weight: 600;">● Core API Online</div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Home / Upload View
# ---------------------------------------------------------------------------
if st.session_state.page == "Home":
    if st.session_state.extracted_data is None:
        st.markdown(
            """
            <div class="gv-hero-wrapper">
                <div class="gv-hero-title">Intelligent Receipt Processing</div>
                <div class="gv-hero-subtitle">Drop your thermal receipts or PDF bills below. Our neural pipeline instantly maps layout, extracts line items, and verifies tax consistency.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Upload Container
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            uploaded = st.file_uploader(
                "Upload Source Document",
                type=["jpg", "jpeg", "png", "webp", "pdf"],
                label_visibility="collapsed"
            )

            if uploaded:
                file_bytes = uploaded.getvalue()
                st.session_state.source_bytes = file_bytes
                st.session_state.source_name = uploaded.name
                st.session_state.source_mime = uploaded.type
                
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                
                if st.button("✦ Initialize Extraction Protocol", type="primary", use_container_width=True):
                    progress = st.progress(0)
                    status = st.empty()
                    steps = [
                        ("Mapping document layout...", 20),
                        ("Executing visual thresholding...", 45),
                        ("Extracting tabular line items...", 75),
                        ("Verifying tax mathematics...", 100),
                    ]
                    start = time.perf_counter()
                    try:
                        for text, pct in steps[:-1]:
                            progress.progress(pct)
                            status.markdown(f"<div style='text-align:center; font-size: 13px; opacity: 0.7; font-weight: 500;'>{text}</div>", unsafe_allow_html=True)
                            time.sleep(0.2)

                        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                        extracted = ocr_extract(img)

                        progress.progress(100)
                        status.markdown("<div style='text-align:center; font-size: 13px; color:#10B981; font-weight: 700;'>✓ Pipeline Execution Complete</div>", unsafe_allow_html=True)
                        time.sleep(0.3)

                        st.session_state.processing_time = round(time.perf_counter() - start, 2)
                        st.session_state.extracted_data = extracted
                        st.session_state.pdf_buffer = None
                        st.session_state.page = "Validation Engine"
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Pipeline Error: {exc}")

    else:
        st.session_state.page = "Validation Engine"
        st.rerun()

# ---------------------------------------------------------------------------
# Validation Engine (Human-in-the-loop)
# ---------------------------------------------------------------------------
elif st.session_state.page == "Validation Engine":
    data = st.session_state.extracted_data
    if not data:
        st.info("No document in memory. Please upload a receipt first.")
        if st.button("← Return to Hub"):
            st.session_state.page = "Home"
            st.rerun()
    else:
        st.markdown(
            """
            <div style="border-bottom: 1px solid rgba(130, 130, 130, 0.2); padding-bottom: 16px; margin-bottom: 24px;">
                <h2 style="margin: 0; font-size: 24px; font-weight: 800;">Validation Engine</h2>
                <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.7;">Review OCR output and override discrepancies prior to compilation.</p>
            </div>
            """, unsafe_allow_html=True
        )

        if st.button("← Discard & Upload New", key="reset"):
            reset_invoice()
            st.session_state.page = "Home"
            st.rerun()

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # Executive Metrics Grid
        merchant = str(data.get("supplier_name", "Unknown Merchant"))
        total = safe_float(data.get("grand_total", 0))
        
        m1, m2, m3, m4 = st.columns(4)
        metrics = [
            (m1, "Detected Vendor", merchant),
            (m2, "Inference Latency", f"{st.session_state.processing_time}s"),
            (m3, "Items Parsed", str(len(data.get("items", [])))),
            (m4, "Extracted Total", format_money(total)),
        ]
        for col, label, val in metrics:
            with col:
                st.markdown(f"""
                    <div class="gv-metric-card">
                        <div class="gv-metric-accent"></div>
                        <div class="gv-metric-label">{label}</div>
                        <div class="gv-metric-value" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 22px;">{escape(val)}</div>
                    </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
        
        # Dual Workspace Setup
        col_view, col_edit = st.columns([1, 1.2], gap="large")

        with col_view:
            st.markdown('<h4 style="font-size: 16px; margin-bottom: 16px;">Source Artifact Preview</h4>', unsafe_allow_html=True)
            if st.session_state.source_bytes:
                try:
                    st.markdown('<div class="gv-image-frame">', unsafe_allow_html=True)
                    st.image(Image.open(io.BytesIO(st.session_state.source_bytes)), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception:
                    st.warning("Preview generation failed.")

        with col_edit:
            st.markdown('<h4 style="font-size: 16px; margin-bottom: 16px;">Data Verification</h4>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            merchant_edit = c1.text_input("Merchant Name", value=merchant)
            date_edit = c2.text_input("Invoice Date", value=str(data.get("date", datetime.now().strftime("%d %b %Y"))))
            
            c3, c4 = st.columns(2)
            gstin_edit = c3.text_input("Supplier GSTIN", value=str(data.get("supplier_gstin", "N/A")))
            invoice_num = c4.text_input("Invoice Number", placeholder="e.g. INV-001")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("<span style='font-size: 14px; font-weight: 600;'>Line Items Ledger</span>", unsafe_allow_html=True)
            
            # Interactive Editor
            editor_df = pd.DataFrame(data.get("items", []))
            edited = st.data_editor(
                editor_df,
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True,
                column_config={
                    "desc": st.column_config.TextColumn("Description"),
                    "qty": st.column_config.NumberColumn("Qty", min_value=1, step=1),
                    "rate": st.column_config.NumberColumn("Rate (₹)", min_value=0.0, format="%.2f"),
                    "amt": st.column_config.NumberColumn("Amount (₹)", min_value=0.0, format="%.2f"),
                },
            )
            
            edited_items = edited.to_dict(orient="records")
            calc_subtotal = round(sum(safe_float(x.get("amt", 0)) for x in edited_items), 2)

            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            
            with st.expander("Tax Configuration & Overrides", expanded=True):
                t1, t2 = st.columns(2)
                tax_type = t1.selectbox("Tax Logic", ["Standard GST", "No Tax Applied"])
                tax_rate = t2.number_input("GST Rate (%)", value=18.0, step=1.0)
                
                override_total = st.number_input("Final Grand Total (₹) [Verify against receipt]", value=total, step=1.0)

            if tax_type == "Standard GST" and tax_rate > 0:
                taxable_base = round(override_total / (1 + tax_rate / 100), 2)
                total_tax = round(override_total - taxable_base, 2)
                cgst = round(total_tax / 2, 2)
                sgst = round(total_tax / 2, 2)
            else:
                cgst = sgst = 0.0
                taxable_base = override_total

            math_check = round(calc_subtotal + cgst + sgst, 2)
            
            if abs(math_check - override_total) > 1.0:
                st.markdown(f'<div class="gv-status warning">⚠ Subtotal + Taxes ({format_money(math_check)}) mismatch with Override Total ({format_money(override_total)})</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="gv-status success">✓ Ledger Mathematics Verified</div>', unsafe_allow_html=True)

            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

            if st.button("Compile Professional Tax Document", type="primary", use_container_width=True):
                payload = {
                    "supplier_name": merchant_edit,
                    "supplier_gstin": gstin_edit,
                    "date": date_edit,
                    "invoice_number": invoice_num,
                    "items": edited_items,
                    "subtotal": calc_subtotal if calc_subtotal else taxable_base,
                    "cgst": cgst,
                    "sgst": sgst,
                    "grand_total": override_total,
                }
                with st.spinner("Generating Vector PDF..."):
                    st.session_state.pdf_buffer = generate_pdf(
                        payload,
                        st.session_state.client_name,
                        st.session_state.client_gstin,
                    )
                    st.session_state.extracted_data = payload
                st.success("Compilation Successful.")

            if st.session_state.pdf_buffer:
                filename = f"GenVoicely_Export_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                st.download_button(
                    "📥 Download Compliant PDF",
                    data=st.session_state.pdf_buffer,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )

# ---------------------------------------------------------------------------
# Peripheral Views
# ---------------------------------------------------------------------------
elif st.session_state.page == "Client Registry":
    st.markdown("## Client Registry", unsafe_allow_html=True)
    st.write("Configure the target corporate entity injected into the 'Bill To' fields of generated PDFs.")
    
    with st.form("client_form"):
        name = st.text_input("Billed Entity Name", value=st.session_state.client_name)
        gstin = st.text_input("Corporate GSTIN", value=st.session_state.client_gstin)
        if st.form_submit_button("Save Configuration", type="primary"):
            st.session_state.client_name = name
            st.session_state.client_gstin = gstin
            st.success("Entity profile updated.")

elif st.session_state.page == "Invoice Archive":
    st.markdown("## Invoice Archive", unsafe_allow_html=True)
    if st.session_state.pdf_buffer:
        st.success("A compiled document is currently in memory. Return to the Validation Engine to download it.")
    else:
        st.info("No documents have been compiled in the current session.")

# Global Footer
st.markdown("<br><br><div style='text-align:center; opacity: 0.5; font-size: 12px; margin-top: 40px;'>GenVoicely AI • Proprietary Document Intelligence System</div>", unsafe_allow_html=True)
