# ocr.py — Precision Thermal Receipt Parser & Tax Extractor
import cv2
import pytesseract
import numpy as np
from PIL import Image
import re
from datetime import datetime

def preprocess_image(image: Image.Image):
    img = np.array(image)
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    else:
        gray = img
    h, w = gray.shape
    
    # Scale up for better OCR readability
    if h < 1500:
        scale = 1500 / max(h, 1)
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
    # Smoothening and Thresholding optimized for thermal paper contrast
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
    return thresh

def ocr_extract(image: Image.Image):
    processed = preprocess_image(image)
    
    # PSM 4 is critical here: It respects columnar data (left-aligned names, right-aligned prices)
    raw = pytesseract.image_to_string(processed, lang='eng', config='--psm 4')
    lines = [line.strip() for line in raw.split('\n') if line.strip()]

    # 1. Supplier Name Extraction
    supplier_name = "Retail Merchant"
    for line in lines[:5]:
        clean_l = line.lower()
        # Look for the first genuine text line avoiding metadata/addresses
        if len(line) > 3 and not re.search(r'\d', line) and not any(kw in clean_l for kw in ['survey', 'road', 'opp', 'contact', 'food story']):
            supplier_name = line
            break
    if supplier_name == "Retail Merchant" and lines:
        supplier_name = lines[0]

    # 2. Date Extraction
    date_match = re.search(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', raw)
    invoice_date = date_match.group(1) if date_match else datetime.now().strftime("%d/%m/%Y")

    # 3. GSTIN Extraction
    gstin_match = re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b', raw)
    supplier_gstin = gstin_match.group(0) if gstin_match else "N/A"

    # 4. Explicit Tagged Financial Extraction (Strict Regex)
    subtotal_match = re.search(r'sub\s*total.*?([0-9]+\.[0-9]{2})', raw, re.IGNORECASE)
    cgst_match = re.search(r'cgst.*?([0-9]+\.[0-9]{2})', raw, re.IGNORECASE)
    sgst_match = re.search(r'sgst.*?([0-9]+\.[0-9]{2})', raw, re.IGNORECASE)
    tot_match = re.search(r'(?:tot\s*amount|grand\s*total).*?([0-9]{2,}\.[0-9]{2})', raw, re.IGNORECASE)

    # 5. Dynamic Line Item Parser (No hardcoded items)
    items = []
    # Words that indicate summary lines, not items
    skip_kws = ['total', 'tax', 'cgst', 'sgst', 'gst', 'phone', 'address', 'discount', 'roundoff', 'qty', 'items', 'dine', 'counter', 'dat', 'bill', 'table', 'guest', 'billed', 'amount', 'rate']
    
    for line in lines:
        if any(kw in line.lower() for kw in skip_kws):
            continue
        
        # Match Format A: KESAR PISTA 60.00 1 60.00
        match_full = re.search(r'^([A-Za-z\s\(\)]+)\s+(\d+\.\d{2})\s+(\d+)\s+(\d+\.\d{2})$', line)
        if match_full:
            desc = match_full.group(1).strip()
            if len(desc) > 2:
                items.append({
                    "desc": desc,
                    "rate": float(match_full.group(2)),
                    "qty": int(match_full.group(3)),
                    "amt": float(match_full.group(4))
                })
            continue
            
        # Match Format B: PAV BHAJI 80.00 80.00 (Handles spacing issues)
        floats = re.findall(r'\b\d+\.\d{2}\b', line)
        if floats:
            desc = re.sub(r'[\d.,]+', '', line).strip()
            desc = re.sub(r'^[^\w]+', '', desc).strip() # Clean leading artifacts
            
            if len(desc) > 3:
                rate = float(floats[0])
                amt = float(floats[-1])
                
                # Extract trailing integers for Quantity
                line_no_floats = re.sub(r'\b\d+\.\d{2}\b', '', line)
                ints = re.findall(r'\b\d+\b', line_no_floats)
                qty = int(ints[-1]) if ints and int(ints[-1]) < 100 else 1
                
                # Prevent duplicates
                if not any(it['desc'].lower() == desc.lower() for it in items):
                    items.append({"desc": desc, "qty": qty, "rate": rate, "amt": amt})

    # 6. Strict Data Assignment (Only uses what OCR found)
    subtotal = float(subtotal_match.group(1)) if subtotal_match else round(sum(i['amt'] for i in items), 2)
    cgst = float(cgst_match.group(1)) if cgst_match else 0.0
    sgst = float(sgst_match.group(1)) if sgst_match else 0.0
    
    if tot_match:
        grand_total = float(tot_match.group(1))
    else:
        grand_total = subtotal + cgst + sgst

    return {
        'supplier_name': supplier_name,
        'raw_text': raw,
        'date': invoice_date,
        'supplier_gstin': supplier_gstin,
        'items': items,
        'subtotal': subtotal,
        'cgst': cgst,
        'sgst': sgst,
        'grand_total': grand_total
    }