# Genvoicely — AI GST Invoice Generator

Upload any hotel/restaurant/shop bill photo → Get perfect GST-compliant invoice in seconds.

Live Demo :- [https://huggingface.co/spaces/Swayam15/genvoicelly]

### Features
- Automatic extraction of GSTIN, date, items, CGST & SGST
- Generates professional PDF invoice
- No manual typing required
- Works on real-world Indian bills

### Tech Stack
- Streamlit
- OpenCV + pytesseract
- ReportLab
- Python

### Run Locally
```bash
git clone https://github.com/Swayam1515/genvoicely.git
cd genvoicely
pip install -r requirements.txt
streamlit run app.py
