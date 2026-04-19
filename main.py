from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
import os
import uvicorn
import random
import json

# ==========================================
# 1. 初始化 FastAPI 应用
# ==========================================
app = FastAPI(
    title="Restaurant Analytics API",
    description="Backend for DS 440 Capstone Project - Team: Bohan Yang & Luping Zhou",
    version="2.2"
)

# ==========================================
# 2. 路径配置
# ==========================================
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_PATH, "dish_recommender.pkl")
JSON_PATH = os.path.join(BASE_PATH, "dataset_crawler-google-places_2026-03-29_18-37-43-145.json")
CSV_PATH = os.path.join(BASE_PATH, "dataset_google-maps-scraper_2026-03-05_01-37-24-459.csv")

tfidf = None
tfidf_matrix = None
df_menu = None
reviews_df = None

# ==========================================
# 3. 加载模型和数据
# ==========================================
def load_resources():
    global tfidf, tfidf_matrix, df_menu, reviews_df

    # 先加载 JSON 评论数据
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                reviews_df = pd.DataFrame(json.load(f))
            print(f"✅ Loaded review JSON ({len(reviews_df)} rows).")
        except Exception as e:
            print(f"⚠️ Failed to load JSON file: {e}")
            reviews_df = None
    else:
        reviews_df = None
        print("⚠️ JSON review file not found.")

    # 优先加载 pkl 模型
    if os.path.exists(MODEL_PATH):
        try:
            # dataclean.py 保存的是 (tfidf, tfidf_matrix, menu_items)
            loaded = joblib.load(MODEL_PATH)
            tfidf, tfidf_matrix, menu_items = loaded

            # 把列表转成 DataFrame，避免 sample() 报错
            df_menu = pd.DataFrame({"Dish": menu_items})

            print("✅ Model and menu items loaded successfully from PKL.")
            return
        except Exception as e:
            print(f"⚠️ Failed to load PKL model: {e}")

    # pkl 失败时再尝试 CSV
    if os.path.exists(CSV_PATH):
        try:
            df_menu = pd.read_csv(CSV_PATH)
            print(f"✅ Loaded raw CSV fallback ({len(df_menu)} rows).")
        except Exception as e:
            print(f"⚠️ Failed to load CSV fallback: {e}")
            df_menu = None
    else:
        df_menu = None
        print("❌ No menu/model data source found.")

load_resources()

# ==========================================
# 4. 数据模型
# ==========================================
class SecurityCheck(BaseModel):
    input_data: dict

# ==========================================
# 5. 基础接口
# ==========================================
@app.get("/")
def health_check():
    return {
        "status": "online",
        "project": "Toast Smart Recs",
        "team": "Bohan Yang & Luping Zhou"
    }

# ==========================================
# 6. 推荐接口
# ==========================================
@app.get("/api/recommendations")
def get_recommendations(weather: str = "Mild", mood: str = "Neutral"):
    if df_menu is None or len(df_menu) == 0:
        return []

    recs = df_menu.copy()

    # 如果 CSV 读入时列名不一致，做兼容映射
    if "Dish" not in recs.columns:
        column_mapping = {
            "name": "Dish",
            "title": "Dish"
        }
        recs = recs.rename(columns=column_mapping)

    # 如果还是没有 Dish，直接返回空
    if "Dish" not in recs.columns:
        return []

    sample_size = min(3, len(recs))
    recs = recs.sample(sample_size).copy()

    # 前端需要 Base_Price
    if "Base_Price" not in recs.columns:
        if "price" in recs.columns:
            recs["Base_Price"] = recs["price"]
        elif "average_price" in recs.columns:
            recs["Base_Price"] = recs["average_price"]
        else:
            recs["Base_Price"] = [round(random.uniform(10.0, 25.0), 2) for _ in range(sample_size)]

    reasons = {
        "Cold/Rainy": "Perfect warm comfort food for a chilly day.",
        "Hot/Sunny": "Refreshing choice to beat the heat!",
        "Mild": "A balanced choice for today’s weather.",
        "Stressed": "A little treat to help you relax.",
        "Happy": "Celebrate your mood with this local favorite!",
        "Neutral": "A popular choice among PSU students!"
    }

    reason_text = reasons.get(weather, reasons.get(mood, "A popular choice among PSU students!"))
    recs["reason"] = reason_text

    return recs[["Dish", "Base_Price", "reason"]].to_dict(orient="records")

