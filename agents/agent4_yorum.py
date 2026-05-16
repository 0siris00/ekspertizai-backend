import anthropic
import os
import json
import re

async def run(arac_bilgi: dict, kronik_sorunlar: list) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    marka = arac_bilgi.get("marka","")
    seri = arac_bilgi.get("seri","")
    model = arac_bilgi.get("model","")
    yil = arac_bilgi.get("yil","")
    km = arac_bilgi.get("km","")
    yakit = arac_bilgi.get("yakit_tipi","")
    vites = arac_bilgi.get("vites","")
    kasa = arac_bilgi.get("kasa_tipi","")
    motor_gucu = arac_bilgi.get("motor_gucu","")
    motor_hacmi = arac_bilgi.get("motor_hacmi","")
    cekis = arac_bilgi.get("cekis","")
    hasar = arac_bilgi.get("agir_hasar_kayitli",False)
    boya = arac_bilgi.get("boya_degisen","")
    tramer = arac_bilgi.get("tramer_durumu","")
    aciklama = arac_bilgi.get("aciklama","")
    
    arac_str = f"{yil} {marka} {seri} {model}".strip()
    
    kronik_str = ""
    if kronik_sorunlar:
        kronik_str = "\n".join([f"- {s}" for s in kronik_sorunlar[:5]])
    
    prompt = f"""Bir ikinci el arac alicisi icin bu arac hakkinda kapsamli bir degerlendirme yap.

ARAC BILGILERI:
- Arac: {arac_str}
- KM: {km}
- Yakit: {yakit} | Vites: {vites} | Kasa: {kasa}
- Motor: {motor_hacmi} / {motor_gucu} | Cekis: {cekis}
- Agir hasar kaydi: {"VAR" if hasar else "YOK"}
- Boya degisen: {boya or "Bilgi yok"}
- Tramer: {tramer or "Bilgi yok"}
- Aciklama: {aciklama or "Yok"}

BU ARACA AIT BILINEN KRONIK SORUNLAR:
{kronik_str or "Bilinen kronik sorun bulunamadi"}

Lutfen asagidaki JSON formatinda yorum yap. SADECE JSON don:
{{
  "genel_degerlendirme": "3-4 cumle sade Turkce ozet",
  "dikkat_edilecekler": ["madde1","madde2","madde3"],
  "satici_sorulari": ["soru1","soru2","soru3","soru4","soru5"],
  "durum": "iyi|dikkat|riskli",
  "durum_label": "Iyi Durumda|Dikkat Gerektirir|Riskli"
}}"""
    
    try:
        resp = client.messages.create(
            model="claude-haiku-4-5", max_tokens=1000,
            messages=[{"role":"user","content":prompt}]
        )
        raw = re.sub(r"```json|```","",resp.content[0].text.strip()).strip()
        result = json.loads(raw)
        print(f"Agent4: {arac_str} yorumlandı - {result.get('durum')}")
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Agent4 hata: {e}")
        return {"success": False, "error": str(e), "data": {
            "genel_degerlendirme": "Araç değerlendirmesi yapılamadı.",
            "dikkat_edilecekler": [],
            "satici_sorulari": [],
            "durum": "dikkat",
            "durum_label": "Dikkat Gerektirir"
        }}
