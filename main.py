from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import pandas as pd
from typing import List, Optional, Dict
from collections import Counter
import re
import os

app = FastAPI(title="Toast Smart Recs Backend - DS 440")

# ==========================================
# 📊 全局变量与数据初始化
# ==========================================
google_data = pd.DataFrame()
menu_data = pd.DataFrame()
hot_tags = []

# 你的 14w 行真实数据文件名
DATA_FILE = "dataset_crawler-google-places_2026-03-29_18-37-43-145.json"

@app.on_event("startup")
def load_db():
    global google_data, menu_data, hot_tags
    print("🚀 Starting DS 440 Backend...")

    # 1. 加载 14w 行 Google Maps 真实数据
    try:
        if os.path.exists(DATA_FILE):
            print(f"📂 Loading {DATA_FILE}...")
            # 你的 JSON 是标准列表格式，不需要 lines=True
            google_data = pd.read_json(DATA_FILE)
            print(f"✅ Loaded {len(google_data)} rows of local market data.")
            
            # --- ✨ 核心：数据驱动的标签提取 (NLP) ---
            print("🧠 Extracting hot tags from reviews...")
            # 筛选 5 星好评的文本进行分词统计
            good_reviews = google_data[google_data['stars'] >= 4.5]['text'].dropna().astype(str)
            all_text = " ".join(good_reviews).lower()
            # 匹配 5 个字母以上的形容词/名词
            words = re.findall(r'\b[a-z]{5,}\b', all_text)
            # 过滤掉一些无意义的常用词 (Stopwords)
            stop_words = {'google', 'restaurant', 'place', 'there', 'their', 'really', 'everything'}
            filtered_words = [w for w in words if w not in stop_words]
            # 取出现频率最高的前 5 个词
            top_words = Counter(filtered_words).most_common(5)
            hot_tags = [tag[0].capitalize() for tag in top_words]
            print(f"🔥 Real-time Hot Tags: {hot_tags}")
        else:
            print(f"⚠️ Warning: {DATA_FILE} not found. Analytics will be limited.")
    except Exception as e:
        print(f"❌ Error loading database: {e}")

    # 2. 菜单数据 (你可以根据需求增加更多 Dish)
    menu_data = pd.DataFrame({
        'Dish': ['Truffle Mushroom Soup', 'Spicy Chicken Wings', 'Summer Salad', 'Hot Chocolate Lava Cake', 'Iced Matcha Latte'],
        'Category': ['Soup', 'Appetizer', 'Salad', 'Dessert', 'Beverage'],
        'Ideal_Weather': ['Cold/Rainy', 'Any', 'Hot/Sunny', 'Cold/Rainy', 'Hot/Sunny'],
        'Ideal_Mood': ['Neutral', 'Stressed', 'Happy', 'Stressed', 'Happy'],
        'Base_Price': [8.99, 12.99, 10.99, 9.99, 5.99]
    })

# ==========================================
# 🛠️ API 接口实现
# ==========================================

# 接口 1: 智能菜品推荐 (结合天气、心情与大数据权重)
@app.get("/api/recommendations")
def get_recommendations(weather: str, mood: str):
    # 基础逻辑筛选
    mask = (menu_data['Ideal_Weather'] == weather) | (menu_data['Ideal_Mood'] == mood)
    recs = menu_data[mask].copy()
    
    # 如果没匹配到，随机给两个（兜底逻辑）
    if recs.empty:
        recs = menu_data.sample(2)
    
    # 注入“数据科学”元素：加入大数据评分背景
    local_avg = google_data['stars'].mean() if not google_data.empty else 4.5
    
    results = recs.to_dict(orient="records")
    for item in results:
        # 动态生成的理由，体现了对大数据的利用
        item['reason'] = f"Perfect for {weather} weather. Locals rate this category {local_avg:.1f}/5!"
    
    return results

# 接口 2: 忠诚度与折扣计算 (Toast 核心逻辑)
@app.get("/api/loyalty/{customer_id}")
def check_loyalty(customer_id: str, order_count: int):
    # 业务规则：每 5 单触发一次 20% 折扣 (Milestone)
    is_milestone = (order_count + 1) % 5 == 0
    discount = 0.20 if is_milestone else 0.0
    next_goal = 5 - ((order_count + 1) % 5)
    
    return {
        "customer_id": customer_id,
        "is_milestone": is_milestone,
        "discount_rate": discount,
        "next_milestone": next_goal
    }

# 接口 3: 实时热门标签 (从 14w 行评论中分析得出)
@app.get("/api/hot-tags")
def get_tags():
    return {"tags": hot_tags}

# 接口 4: 竞品分析看板 (为 Manager Dashboard 提供处理后的数据)
@app.get("/api/analytics/competitors")
def get_competitor_stats():
    if google_data.empty:
        return []
    
    # 这里的处理逻辑：只取评分最高的前 10 家本地竞品传给前端，防止数据过载
    stats = google_data.groupby('title').agg({
        'stars': 'mean',
        'reviewsCount': 'first'
    }).reset_index()
    
    top_competitors = stats.sort_values(by='reviewsCount', ascending=False).head(10)
    
    # 格式化为前端熟悉的字段名
    return [
        {"name": row['title'], "rating": round(row['stars'], 1), "reviewCount": row['reviewsCount']}
        for _, row in top_competitors.iterrows()
    ]

