 # utils.py
import re
from datetime import datetime

def clean_text(text):
    return ' '.join(text.split())

def extract_date(text):
    patterns = [
        r'\b(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})\b',
        r'\b(\d{2,4}[\/-]\d{1,2}[\/-]\d{1,2})\b'
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(1)
    return datetime.now().strftime("%d/%m/%Y")

def extract_gstin(text):
    pattern = r'\b(\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[A-Z\d]{1})\b'
    match = re.search(pattern, text.upper())
    return match.group(1) if match else "27AAAAA0000A1Z5"

def extract_items(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    items = []
    for line in lines:
        # Pattern: Item Name 2 100 200
        match = re.search(r'(.+?)\s+(\d+)\s+([\d.]+)\s+([\d.]+)', line)
        if match:
            name, qty, rate, amt = match.groups()
            items.append({
                'desc': name.strip(),
                'qty': int(qty),
                'rate': float(rate),
                'amt': float(amt)
            })
    return items if items else [{'desc': 'Service Charge', 'qty': 1, 'rate': 500, 'amt': 500}]
