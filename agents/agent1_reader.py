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
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        import fitz
        doc = fitz.open(file_path)
        all_text = []
        for page_num in range(min(len(doc), 3)):
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_bytes = pix.tobytes("jpeg")
            if len(img_bytes) > 4*1024*1024:
                pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
                img_bytes = pix.tobytes("jpeg")
            image_data = base64.b64encode(img_bytes).decode("utf-8")
            resp = client.messages.create(model="claude-haiku-4-5", max_tokens=2000,
                messages=[{"role":"user","content":[
                    {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":image_data}},
                    {"type":"text","text":"Bu ilan veya ekspertiz raporu gorselindeki tum metni aynen yaz. Ozellikle aracin konumu, il ve ilce bilgisi, plaka, marka, model, km, fiyat bilgilerini mutlaka dahil et."}
                ]}])
            all_text.append(resp.content[0].text)
        doc.close()
        return "\n".join(all_text)
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    media_type = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png"
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": image_data}},
            {"type": "text", "text": "Bu ilan veya ekspertiz raporu görselindeki tüm metni olduğu gibi yaz. Araç konumu (il, ilçe), plaka, marka, model, km, fiyat bilgilerini mutlaka dahil et."}
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
    # Metin içinden il/ilçe çıkar
    for pattern in [r'(?:Konum|Şehir|İl|Bulunduğu İl)\s*[:\s]+([A-ZÇĞİÖŞÜa-zçğıöşü]+)', r'([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\s*[/,]\s*([A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\s+ilanı']:
        m = re.search(pattern, text, re.IGNORECASE)
        if m: info["il"] = m.group(1).strip()[:30]; break
    ilce_m = re.search(r"(?:Ilce|Semt|İlçe)[:\s]+([A-Za-z\s]+?)(?:\n|,|$)", text, re.IGNORECASE)
    if ilce_m: info["ilce"] = ilce_m.group(1).strip()[:30]
    # Sahibinden formatı: "İstanbul Büyükçekmece" gibi
    sehir_m = re.search(r"(Istanbul|Ankara|Izmir|Bursa|Antalya|Adana|Konya|Mersin|Kocaeli|Samsun|Gaziantep|Balikesir|Denizli|Sakarya|Trabzon|Eskisehir|Kayseri)", text, re.IGNORECASE)
    if sehir_m and not info.get("il"): info["il"] = sehir_m.group(1)
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

def parse_report_text(text: str) -> dict:
    """Metin girişinden rapor parse et — dosya gerektirmez"""
    import re
    vehicle_info = {
        "plaka": None, "marka": None, "model": None,
        "yil": None, "km": None, "yakit": None, "vites": None,
        "ekspertiz_firmasi": None
    }
    # Plaka
    plaka = re.search(r'\b\d{2}\s?[A-ZÇĞİÖŞÜ]{1,3}\s?\d{2,4}\b', text)
    if plaka: vehicle_info["plaka"] = plaka.group().replace(" ","")
    # KM
    km = re.search(r'KM[:\s]*([0-9.,]+)', text, re.IGNORECASE)
    if km: vehicle_info["km"] = int(km.group(1).replace(".","").replace(",",""))
    # Araç bilgisi
    arac = re.search(r'Araç[:\s]*([^\|]+)', text, re.IGNORECASE)
    if arac:
        parts = arac.group(1).strip().split()
        if len(parts) >= 1: vehicle_info["marka"] = parts[0]
        if len(parts) >= 2: vehicle_info["model"] = parts[1]
    # Yakıt/Vites
    if "Benzin" in text: vehicle_info["yakit"] = "Benzin"
    elif "Dizel" in text or "Diesel" in text: vehicle_info["yakit"] = "Dizel"
    if "Manuel" in text: vehicle_info["vites"] = "Manuel"
    elif "Otomatik" in text: vehicle_info["vites"] = "Otomatik"

    categories = {
        "guvenlik": True, "mekanik": True,
        "sarf": True, "kaporta": True, "idari": True
    }
    return {
        "vehicle_info": vehicle_info,
        "masked_text": text,
        "categories": categories
    }