# ==========================================
# 7. 热门标签接口
# ==========================================
@app.get("/api/hot-tags")
def get_hot_tags():
    return {"tags": ["Fresh", "Popular", "Local", "PSU-Special", "Fast-Service"]}

# ==========================================
# 8. 忠诚度接口
# ==========================================
@app.get("/api/loyalty/{customer_id}")
def get_loyalty(customer_id: str, order_count: int = 0):
    is_milestone = order_count >= 5 and (order_count % 5 == 0)
    next_milestone = 5 - (order_count % 5)
    if next_milestone == 0:
        next_milestone = 5

    return {
        "customer_id": customer_id,
        "is_milestone": is_milestone,
        "discount_rate": 0.2 if is_milestone else 0.0,
        "next_milestone": next_milestone
    }

# ==========================================
# 9. 经理看板汇总接口
# ==========================================
@app.get("/api/analytics/summary")
def get_manager_summary():
    total_records = len(reviews_df) if reviews_df is not None else 0

    avg_rating = None
    if reviews_df is not None and "stars" in reviews_df.columns:
        try:
            avg_rating = round(pd.to_numeric(reviews_df["stars"], errors="coerce").mean(), 2)
        except Exception:
            avg_rating = None

    return {
        "total_records_processed": total_records,
        "average_rating": avg_rating,
        "top_selling_category": "Main Course",
        "daily_active_users": 124,
        "system_status": "Secure"
    }

# ==========================================
# 10. 竞品分析接口
# ==========================================
@app.get("/api/analytics/competitors")
def get_competitor_stats():
    if reviews_df is not None and "title" in reviews_df.columns and "stars" in reviews_df.columns:
        try:
            temp = reviews_df.copy()
            temp["stars"] = pd.to_numeric(temp["stars"], errors="coerce")

            grouped = (
                temp.groupby("title", dropna=True)
                .agg(
                    rating=("stars", "mean"),
                    reviewCount=("title", "size")
                )
                .reset_index()
                .rename(columns={"title": "name"})
            )

            grouped["rating"] = grouped["rating"].round(2)
            grouped = grouped.sort_values(by="reviewCount", ascending=False).head(10)

            return grouped[["name", "rating", "reviewCount"]].to_dict(orient="records")
        except Exception as e:
            print(f"⚠️ Competitor stats generation failed: {e}")

    return [
        {"name": "McLanahan's", "rating": 4.5, "reviewCount": 1240},
        {"name": "Cozy Thai", "rating": 4.7, "reviewCount": 890},
        {"name": "Champs Sports Grill", "rating": 4.3, "reviewCount": 2150},
        {"name": "The Tavern", "rating": 4.6, "reviewCount": 560},
        {"name": "Corner Room", "rating": 4.2, "reviewCount": 1100}
    ]

# ==========================================
# 11. 安全检测接口
# ==========================================
@app.post("/api/security/validate")
def validate_input(payload: SecurityCheck):
    for key, value in payload.input_data.items():
        if isinstance(value, str):
            malicious_patterns = ["DROP", "DELETE", "SELECT *", "--"]
            if any(pattern in value.upper() for pattern in malicious_patterns) or len(value) > 500:
                raise HTTPException(
                    status_code=403,
                    detail="Security Alert: Potential malicious input detected."
                )
    return {"status": "Clean", "message": "Input passed destruction testing."}

# ==========================================
# 12. 启动入口
# ==========================================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)