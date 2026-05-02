import anthropic
import fitz
import base64
import re
import os
import json
from pathlib import Path

def extract_text_from_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_from_image(file_path: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(file_path).suffix.lower()
    media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
            {"type": "text", "text": "Bu ekspertiz raporu görselindeki tüm metni olduğu gibi yaz. Hiçbir şeyi atlama."}
        ]}]
    )
    return response.content[0].text

def mask_personal_data(text: str) -> str:
    text = re.sub(r'\b\d{11}\b', '***********', text)
    text = re.sub(r'(\+90|0)?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', '***TELEFON***', text)
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***EMAIL***', text)
    def mask_sase(match):
        s = match.group(0)
        return '*' * (len(s) - 6) + s[-6:]
    text = re.sub(r'[A-HJ-NPR-Z0-9]{17}', mask_sase, text)
    return text

def detect_categories(text: str) -> dict:
    text_upper = text.upper()
    return {
        "guvenlik": any(kw in text_upper for kw in ["AİRBAG","AIRBAG","ŞASE","FREN TEST","EMNİYET"]),
        "mekanik": any(kw in text_upper for kw in ["MOTOR","TURBO","ŞANZIMAN","KARTER","ENJEKTÖR","VURUNTU","TERLEME","KAÇAK","DUMAN"]),
        "sarf": any(kw in text_upper for kw in ["TRİGER","LASTİK","ROTİL","ROT BAŞI","SÜSPANSİYON","AMORTISÖR","BALATA"]),
        "kaporta": any(kw in text_upper for kw in ["BOYALI","DEĞİŞEN","ONARIM","KAPORTA","DIŞ GÖVDE","BOYA","MİKRON"]),
        "idari": any(kw in text_upper for kw in ["OGS","HGS","MTV","KM SORGU","EMİSYON","HASAR KAYDI","SBM"])
    }

def parse_vehicle_info(text: str) -> dict:
    info = {}
    plaka = re.search(r'PLAKA\s*[:\s]+([A-Z0-9]{2,8})', text, re.IGNORECASE)
    if plaka: info["plaka"] = plaka.group(1).strip()
    marka = re.search(r'MARKA\s*[:\s]+([A-ZÇĞİÖŞÜa-z\s\-]+?)(?:\n|MODEL)', text, re.IGNORECASE)
    if marka: info["marka"] = marka.group(1).strip()
    model = re.search(r'MODEL\s*[:\s]+([A-Za-z0-9\s\.\-]+?)(?:\n|ÜRETİM|YIL)', text, re.IGNORECASE)
    if model: info["model"] = model.group(1).strip()
    yil = re.search(r'(?:ÜRETİM YILI|MODEL YILI)[:\s]+(\d{4})', text, re.IGNORECASE)
    if yil: info["yil"] = int(yil.group(1))
    km = re.search(r'(\d{1,3}(?:\.\d{3})*|\d+)\s*[Kk][Mm]', text)
    if km: info["km"] = int(km.group(1).replace(".", ""))
    for yakit in ["Dizel","Benzin","LPG","Benzin/LPG","Hibrit","Elektrik"]:
        if yakit.upper() in text.upper():
            info["yakit"] = yakit
            break
    if "OTOMATİK" in text.upper(): info["vites"] = "Otomatik"
    elif "MANUEL" in text.upper(): info["vites"] = "Manuel"
    for firma in ["Dynobil","Otorapor","PilotGarage","Umran","Garantili Arabam","Dynomoss","Güney"]:
        if firma.upper() in text.upper():
            info["ekspertiz_firmasi"] = firma
            break
    return info

async def run(file_path: str, file_type: str) -> dict:
    if file_type == "pdf":
        raw_text = extract_text_from_pdf(file_path)
    else:
        raw_text = extract_text_from_image(file_path)
    vehicle_info = parse_vehicle_info(raw_text)
    categories = detect_categories(raw_text)
    masked_text = mask_personal_data(raw_text)
    return {"raw_text": raw_text, "masked_text": masked_text, "vehicle_info": vehicle_info, "categories": categories}
