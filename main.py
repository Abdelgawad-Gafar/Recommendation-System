from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
import os

# استيراد المسارات (Routers)
from reel_service import router as reel_router
from user_service import router as user_router

# استيراد دالة التدريب
from run_daily_training import sync_and_train

# =====================================================================
# إدارة دورة حياة السيرفر (Lifespan) لجدولة التدريب في الخلفية
# =====================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. ما يحدث عند تشغيل السيرفر (Startup)
    scheduler = BackgroundScheduler()
    
    # جدولة المهمة لتعمل يومياً الساعة 3:00 فجراً
    scheduler.add_job(sync_and_train, 'cron', hour=3, minute=0)
    scheduler.start()
    
    # إذا كان الملف غير موجود (أول مرة يتم تشغيل النظام فيها)، ابدأ التدريب فوراً في الخلفية
    if not os.path.exists("svd_data/svd_results.pkl"):
        print("SVD Matrix not found. Starting initial training in background...")
        scheduler.add_job(sync_and_train)
        
    yield # هنا يبدأ السيرفر في استقبال طلبات المستخدمين بسلاسة
    
    # 2. ما يحدث عند إغلاق السيرفر (Shutdown)
    scheduler.shutdown()

# =====================================================================
# إعداد تطبيق FastAPI
# =====================================================================
app = FastAPI(
    title="Alluvo Hybrid Recommendation Engine",
    description="Production-Ready AI & SVD Engine with Fault-Tolerant Hybrid Scoring",
    version="10.0",
    lifespan=lifespan  # تم ربط دورة الحياة هنا
)

# دمج مسارات الفيديوهات والمستخدمين
app.include_router(reel_router)
app.include_router(user_router)

# المسار الرئيسي (Root)
@app.get("/")
async def root():
    return {
        "status": "Online",
        "message": "Alluvo V10.0 Fault-Tolerant Hybrid Engine is running!",
        "background_jobs": "SVD Training scheduled daily at 03:00 AM",
        "endpoints": [
            "/api/reels/process",
            "/api/reels/update-metadata",
            "/api/reels/delete",
            "/api/users/recommend"
        ]
    }