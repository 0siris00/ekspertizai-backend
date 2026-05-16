import asyncio
import uuid
import os
from agents.agent1_reader import run as agent1_run
from agents.agent2_5_scorers import run_parallel
from agents.agent6_writer import run as agent6_run
from utils.telegram import notify_admin_review, notify_new_report

async def analyze_report(file_path: str, file_type: str, user_id: str, supabase_client=None) -> dict:
    report_id = str(uuid.uuid4())
    try:
        print(f"[{report_id}] Agent 1: Belge okunuyor...")
        reader_result = await agent1_run(file_path, file_type)
        vehicle_info = reader_result["vehicle_info"]
        masked_text = reader_result["masked_text"]
        categories = reader_result["categories"]
        if not any(categories.values()):
            return {"success": False, "error": "Rapor içeriği okunamadı. Lütfen daha net bir fotoğraf veya PDF yükleyin."}
        print(f"[{report_id}] Agent 2-5: Paralel skorlama...")
        category_results = await run_parallel(masked_text, vehicle_info, categories)
        print(f"[{report_id}] Agent 6: Rapor yazılıyor...")
        final_report = await agent6_run(category_results, vehicle_info, masked_text)
        final_report["vehicleInfo"] = vehicle_info
        final_report["reportId"] = report_id
        if supabase_client:
            await save_to_supabase(supabase_client, report_id, user_id, vehicle_info, final_report)
        if final_report["adminReview"]["needed"]:
            await notify_admin_review(report_id, final_report["adminReview"]["questions"], vehicle_info)
        await notify_new_report(report_id, vehicle_info, final_report["verdict"])
        print(f"[{report_id}] Tamamlandı. Verdict: {final_report['verdict']}")
        # İlan bilgilerini kaydet (araç analizi için)
        try:
            from agents.ilan_agent import save_ilan_to_db
            await save_ilan_to_db(vehicle_info, report_id, user_id)
        except Exception as ie:
            print(f"İlan kayıt hatası: {ie}")
        
        # vehicleInfo eksik alanları ilan agent ile tamamla
        vi = final_report.get("vehicleInfo", {})
        if not vi.get("marka") or not vi.get("model"):
            try:
                from agents.ilan_agent import extract_ilan_info
                ilan_info = await extract_ilan_info(file_path, file_type)
                for key in ["marka","model","km","motor_hacmi","beygir","il","ilce","yil","yakit","vites","kasa_tipi"]:
                    if ilan_info.get(key) and not vi.get(key):
                        vi[key] = ilan_info[key]
                final_report["vehicleInfo"] = vi
                print(f"[{report_id}] İlan agent ile tamamlandı: {vi.get('marka')} {vi.get('model')}")
            except Exception as ie:
                print(f"[{report_id}] İlan agent hatası: {ie}")
        
        return {"success": True, "data": final_report}
    except Exception as e:
        print(f"[{report_id}] Hata: {str(e)}")
        return {"success": False, "error": str(e), "reportId": report_id}

async def save_to_supabase(client, report_id, user_id, vehicle_info, analysis):
    try:
        client.table("reports").insert({
            "id": report_id, "user_id": user_id,
            "plaka": vehicle_info.get("plaka"),
            "marka": vehicle_info.get("marka"),
            "model": vehicle_info.get("model"),
            "yil": vehicle_info.get("yil"),
            "km": vehicle_info.get("km"),
            "yakit": vehicle_info.get("yakit"),
            "vites": vehicle_info.get("vites"),
            "ekspertiz_firmasi": vehicle_info.get("ekspertiz_firmasi"),
        }).execute()
        client.table("analyses").insert({
            "report_id": report_id,
            "verdict": analysis["verdict"],
            "verdict_label": analysis["verdictLabel"],
            "summary": analysis["summary"],
            "categories": analysis["categories"],
            "costs": analysis["costs"],
            "total_cost_min": analysis["totalCostMin"],
            "total_cost_max": analysis["totalCostMax"],
            "is_risky_vehicle": analysis["isRiskyVehicle"],
            "risky_reason": analysis.get("riskyReason",""),
            "admin_review_needed": analysis["adminReview"]["needed"],
            "admin_review_questions": analysis["adminReview"]["questions"],
        }).execute()
    except Exception as e:
        print(f"Supabase kayıt hatası: {e}")

async def analyze_text(report_text: str, user_id: str, supabase_client=None) -> dict:
    """Direkt metin girişi ile analiz — dosya gerektirmez"""
    from agents.agent1_reader import parse_report_text
    report_id = str(uuid.uuid4())
    try:
        reader_result = parse_report_text(report_text)
        vehicle_info = reader_result["vehicle_info"]
        masked_text = reader_result["masked_text"]
        categories = reader_result["categories"]
        category_results = await run_parallel(masked_text, vehicle_info, categories)
        final_report = await agent6_run(category_results, vehicle_info, masked_text)
        final_report["vehicleInfo"] = vehicle_info
        final_report["reportId"] = report_id
        if supabase_client:
            await save_to_supabase(supabase_client, report_id, user_id, vehicle_info, final_report)
        return {"success": True, "data": final_report}
    except Exception as e:
        return {"success": False, "error": str(e), "reportId": report_id}

async def analyze_report_smart(file_path: str, file_type: str, user_id: str, supabase_client=None) -> dict:
    from agents.agent1_reader import extract_text_from_pdf, extract_text_from_image, parse_vehicle_info, detect_categories, mask_personal_data
    report_id = str(uuid.uuid4())
    try:
        if file_type == "pdf":
            raw_text = extract_text_from_pdf(file_path)
            if len(raw_text.strip()) < 100:
                raw_text = extract_text_from_image(file_path)
        else:
            raw_text = extract_text_from_image(file_path)
        vehicle_info = parse_vehicle_info(raw_text)
        categories = detect_categories(raw_text)
        masked_text = mask_personal_data(raw_text)
        if not any(categories.values()):
            categories = {"guvenlik": True, "mekanik": True, "sarf": True, "kaporta": True, "idari": True}
        category_results = await run_parallel(masked_text, vehicle_info, categories)
        final_report = await agent6_run(category_results, vehicle_info, masked_text)
        final_report["vehicleInfo"] = vehicle_info
        final_report["reportId"] = report_id
        return {"success": True, "data": final_report}
    except Exception as e:
        return {"success": False, "error": str(e), "reportId": report_id}
