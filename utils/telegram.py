import httpx
import os

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def send_message(chat_id: str, text: str) -> bool:
    if not BOT_TOKEN or not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{BASE_URL}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram hata: {e}")
        return False

async def notify_admin(text: str) -> bool:
    return await send_message(ADMIN_CHAT_ID, text)

async def notify_admin_review(report_id: str, questions: list, vehicle_info: dict) -> bool:
    marka = vehicle_info.get("marka", "?")
    model = vehicle_info.get("model", "")
    plaka = vehicle_info.get("plaka", "")
    text = f"🔔 *Manuel İnceleme Gerekiyor*\n\n🚗 {marka} {model} `{plaka}`\n📋 Rapor: `{report_id[:8]}...`\n\n❓ *Bulgular:*\n"
    for i, q in enumerate(questions, 1):
        text += f"{i}. {q}\n"
    text += f"\nhttps://ekspertizai.com/admin/review/{report_id}"
    return await notify_admin(text)

async def notify_new_report(report_id: str, vehicle_info: dict, verdict: str) -> bool:
    marka = vehicle_info.get("marka", "?")
    model = vehicle_info.get("model", "")
    km = vehicle_info.get("km", 0)
    emoji = {"A": "✅", "B": "🟡", "C": "🔴"}.get(verdict, "❓")
    text = f"{emoji} *Yeni Rapor*\n\n🚗 {marka} {model} — {km:,} km\n📊 Sonuç: *{verdict} Tipi*"
    return await notify_admin(text)

async def notify_consultation_request(expert_chat_id: str, report_id: str, vehicle_info: dict, preferred_time: str, user_phone: str) -> bool:
    marka = vehicle_info.get("marka", "?")
    model = vehicle_info.get("model", "")
    km = vehicle_info.get("km", 0)
    plaka = vehicle_info.get("plaka", "")
    text = f"📞 *Yeni Danışmanlık Talebi*\n\n🚗 {marka} {model} — {km:,} km `{plaka}`\n👤 Müşteri: `{user_phone}`\n🕐 Tercih: {preferred_time}\n\nhttps://ekspertizai.com/admin/consultation/{report_id}"
    return await send_message(expert_chat_id, text)
