from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import pandas as pd
from typing import List, Optional, Dict
from collections import Counter
import re
import os

app = FastAPI(title="Toast Smart Recs Backend - DS 440")
from fastapi import Request
from fastapi.responses import JSONResponse
import threading

# ==========================================
# 🛡️ DEFENSE MECHANISM: Traffic Controller (Rate Limiter)
# ==========================================
active_requests = 0
request_lock = threading.Lock()
MAX_CONCURRENT_REQUESTS = 50 # Maximum number of users allowed at the exact same time

@app.middleware("http")
async def limit_traffic(request: Request, call_next):
    global active_requests
    
    with request_lock:
        if active_requests >= MAX_CONCURRENT_REQUESTS:
            # Gracefully reject extra requests with a 429 status code instead of crashing
            return JSONResponse(
                status_code=429, 
                content={"error": "⚠️ Server is currently experiencing high traffic. Please try again later."}
            )
        active_requests += 1

    try:
        response = await call_next(request)
        return response
    finally:
        with request_lock:
            active_requests -= 1
# ==========================================
# ==========================================
# 📊 全局变量与数据初始化
# ==========================================
google_data = pd.DataFrame()
menu_data = pd.DataFrame()
hot_tags = []

# 你的 14w 行真实数据文件名
DATA_FILE = "dataset_crawler-google-places_2026-03-29_18-37-43-145.json123"
# df = pd.read_csv(r'C:\Users\22805\Desktop\试验代码文件\poisoned_restaurant_data.csv')
# test_crash = df['Average_Cost'].mean()

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
    
    # --- 修复部分：通过计数来生成评论数 ---
    # 我们按餐厅名 (title) 分组
    # 'stars': 'mean' 计算平均分
    # 'title': 'count' 计算该餐厅出现了多少次（即有多少条评论）
    stats = google_data.groupby('title').agg({
        'stars': 'mean',
        'title': 'count' 
    }).rename(columns={'title': 'reviewCount'}).reset_index()
    
    # 排序并取前 10 名
    top_competitors = stats.sort_values(by='reviewCount', ascending=False).head(10)
    
    # 转换为前端需要的格式
    return [
        {
            "name": row['title'], 
            "rating": round(row['stars'], 1), 
            "reviewCount": int(row['reviewCount'])
        }
        for _, row in top_competitors.iterrows()
    ]
# ==========================================
# 🛡️ STRESS TEST: Defense Mechanism Verification
# ==========================================
import pandas as pd

print("\n--- 🛡️ Starting Defense Mechanism Test ---")
# try:
#     # 1. 读取我们制造的脏数据炸弹
#     df_test = pd.read_csv(r'C:\Users\22805\Desktop\试验代码文件\poisoned_restaurant_data.csv')
#     print("💣 Poisoned data loaded. Commencing cleaning...")
    
#     # 2. 清洗逻辑：强制转换数值，非数值变成 NaN
#     df_test['Rating'] = pd.to_numeric(df_test['Rating'], errors='coerce')
#     df_test['Average_Cost'] = pd.to_numeric(df_test['Average_Cost'], errors='coerce')
    
#     # 3. 逻辑过滤：踢掉不合理的评分和价格
#     df_test = df_test[(df_test['Rating'] >= 0) & (df_test['Rating'] <= 5)]
#     df_test = df_test[df_test['Average_Cost'] >= 0]
    
#     # 4. 尝试执行刚才让系统崩溃的计算
#     safe_mean = df_test['Average_Cost'].mean()
#     print(f"✅ Data cleaned successfully! Safe average cost calculated: {safe_mean}")

# except Exception as e:
#     # 如果真的遇到无法处理的绝境，系统也不会崩溃死掉
#     print(f"⚠️ Warning: Blocked bad data. Details: {e}")
# print("--- Test Complete ---\n")


# ==========================================
# 🎯 TARGET ENDPOINT FOR STRESS TEST
# ==========================================
# import time
# import uvicorn

# @app.get("/search")
# def dummy_search():
#     # Simulate a heavy database query taking 0.5 seconds
#     time.sleep(0.5) 
#     return {"message": "Search results found!"}

# # Start the server properly so it listens for requests
# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)

# ==========================================
# 🛡️ CASE 3 DEFENSE: Data Schema Validation
# ==========================================
print("\n🛡️ Testing Search Logic Resilience...")

# 1. First, check if the dataset is actually loaded and contains the required column
if 'name' not in google_data.columns:
    print("❌ CRITICAL ERROR: Column 'name' is missing from the database!")
    print("⚠️ Defense Triggered: Search operation aborted to prevent system crash.")
    # Here you can handle the error gracefully, maybe show a popup to the user
else:
    # 2. Only if the column exists, perform the filter
    print("✅ Schema check passed. Filtering data...")
    search_query = "NonExistentRestaurant_12345"
    filtered_df = google_data[google_data['name'] == search_query]
    
    # 3. Further defense: Check if any results were found
    if filtered_df.empty:
        print(f"ℹ️ Info: No restaurants found matching '{search_query}'.")
    else:
        print(f"✅ Success! Found {len(filtered_df)} matches.")

print("--- Case 3 Defense Test Complete ---\n")

