"""
Arşiv Router
- Harici rapor yükleme (kullanıcı katkısı)
- Geçmiş rapor uyumsuzluk tespiti
- Paket satın alma
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from utils.supabase_client import get_supabase
from utils.telegram import notify_admin
import uuid
from datetime import datetime

router = APIRouter()

# ─── MODELLER ─────────────────────────────────────────

class ExternalReportUpload(BaseModel):
    user_id: str
    legal_disclaimer_accepted: bool  # Yasal sorumluluk kabulü
    disclaimer_text: str = "Bu raporu üçüncü taraf olarak yüklüyorum. Raporun nereden temin edildiğine dair tüm yasal sorumluluk tarafıma aittir."

class PackagePurchase(BaseModel):
    user_id: str
    plaka: str
    report_ids: List[str]  # Satın alınacak rapor ID'leri

class DiscountUpdate(BaseModel):
    discount_percent: int  # 0-50 arası

# ─── UYUMSUZLUK TESPİT MOTORU ─────────────────────────

CONFLICT_RULES = [
    {
        "id": "km_dusus",
        "label": "Kilometre Düşüşü",
        "severity": "critical",
        "description": "Araçta kilometre manipülasyonu şüphesi var.",
        "detail": "Eski rapora göre kilometre değeri düşmüş. Bu teknik olarak imkansızdır."
    },
    {
        "id": "kaporta_celisiki",
        "label": "Kaporta/Boya Çelişkisi",
        "severity": "high",
        "description": "Daha önceki raporda orijinal görünen parçalar sonraki raporda boyalı/değişen olarak görünüyor.",
        "detail": "Bu durum, raporlar arasında araçta değişiklik yapıldığına işaret edebilir."
    },
    {
        "id": "sase_hasar_celisiki",
        "label": "Şase/Hasar Kaydı Çelişkisi",
        "severity": "critical",
        "description": "Şase, airbag veya hasar kaydında çelişkili bilgiler mevcut.",
        "detail": "Raporlar arasında yapısal güvenlikle ilgili farklı sonuçlar tespit edildi."
    },
    {
        "id": "mekanik_celisiki",
        "label": "Yağ/Duman Çelişkisi",
        "severity": "high",
        "description": "Önceki raporda temiz görünen mekanik durum, sonraki raporda sorunlu çıkmış.",
        "detail": "Yağ sızıntısı veya duman sorunu raporlar arasında farklı gösteriliyor."
    }
]

def detect_conflicts(reports: list) -> list:
    """
    Raporlar arasındaki uyumsuzlukları tespit et.
    reports: Tarih sıralı rapor listesi (eskiden yeniye)
    """
    if len(reports) < 2:
        return []
    
    conflicts = []
    
    for i in range(1, len(reports)):
        old = reports[i-1]
        new = reports[i]
        
        # KM kontrolü
        old_km = old.get("km", 0) or 0
        new_km = new.get("km", 0) or 0
        if old_km > 0 and new_km > 0 and new_km < old_km:
            conflicts.append({
                **CONFLICT_RULES[0],
                "old_value": f"{old_km:,} km ({old.get('tarih', '?')})",
                "new_value": f"{new_km:,} km ({new.get('tarih', '?')})",
                "fark": f"{old_km - new_km:,} km"
            })
        
        # Kaporta çelişkisi
        old_kaporta = set(old.get("boyali_parcalar", []))
        new_kaporta = set(new.get("boyali_parcalar", []))
        yeni_boyali = new_kaporta - old_kaporta
        if yeni_boyali:
            conflicts.append({
                **CONFLICT_RULES[1],
                "old_value": f"Boyalı parça: {', '.join(old_kaporta) or 'Yok'}",
                "new_value": f"Yeni boyalı: {', '.join(yeni_boyali)}",
            })
        
        # Şase/hasar çelişkisi
        if old.get("sase_durumu") == "orijinal" and new.get("sase_durumu") != "orijinal":
            conflicts.append({
                **CONFLICT_RULES[2],
                "old_value": f"Şase: Orijinal ({old.get('tarih', '?')})",
                "new_value": f"Şase: {new.get('sase_durumu', '?')} ({new.get('tarih', '?')})",
            })
        
        # Yağ/duman çelişkisi
        old_mekanik = old.get("mekanik_notlar", "")
        new_mekanik = new.get("mekanik_notlar", "")
        temiz_ifadeler = ["temiz", "sorunsuz", "normal"]
        sorunlu_ifadeler = ["yağ sızıntı", "duman", "karter"]
        
        old_temiz = any(k in old_mekanik.lower() for k in temiz_ifadeler)
        new_sorunlu = any(k in new_mekanik.lower() for k in sorunlu_ifadeler)
        if old_temiz and new_sorunlu:
            conflicts.append({
                **CONFLICT_RULES[3],
                "old_value": f"Mekanik: Temiz ({old.get('tarih', '?')})",
                "new_value": f"Mekanik: {new_mekanik[:80]}... ({new.get('tarih', '?')})",
            })
    
    return conflicts

def calculate_package_price(reports: list, discount_percent: int = 20) -> dict:
    """Paket fiyatı hesapla"""
    unit_price = 79  # Rapor başına ₺
    total_normal = len(reports) * unit_price
    discount_amount = int(total_normal * discount_percent / 100)
    total_discounted = total_normal - discount_amount
    return {
        "report_count": len(reports),
        "unit_price": unit_price,
        "total_normal": total_normal,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "total_discounted": total_discounted
    }

# ─── ENDPOINT'LER ──────────────────────────────────────

@router.get("/check/{plaka}")
async def check_plate_history(plaka: str, user_id: Optional[str] = None):
    """
    Plaka ile geçmiş rapor sorgula.
    Uyumsuzluk varsa uyarı döndür.
    Paketi satın alma seçeneği sun.
    """
    db = get_supabase()
    
    # Raporları getir (tarih sıralı)
    result = db.table("reports")\
        .select("id, plaka, marka, model, yil, km, created_at")\
        .eq("plaka", plaka.upper().replace(" ", ""))\
        .order("created_at")\
        .execute()
    
    if not result.data:
        return {"found": False, "message": "Bu plakaya ait rapor bulunamadı."}
    
    reports = result.data
    conflicts = detect_conflicts(reports)
    
    # Discount ayarını DB'den al
    discount_setting = db.table("settings")\
        .select("value")\
        .eq("key", "archive_discount_percent")\
        .execute()
    discount = int(discount_setting.data[0]["value"]) if discount_setting.data else 20
    
    pricing = calculate_package_price(reports, discount)
    
    return {
        "found": True,
        "plaka": plaka,
        "report_count": len(reports),
        "reports": [
            {
                "id": r["id"],
                "tarih": r["created_at"][:10],
                "marka": r.get("marka"),
                "model": r.get("model"),
                "km": r.get("km"),
                "price": 79
            }
            for r in reports
        ],
        "has_conflicts": len(conflicts) > 0,
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "conflict_severity": "critical" if any(c["severity"] == "critical" for c in conflicts) else "high" if conflicts else None,
        "pricing": pricing
    }

@router.post("/upload-external")
async def upload_external_report(
    data: ExternalReportUpload,
    file: UploadFile = File(...)
):
    """
    Kullanıcı harici rapor yükle.
    Yasal sorumluluk kabulü zorunlu.
    Admin onayı sonrası arşive girer.
    Kullanıcıya +1 analiz hakkı verilir (onay sonrası).
    """
    if not data.legal_disclaimer_accepted:
        raise HTTPException(status_code=400, detail="Yasal sorumluluk kabulü zorunludur.")
    
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Sadece PDF veya görsel yükleyebilirsiniz.")
    
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Dosya 10MB'ı geçemez.")
    
    # Supabase Storage'a yükle
    db = get_supabase()
    file_id = str(uuid.uuid4())
    file_ext = ".pdf" if file.content_type == "application/pdf" else ".jpg"
    storage_path = f"external_reports/{file_id}{file_ext}"
    
    try:
        db.storage.from_("reports").upload(storage_path, contents)
    except Exception as e:
        pass  # Storage hatası olsa bile devam et
    
    # Arşiv kaydı oluştur (pending)
    db.table("external_reports").insert({
        "id": file_id,
        "user_id": data.user_id,
        "file_path": storage_path,
        "legal_accepted": True,
        "disclaimer_text": data.disclaimer_text,
        "status": "pending_review",
        "created_at": datetime.now().isoformat()
    }).execute()
    
    # Admin bildirimi
    await notify_admin(
        f"📥 Yeni Harici Rapor Yüklendi\n\n"
        f"👤 Kullanıcı: {data.user_id[:8]}...\n"
        f"📋 Yasal kabul: ✅\n"
        f"🔗 İnceleme: https://ekspertizai.com/admin/external/{file_id}"
    )
    
    return {
        "success": True,
        "upload_id": file_id,
        "message": "Raporunuz incelemeye alındı. Onaylandıktan sonra +1 analiz hakkı hesabınıza eklenecek.",
        "reward": "1 ücretsiz analiz hakkı (onay sonrası)"
    }

@router.post("/purchase-package")
async def purchase_package(data: PackagePurchase):
    """Çelişkili raporlar dahil tüm paketi satın al"""
    db = get_supabase()
    
    # Fiyat hesapla
    discount_setting = db.table("settings")\
        .select("value").eq("key", "archive_discount_percent").execute()
    discount = int(discount_setting.data[0]["value"]) if discount_setting.data else 20
    
    pricing = calculate_package_price(data.report_ids, discount)
    
    # Sipariş oluştur (ödeme bekleniyor)
    order_id = str(uuid.uuid4())
    db.table("orders").insert({
        "id": order_id,
        "user_id": data.user_id,
        "type": "archive_package",
        "report_ids": data.report_ids,
        "plaka": data.plaka,
        "amount": pricing["total_discounted"],
        "original_amount": pricing["total_normal"],
        "discount_percent": pricing["discount_percent"],
        "status": "pending_payment",
        "created_at": datetime.now().isoformat()
    }).execute()
    
    return {
        "success": True,
        "order_id": order_id,
        "pricing": pricing,
        "payment_url": f"https://ekspertizai.com/payment/{order_id}"
    }

@router.post("/admin/external/{upload_id}/approve")
async def approve_external_report(upload_id: str):
    """Admin: Harici raporu onayla, kullanıcıya ödül ver"""
    db = get_supabase()
    
    upload = db.table("external_reports")\
        .select("*").eq("id", upload_id).execute()
    
    if not upload.data:
        raise HTTPException(status_code=404, detail="Yükleme bulunamadı")
    
    user_id = upload.data[0]["user_id"]
    
    # Onaylandı olarak işaretle
    db.table("external_reports").update({
        "status": "approved",
        "approved_at": datetime.now().isoformat()
    }).eq("id", upload_id).execute()
    
    # Kullanıcıya +1 analiz hakkı
    user = db.table("users").select("free_analyses").eq("id", user_id).execute()
    if user.data:
        new_count = user.data[0].get("free_analyses", 0) + 1
        db.table("users").update({"free_analyses": new_count}).eq("id", user_id).execute()
    
    return {"success": True, "message": "Rapor onaylandı, kullanıcıya +1 analiz hakkı verildi."}

@router.put("/admin/discount")
async def update_archive_discount(data: DiscountUpdate):
    """Admin: Arşiv paket indirim oranını güncelle"""
    if not 0 <= data.discount_percent <= 50:
        raise HTTPException(status_code=400, detail="İndirim 0-50 arası olmalı")
    
    db = get_supabase()
    db.table("settings").upsert({
        "key": "archive_discount_percent",
        "value": str(data.discount_percent),
        "description": "Arşiv paket indirimi (%)",
        "updated_at": datetime.now().isoformat()
    }).execute()
    
    return {"success": True, "discount_percent": data.discount_percent}
