import pandas as pd
import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. 加载数据
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_path, 'dataset_crawler-google-places_2026-03-29_18-37-43-145.json')

with open(file_path, 'r', encoding='utf-8') as f:
    df = pd.DataFrame(json.load(f))

# 2. 简单的菜品提取逻辑（这里你可以根据菜单手动列出，或者让 AI 自动提取）
# 假设我们关注以下几个热门关键词（你可以扩充这个列表）
menu_items = ['chicken', 'pizza', 'pasta', 'steak', 'burger', 'salad', 'pita', 'kabob', 'hummus']

# 3. 为每个菜品汇总评论
item_profiles = {}
for item in menu_items:
    # 找到所有提到这个菜品的评论
    related_reviews = df[df['text'].str.contains(item, case=False, na=False)]['text']
    # 汇总成一个大的描述文本
    item_profiles[item] = " ".join(related_reviews)

# 4. 使用 TF-IDF 向量化
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(list(item_profiles.values()))

# 5. 保存这个“推荐引擎”
joblib.dump((tfidf, tfidf_matrix, menu_items), 'dish_recommender.pkl')
print("✅ 智能推荐引擎训练完成！")