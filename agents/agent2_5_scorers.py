import anthropic
import asyncio
import json
import os
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
CLIENT = None

def get_client():
    global CLIENT
    if CLIENT is None:
        CLIENT = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return CLIENT

def load_skill(skill_name: str) -> str:
    skill_path = SKILLS_DIR / f"{skill_name}_skill.md"
    return skill_path.read_text(encoding="utf-8")

async def score_category(category: str, masked_text: str, vehicle_info: dict) -> dict:
    skill_content = load_skill(category)
    client = get_client()
    is_lpg = "LPG" in str(vehicle_info.get("yakit", "")).upper()
    context = f"Araç yakıt türü: {vehicle_info.get('yakit', 'Bilinmiyor')}\n"
    if is_lpg:
        context += "NOT: Bu araç LPG'lidir. Oksijen sensörü arızaları ihmal edilmeli.\n"
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        system=skill_content,
        messages=[{"role": "user", "content": f"{context}\nRapor:\n\n{masked_text}"}]
    )
    raw = response.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except:
        return {
            "category": category, "score": "yellow",
            "scoreLabel": "KONTROL GEREKLİ",
            "findings": [{"text": "Kategori analiz edilemedi.", "level": "info", "detail": ""}],
            "parseError": True
        }

async def run_parallel(masked_text: str, vehicle_info: dict, categories: dict) -> list:
    # Kaporta only raporu tespiti
    kaporta_keywords = ['mikron','boya','kaporta','çamurluk','kaput','renk','tamir boyası','folyo']
    mekanik_keywords = ['dinamometre','yağ','motor','vites','şanzıman','fren test','süspansiyon test','km/h']
    text_lower = masked_text.lower()
    has_mekanik = any(k in text_lower for k in mekanik_keywords)
    has_kaporta = any(k in text_lower for k in kaporta_keywords)
    kaporta_only = has_kaporta and not has_mekanik

    # Kaporta only raporu için atlanacak kategoriler
    skip_if_kaporta_only = ['mekanik', 'sarf'] if kaporta_only else []

    tasks = []
    active_categories = []
    for cat, is_present in categories.items():
        if cat in skip_if_kaporta_only:
            continue
        if is_present:
            tasks.append(score_category(cat, masked_text, vehicle_info))
            active_categories.append(cat)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append({
                "category": active_categories[i], "score": "yellow",
                "scoreLabel": "KONTROL GEREKLİ",
                "findings": [{"text": f"Analiz hatası: {str(result)}", "level": "info", "detail": ""}],
                "error": str(result)
            })
        else:
            processed.append(result)
    return processed
