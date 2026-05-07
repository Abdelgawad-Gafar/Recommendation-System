import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
import pickle
import os
from database import logger

class CFTrainer:
    def __init__(self, cache_file="svd_data/svd_results.pkl"):
        self.cache_file = cache_file

    def train_from_db(self, df):
        logger.info("Starting SVD training...")
        pivot = df.pivot_table(index='userId', columns='reelId', values='score', aggfunc='max').fillna(0)
        
        if pivot.empty or pivot.shape[1] < 2:
            logger.warning("Not enough data to train SVD.")
            return

        svd = TruncatedSVD(n_components=min(10, pivot.shape[1]-1))
        preds = np.dot(svd.fit_transform(pivot), svd.components_)
        
        data = {
            "matrix": preds,
            "user_idx": {str(id): i for i, id in enumerate(pivot.index)},
            "item_idx": {str(id): i for i, id in enumerate(pivot.columns)}
        }
        # الحفظ الآمن لضمان عدم توقف النظام (Zero Downtime)
        temp_file = self.cache_file + ".tmp"
        
        # 1. حفظ البيانات في ملف مؤقت
        with open(temp_file, "wb") as f:
            pickle.dump(data, f)
            
        # 2. استبدال الملف القديم بالجديد في خطوة واحدة سريعة (Atomic Replace)
        os.replace(temp_file, self.cache_file)
        
        logger.info("SVD matrix successfully updated with ZERO downtime.")

    def get_top_items_for_user(self, user_id, top_n=50):
        if not os.path.exists(self.cache_file):
            return []
        with open(self.cache_file, "rb") as f:
            d = pickle.load(f)
        
        u_idx = d["user_idx"].get(str(user_id))
        if u_idx is None:
            return []
        
        user_scores = d["matrix"][u_idx]
        item_ids = list(d["item_idx"].keys())
        
        # ترتيب الفيديوهات من الأعلى تقييماً للأقل
        sorted_indices = np.argsort(user_scores)[::-1]
        return [int(item_ids[i]) for i in sorted_indices[:top_n]]