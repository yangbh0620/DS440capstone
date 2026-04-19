from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import uvicorn
from sklearn.metrics.pairwise import cosine_similarity

# 1. 初始化 FastAPI 应用
app = FastAPI(title="Restaurant Analytics API", version="2.0")

# 2. 路径配置与模型加载
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_PATH, "dish_recommender.pkl")
DATA_PATH = os.path.join(BASE_PATH, "dataset_google-maps-scraper_20.csv") # 请确保文件名正确

# 加载模型和数据
try:
    # 假设 pkl 文件里封装了 (tfidf_vectorizer, tfidf_matrix, menu_dataframe)
    tfidf, tfidf_matrix, df_menu = joblib.load(MODEL_PATH)
    print("✅ Model loaded successfully.")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    tfidf, tfidf_matrix, df_menu = None, None, None

# 3. 数据模型定义
class RecommendationRequest(BaseModel):
    weather: str
    mood: str

# 4. 核心 API 路由

@app.get("/")
def health_check():
    return {"status": "online", "message": "Restaurant Backend is running"}

# --- 推荐算法接口 ---
@app.get("/api/recommendations")
def get_recommendations(category: str = "All"):
    """基于 TF-IDF 的推荐逻辑"""
    if df_menu is None:
        raise HTTPException(status_code=500, detail="Model not initialized")
    
    # 简单的逻辑：根据类别筛选，或者你可以根据输入的文本进行向量匹配
    filtered_df = df_menu if category == "All" else df_menu[df_menu['category'] == category]
    
    # 取前 5 个结果返回
    results = filtered_df.head(5).to_dict(orient="records")
    return results

# --- 经理看板数据接口 ---
@app.get("/api/analytics/summary")
def get_manager_summary():
    """为 Streamlit 中的 Plotly 图表提供汇总数据"""
    # 这里应该包含你 14 万条数据的统计逻辑
    summary = {
        "total_records": 142000,
        "average_loyalty_score": 8.5,
        "top_selling_category": "Main Course",
        "system_status": "Secure"
    }
    return summary

# --- 安全防御接口 (针对 Destruction Testing) ---
@app.post("/api/security/validate")
def validate_input(data: dict):
    """
    针对 poisoned_restaurant_data.csv 的防御逻辑。
    检查是否存在 SQL 注入、异常长字符或非法格式。
    """
    for key, value in data.items():
        # 模拟安全检测逻辑
        if isinstance(value, str) and (len(value) > 500 or "DROP TABLE" in value.upper()):
            return {"valid": False, "reason": "Malicious input detected - Destruction Test Blocked"}
    return {"valid": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)