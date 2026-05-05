from database import get_sql_conn, logger
from cf_trainer import CFTrainer
import pandas as pd

def sync_and_train():
    logger.info("Connecting to SQL Server to fetch real interactions...")
    conn = get_sql_conn()
    
    # استعلام حقيقي يجمع نقاط المشاهدة، الإعجابات، وشراء المنتجات
    query = """
    SELECT 
        v.UserId as userId,
        v.ReelId as reelId,
        (
            v.WatchedDurationSeconds * 1.0 / NULLIF(v.VideoDurationSeconds, 0) + 
            (SELECT COUNT(*) FROM BrandReviewLikes l WHERE l.UserId = v.UserId) * 1.5 +
            (SELECT COUNT(*) FROM OrderProducts op 
             JOIN ProductReels pr ON pr.ProductId = op.ProductId 
             WHERE pr.ReelId = v.ReelId) * 5.0
        ) as score
    FROM UserReelView v
    WHERE v.VideoDurationSeconds > 0
    """
    
    try:
        df = pd.read_sql(query, conn)
        if not df.empty:
            trainer = CFTrainer()
            trainer.train_from_db(df)
        else:
            logger.warning("Query returned empty dataframe.")
    except Exception as e:
        logger.error(f"Training failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    sync_and_train()