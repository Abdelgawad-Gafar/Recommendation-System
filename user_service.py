from fastapi import APIRouter
from database import reels_collection, get_sql_conn,  logger
from cf_trainer import CFTrainer
import numpy as np
from models import UserPayload

router = APIRouter()
cf_engine = CFTrainer()

def get_trend_reels_sql(top_k: int, viewed_ids: list):
    try:
        conn = get_sql_conn()
        cursor = conn.cursor()
        # جلب أضعاف العدد المطلوب كاحتياطي (Buffer)
        cursor.execute(f"SELECT TOP {top_k * 3} Id FROM ReelsTable ORDER BY (NumOfWatches + NumOfLikes * 2) DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [int(row[0]) for row in rows if str(row[0]) not in viewed_ids]
    except Exception as e:
        logger.error(f"Trend System (SQL) Failed: {e}")
        return []

def get_latest_reels_sql(top_k: int, viewed_ids: list):
    try:
        conn = get_sql_conn()
        cursor = conn.cursor()
        cursor.execute(f"SELECT TOP {top_k * 3} Id FROM ReelsTable ORDER BY CreatedAt DESC")
        rows = cursor.fetchall()
        conn.close()
        
        return [int(row[0]) for row in rows if str(row[0]) not in viewed_ids][:top_k]
    except Exception as e:
        logger.error(f"Fallback System Failed: {e}")
        return []

@router.post("/api/users/recommend")
async def recommend(user: UserPayload, top_k: int = 10):
    viewed_ids = list(set([str(v.get('reelId')) for v in user.userReelViews if 'reelId' in v]))
    
    ai_results = []
    trend_results = []
    cf_results = []

    # 1. الذكاء الاصطناعي (AI)
    # 1. الذكاء الاصطناعي (AI)
    try:
        if not viewed_ids:
            user_vector = np.zeros(512)
        else:
            viewed_data = reels_collection.get(ids=viewed_ids, include=["embeddings"])
            
            # --- الحل السحري لتجنب خطأ NumPy ---
            embeddings = viewed_data.get("embeddings")
            if embeddings is not None and len(embeddings) > 0:
                user_vector = np.mean(embeddings, axis=0)
            else:
                user_vector = np.zeros(512)
            # -----------------------------------

        # البحث بعدد ديناميكي
        search = reels_collection.query(query_embeddings=[user_vector.tolist()], n_results=top_k * 3)
        
        # فحص آمن جداً لنتيجة البحث
        if search.get("ids") and len(search["ids"]) > 0 and len(search["ids"][0]) > 0:
            ai_results = [int(rid) for rid in search["ids"][0] if str(rid) not in viewed_ids]
            
    except Exception as e:
        logger.error(f"AI System Offline: {e}")

    # 2. السلوك المجتمعي (CF)
    # 2. السلوك المجتمعي (CF)
    try:
        cf_raw = cf_engine.get_top_items_for_user(user.id, top_n=top_k * 3)
        if cf_raw:
            cf_results = [int(rid) for rid in cf_raw if str(rid) not in viewed_ids]
        else:
            logger.warning("CF System: Missing pickle file or user not found. Skipping CF.")
    except Exception as e:
        logger.error(f"CF System Offline: {e}")

    # ==================== المازج الديناميكي (Dynamic Mixer) ====================
    working_systems = []
    if ai_results: working_systems.append(ai_results)
    if cf_results: working_systems.append(cf_results)
    if trend_results: working_systems.append(trend_results)

    final_feed = []

    # الحالة 1: 3 أنظمة تعمل (النسب: 40% AI, 30% CF, 30% Trend)
    if len(working_systems) == 3:
        ai_count = int(top_k * 0.4)
        cf_count = int(top_k * 0.3)
        trend_count = top_k - ai_count - cf_count # ضمان أن المجموع يساوي top_k بالضبط

        logger.info(f"3 Systems Online. Mixing: {ai_count} AI, {cf_count} CF, {trend_count} Trend.")
        final_feed.extend(ai_results[:ai_count])
        final_feed.extend(cf_results[:cf_count])
        final_feed.extend(trend_results[:trend_count])

    # الحالة 2: نظامان فقط يعملان (النسب: 50% لكل نظام)
    elif len(working_systems) == 2:
        sys1_count = int(top_k * 0.5)
        sys2_count = top_k - sys1_count

        logger.info(f"2 Systems Online. Mixing {sys1_count} and {sys2_count}.")
        final_feed.extend(working_systems[0][:sys1_count])
        final_feed.extend(working_systems[1][:sys2_count])

    # الحالة 3: نظام واحد يعمل (النسبة: 100%)
    elif len(working_systems) == 1:
        logger.info(f"1 System Online. Giving it 100% capacity ({top_k} reels).")
        final_feed.extend(working_systems[0][:top_k])

    # الحالة 4: لا يوجد أي نظام يعمل (الخطة البديلة)
    else:
        logger.critical("ALL SYSTEMS FAILED! Triggering Ultimate SQL Fallback.")
        final_feed = get_latest_reels_sql(top_k, viewed_ids)
        return {"recommendedReelIds": final_feed, "system_status": "Fallback Only"}

    # ==================== تنظيف التكرارات واستكمال النواقص ====================
    seen = set()
    unique_feed = []
    
    # 1. إضافة الفيديوهات المختارة بدون تكرار
    for rid in final_feed:
        if rid not in seen:
            unique_feed.append(rid)
            seen.add(rid)

    # 2. في حالة نقص العدد (بسبب أن الأنظمة اقترحت نفس الفيديوهات)، نملأ من الاحتياطي
    if len(unique_feed) < top_k:
        backup_pool = ai_results + trend_results + cf_results
        for rid in backup_pool:
            if rid not in seen:
                unique_feed.append(rid)
                seen.add(rid)
                if len(unique_feed) == top_k:
                    break

    return {
        "recommendedReelIds": unique_feed[:top_k],
        "active_systems_count": len(working_systems)
    }