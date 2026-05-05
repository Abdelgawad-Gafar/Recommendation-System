import tempfile, requests, os
from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from analyzer import ReelAnalyzer
from database import reels_collection, logger
from models import ReelPayload, ReelUpdatePayload  # تأكد أن ReelPayload معرف في models

router = APIRouter()
analyzer = ReelAnalyzer()

# موديل جديد لاستقبال قائمة فيديوهات في التحديث
class BatchUpdatePayload(BaseModel):
    reels: List[ReelUpdatePayload]

# موديل جديد لاستقبال قائمة فيديوهات في المعالجة (Processing)
class BatchProcessPayload(BaseModel):
    reels: List[ReelPayload]

@router.post("/api/reels/process")
async def process_reels_batch(payload: BatchProcessPayload):
    results = {"successful": [], "failed": []}
    
    for reel in payload.reels:
        reel_id = str(reel.id)
        try:
            # 1. فحص هل الفيديو موجود لتحديثه أو إضافته
            existing = reels_collection.get(ids=[reel_id], include=["metadatas"])
            
            if existing and existing.get("ids"):
                reels_collection.update(
                    ids=[reel_id],
                    metadatas=[{"createdAt": reel.createdAt, "likes": reel.numOfLikes, "watches": reel.numOfWatches}]
                )
                results["successful"].append({"id": reel_id, "action": "metadata_updated"})
                continue

            # 2. إذا كان جديداً: تحميل الفيديو ومعالجته
            products_info = ", ".join([f"{p.get('product', {}).get('name', '')}" for p in reel.productReels])
            context = f"Brand: {reel.brand.displayName}. Desc: {reel.brand.description}. Products: {products_info}"

            resp = requests.get(reel.videoUrl, timeout=15) # إضافة timeout للأمان
            resp.raise_for_status() # التأكد أن الرابط يعمل

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(resp.content)
                video_path = tmp.name

            # تحليل الذكاء الاصطناعي
            vector = analyzer.process_video(video_path, context)
            if os.path.exists(video_path):
                os.remove(video_path)

            # الإضافة لـ ChromaDB
            reels_collection.add(
                ids=[reel_id],
                embeddings=[vector.tolist()],
                metadatas=[{"createdAt": reel.createdAt, "likes": reel.numOfLikes, "watches": reel.numOfWatches}]
            )
            
            results["successful"].append({"id": reel_id, "action": "created"})
            logger.info(f"Reel {reel_id} processed successfully.")

        except Exception as e:
            logger.error(f"Failed to process reel {reel_id}: {e}")
            results["failed"].append({"id": reel_id, "error": str(e)})

    return {
        "status": "Batch processing complete",
        "summary": {
            "total": len(payload.reels),
            "success": len(results["successful"]),
            "fail": len(results["failed"])
        },
        "details": results
    }

@router.put("/api/reels/update-metadata")
async def update_stats_batch(payload: BatchUpdatePayload):
    results = {"successful": [], "failed": []}
    
    for data in payload.reels:
        reel_id = str(data.reelId)
        try:
            existing = reels_collection.get(ids=[reel_id], include=["metadatas"])
            if not existing["ids"]:
                results["failed"].append({"id": reel_id, "error": "Reel not found in vector database"})
                continue
            
            old_meta = existing["metadatas"][0]
            reels_collection.update(
                ids=[reel_id],
                metadatas=[{"createdAt": old_meta.get("createdAt"), "likes": data.likes, "watches": data.watches}]
            )
            results["successful"].append(reel_id)
            
        except Exception as e:
            results["failed"].append({"id": reel_id, "error": str(e)})

    return {
        "status": "Update batch complete",
        "success_count": len(results["successful"]),
        "failed_details": results["failed"]
    }

@router.delete("/api/reels/delete")
async def delete_reel(reel_id: str):
    # يبقى كما هو أو يمكن تحويله لـ Batch أيضاً بنفس المنطق
    try:
        reel_id_str = str(reel_id)
        existing = reels_collection.get(ids=[reel_id_str])
        if not existing.get("ids"):
            raise HTTPException(status_code=404, detail="Reel not found")

        reels_collection.delete(ids=[reel_id_str])
        return {"status": "deleted", "reelId": reel_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))