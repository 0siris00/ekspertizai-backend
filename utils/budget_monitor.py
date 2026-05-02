"""
Bütçe ve Kullanım İzleme Modülü
Ücretli servislerin limitine yaklaşıldığında Telegram bildirimi gönderir.
"""
import os
import json
from datetime import datetime, date
from pathlib import Path

THRESHOLDS = {
    "anthropic_daily_usd": {"warn": 5.0, "critical": 8.0},
    "anthropic_monthly_usd": {"warn": 50.0, "critical": 80.0},
    "netgsm_sms_count": {"warn": 800, "critical": 950},  # 1000 SMS paketi
    "supabase_db_mb": {"warn": 400, "critical": 480},    # 500MB limit
    "supabase_storage_mb": {"warn": 800, "critical": 950}, # 1GB limit
}

USAGE_FILE = "/opt/ekspertizai/data/usage.json"

def load_usage() -> dict:
    try:
        return json.loads(Path(USAGE_FILE).read_text())
    except:
        return {"anthropic_daily_usd": 0, "anthropic_monthly_usd": 0,
                "netgsm_sms_count": 0, "last_reset": str(date.today())}

def save_usage(data: dict):
    Path(USAGE_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(USAGE_FILE).write_text(json.dumps(data, ensure_ascii=False, indent=2))

def add_usage(key: str, amount: float = 1):
    data = load_usage()
    # Günlük reset kontrolü
    if data.get("last_reset") != str(date.today()):
        data["anthropic_daily_usd"] = 0
        data["last_reset"] = str(date.today())
    data[key] = data.get(key, 0) + amount
    save_usage(data)
    return data[key]

async def check_and_notify(key: str, current_value: float):
    """Eşik aşıldıysa Telegram'a bildirim gönder"""
    import httpx
    threshold = THRESHOLDS.get(key, {})
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
    level = None
    if current_value >= threshold.get("critical", float('inf')):
        level = "🔴 KRİTİK"
    elif current_value >= threshold.get("warn", float('inf')):
        level = "🟡 UYARI"
    
    if not level:
        return
    
    labels = {
        "anthropic_daily_usd": f"Anthropic günlük harcama: ${current_value:.2f}",
        "anthropic_monthly_usd": f"Anthropic aylık harcama: ${current_value:.2f}",
        "netgsm_sms_count": f"Netgsm SMS kullanımı: {int(current_value)}/1000",
        "supabase_db_mb": f"Supabase DB kullanımı: {current_value:.0f}/500 MB",
        "supabase_storage_mb": f"Supabase Storage: {current_value:.0f}/1000 MB",
    }
    
    msg = f"{level} — EkspertizAI Kaynak Uyarısı\n\n{labels.get(key, key)}\n\n⚡ Paketi yükseltmeyi değerlendirin."
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg}
            )
    except:
        pass
