import anthropic
import json
import os

def calculate_verdict(category_results: list) -> tuple:
    has_red = False
    has_yellow = False
    is_risky = False
    for cat in category_results:
        score = cat.get("score", "green")
        if score == "red": has_red = True
        elif score == "yellow": has_yellow = True
        if cat.get("isRiskyVehicle", False): is_risky = True
    for cat in category_results:
        if cat.get("category") == "Güvenlik" and cat.get("score") == "red":
            return "C", "C Tipi — Riskli veya Ağır Hasarlı"
    if is_risky or has_red:
        return "C", "C Tipi — Riskli veya Ağır Hasarlı"
    elif has_yellow:
        return "B", "B Tipi — Masraflı ama Kemikli"
    else:
        return "A", "A Tipi — Masrafsız ve Sağlam"

def check_admin_review(category_results: list) -> dict:
    questions = []
    for cat in category_results:
        if cat.get("parseError") or cat.get("error"):
            questions.append(f"{cat.get('category')} kategorisi analiz edilemedi.")
    return {"needed": len(questions) > 0, "questions": questions}

def calculate_total_costs(category_results: list) -> tuple:
    total_min, total_max = 2500, 5000
    for cat in category_results:
        for cost in cat.get("estimatedCosts", []):
            try:
                parts = cost.get("amount","").replace("₺","").replace(".","").replace(" ","").split("–")
                if len(parts) == 2:
                    total_min += int(parts[0])
                    total_max += int(parts[1])
            except: pass
    return total_min, total_max

def generate_glossary(category_results: list) -> dict:
    glossary = {}
    term_dict = {
        "karter": "Motorun altındaki yağ haznesi. Sızıntı motor için ciddi risk oluşturur.",
        "rotil": "Ön süspansiyon sistemindeki eklem parçası. Deforme olunca direksiyon kontrolü bozulur.",
        "triger": "Motorun iç mekanizmasını senkronize eden kayış. Kopması motoru tamamen çökertir.",
        "turbo": "Egzoz gazını kullanarak motora ek hava pompalar, güç artırır.",
        "terleme": "Contaların yağ veya su ile ıslanması. Kaçak öncesi belirti.",
        "amortisör": "Yolun titreşimini absorbe eden süspansiyon elemanı.",
        "balata": "Fren sisteminde disk üzerine sürtünerek aracı durduran parça.",
        "senkromeç": "Manuel şanzımanda vites geçişini yumuşatan mekanizma.",
        "intercooler": "Turbolu motorlarda sıkıştırılmış havayı soğutan radyatör.",
        "yatak sarması": "Motor içindeki yatakların yağ yokluğundan tutunması — motor tamamen çöker.",
    }
    all_text = str(category_results).lower()
    for term, definition in term_dict.items():
        if term in all_text:
            glossary[term] = definition
    return glossary

async def run(category_results: list, vehicle_info: dict, masked_text: str) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    verdict, verdict_label = calculate_verdict(category_results)
    total_min, total_max = calculate_total_costs(category_results)
    admin_review = check_admin_review(category_results)
    is_risky = any(cat.get("isRiskyVehicle", False) for cat in category_results)
    risky_reasons = [cat.get("riskyReason", "") for cat in category_results if cat.get("isRiskyVehicle")]
    risky_reason = ". ".join([r for r in risky_reasons if r])
    summary_prompt = f"""
Aşağıdaki ekspertiz analiz sonuçlarına göre otomotive yabancı bir müşteri için 3-4 cümlelik sade Türkçe özet yaz.
Teknik terim kullanma. Alım tavsiyesi ver.
Verdict: {verdict} — {verdict_label}
Kategoriler: {json.dumps(category_results, ensure_ascii=False)}
Araç: {vehicle_info.get('marka','')} {vehicle_info.get('model','')} {vehicle_info.get('yil','')} — {vehicle_info.get('km','')} km
Sadece özet metni yaz."""
    summary_response = client.messages.create(
        model="claude-haiku-4-5", max_tokens=400,
        messages=[{"role": "user", "content": summary_prompt}]
    )
    summary = summary_response.content[0].text.strip()
    all_costs = []
    for cat in category_results:
        all_costs.extend(cat.get("estimatedCosts", []))
    all_costs.append({"label": "Periyodik yağ bakımı", "amount": "2.500 – 5.000 ₺", "urgent": False})
    kaporta_findings = []
    admin_notes = []
    for cat in category_results:
        if cat.get("category") == "Kaporta & Değer":
            kaporta_findings = [f.get("text","") for f in cat.get("findings",[])]
        if cat.get("category") == "İdari Kontroller":
            admin_notes = [f.get("text","") for f in cat.get("findings",[])]
    return {
        "verdict": verdict, "verdictLabel": verdict_label, "summary": summary,
        "categories": category_results, "costs": all_costs,
        "totalCostMin": total_min, "totalCostMax": total_max,
        "carportaInfo": kaporta_findings, "adminNotes": admin_notes,
        "glossary": generate_glossary(category_results),
        "isRiskyVehicle": is_risky, "riskyReason": risky_reason,
        "adminReview": admin_review
    }
