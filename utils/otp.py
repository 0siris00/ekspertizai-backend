"""
OTP Modülü — Telefon doğrulama
Test aşaması: Telegram üzerinden
Production: Netgsm SMS (hazır, tek satır değişiklik)
"""
import random
import hashlib
import time
import os

# OTP geçerlilik süresi (saniye)
OTP_EXPIRE = 300  # 5 dakika
OTP_LENGTH = 6

# Geçici bellek (production'da Redis kullanılacak)
_otp_store = {}

def generate_otp(phone: str) -> str:
    code = str(random.randint(100000, 999999))
    expire_at = time.time() + OTP_EXPIRE
    key = hashlib.md5(phone.encode()).hexdigest()
    _otp_store[key] = {"code": code, "expire": expire_at, "phone": phone}
    return code

def verify_otp(phone: str, code: str) -> bool:
    key = hashlib.md5(phone.encode()).hexdigest()
    record = _otp_store.get(key)
    if not record:
        return False
    if time.time() > record["expire"]:
        del _otp_store[key]
        return False
    if record["code"] != code:
        return False
    del _otp_store[key]
    return True

async def send_otp_telegram(phone: str, code: str) -> bool:
    """Test aşaması: OTP'yi Telegram'a gönder"""
    import httpx
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    msg = f"🔐 OTP Test\n\nTelefon: {phone}\nKod: *{code}*\nGeçerlilik: 5 dakika"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}
            )
        return r.status_code == 200
    except:
        return False

async def send_otp_netgsm(phone: str, code: str) -> bool:
    """Production: Netgsm SMS (Netgsm bilgileri gelince aktif edilecek)"""
    import httpx
    username = os.getenv("NETGSM_USERNAME")
    password = os.getenv("NETGSM_PASSWORD")
    header = os.getenv("NETGSM_HEADER", "EkspertizAI")
    message = f"EkspertizAI dogrulama kodunuz: {code}. 5 dakika gecerlidir."
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.netgsm.com.tr/sms/send/get",
                params={
                    "usercode": username, "password": password,
                    "gsmno": phone, "message": message,
                    "msgheader": header, "dil": "TR"
                }
            )
        return r.text.startswith("00")
    except:
        return False

async def send_otp(phone: str) -> dict:
    """
    Ana OTP gönderici.
    NETGSM_USERNAME varsa SMS, yoksa Telegram.
    """
    code = generate_otp(phone)
    use_sms = bool(os.getenv("NETGSM_USERNAME"))
    
    if use_sms:
        success = await send_otp_netgsm(phone, code)
        channel = "sms"
    else:
        success = await send_otp_telegram(phone, code)
        channel = "telegram"
    
    return {"success": success, "channel": channel, "expire_seconds": OTP_EXPIRE}
