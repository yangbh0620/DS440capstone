import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# 页面基本配置
# ==========================================
st.set_page_config(page_title="Toast Smart Recs & Loyalty", layout="wide", page_icon="🍽️")

# --- 侧边栏导航 ---
st.sidebar.title("🍽️ Smart POS System")
st.sidebar.markdown("Integration Prototype for Toast")
page = st.sidebar.radio("Navigation", ["1. Front-of-House (POS View)", "2. Manager Dashboard"])

st.sidebar.divider()
st.sidebar.info("Team: Bohan Yang & Luping Zhou\n\nCourse: DS 440\n\nProject: Improve your eating experience")

# ==========================================
# 数据加载与整合 (整合真实爬取数据)
# ==========================================
@st.cache_data
def load_menu_data():
    return pd.DataFrame({
        'Dish': ['Truffle Mushroom Soup', 'Spicy Chicken Wings', 'Summer Salad', 'Hot Chocolate Lava Cake', 'Iced Matcha Latte'],
        'Category': ['Soup', 'Appetizer', 'Salad', 'Dessert', 'Beverage'],
        'Ideal_Weather': ['Cold/Rainy', 'Any', 'Hot/Sunny', 'Cold/Rainy', 'Hot/Sunny'],
        'Ideal_Mood': ['Neutral', 'Stressed', 'Happy', 'Stressed', 'Happy'],
        'Base_Price': [8.99, 12.99, 10.99, 9.99, 5.99]
    })

@st.cache_data
def load_google_data():
    try:
        # 读取你刚刚抓取的真实数据集
        df = pd.read_csv("dataset_google-maps-scraper_2026-03-05_01-37-24-459.csv")
        return df[['name', 'rating', 'reviewCount']].dropna().head(10)
    except Exception as e:
        return pd.DataFrame()

menu_df = load_menu_data()
google_df = load_google_data()

# ==========================================
# 页面 1: 前台点餐系统 (Phase 2 & 3)
# ==========================================
if page == "1. Front-of-House (POS View)":
    st.title("🛎️ Waitstaff POS Interface")
    st.markdown("Use real-time context to recommend dishes and track loyalty milestones.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("1. Context & Customer")
        customer_id = st.text_input("Customer ID (Hashed)", value="CUST-8F92A")
        orders_completed = st.number_input("Historical Order Count", min_value=0, value=4, step=1)
        
        st.divider()
        st.markdown("**Real-time Environmental Tags**")
        current_weather = st.selectbox("Current Weather", ["Cold/Rainy", "Hot/Sunny", "Mild"])
        current_mood = st.selectbox("Customer Mood (Optional)", ["Neutral", "Happy", "Stressed"])
        
        generate_btn = st.button("Generate Recommendations", type="primary")

    with col2:
        st.subheader("2. Smart Recommendations")
        if generate_btn:
            st.success("Recommendations generated!")
            
            # --- 模块 A: 单品推荐 ---
            st.markdown("### 🌟 Top Suggested Items")
            
            recommendations = menu_df[(menu_df['Ideal_Weather'] == current_weather) | (menu_df['Ideal_Mood'] == current_mood)].head(3)
            if recommendations.empty:
                recommendations = menu_df.head(2) 
                
            for index, row in recommendations.iterrows():
                with st.expander(f"⭐ **{row['Dish']}** - ${row['Base_Price']:.2f}"):
                    reason = ""
                    if row['Ideal_Weather'] == current_weather and current_weather == "Cold/Rainy":
                        reason = "It's cold/rainy today, how about a warm bowl of soup?"
                    elif row['Ideal_Weather'] == current_weather and current_weather == "Hot/Sunny":
                        reason = "Perfect refreshing choice for a hot and sunny day!"
                    elif row['Ideal_Mood'] == current_mood and current_mood == "Stressed":
                        reason = "Have a small cake to lift your spirits!"
                    else:
                        reason = "Suggested based on historical ordering patterns."
                    
                    st.write(f"**Contextual Reasoning:** {reason}")
                    
                    if not google_df.empty:
                        mock_google = google_df.sample(1).iloc[0]
                        st.info(f"📈 **Google Review Insights:** Rated **{mock_google['rating']} / 5.0** (Based on {int(mock_google['reviewCount'])} authentic reviews)")
                    
                    st.button(f"Add {row['Dish']} to Cart", key=f"add_single_{index}")
            
            # --- 模块 B: 新增的智能套餐 (Combo Deals) ---
            st.divider()
            st.markdown("### 🍱 Dynamic Combo Deal (Upselling)")
            
            # 自动挑选一个吃的和一个喝的来组合
            food_items = menu_df[menu_df['Category'].isin(['Soup', 'Appetizer', 'Salad'])]
            drink_items = menu_df[menu_df['Category'] == 'Beverage']
            
            if not food_items.empty and not drink_items.empty:
                # 尽量选符合当前天气的食物
                food_rec = food_items[food_items['Ideal_Weather'] == current_weather]
                selected_food = food_rec.iloc[0] if not food_rec.empty else food_items.iloc[0]
                selected_drink = drink_items.iloc[0]
                
                original_price = selected_food['Base_Price'] + selected_drink['Base_Price']
                combo_price = original_price * 0.90 # 给个 9 折
                
                with st.container(border=True):
                    st.write(f"**{selected_food['Dish']} + {selected_drink['Dish']}**")
                    st.write(f"Original: ~~${original_price:.2f}~~ ➡️ **Combo Price: ${combo_price:.2f}**")
                    st.caption(f"💡 System Hint: Recommend this pairing to increase average check size! Matched for {current_weather} weather.")
                    st.button("Add Combo to Cart", type="primary", use_container_width=True)

            # --- 模块 C: 忠诚度与优惠券 ---
            st.divider()
            st.markdown("### 🎟️ Loyalty Milestone Check")
            current_order_total = orders_completed + 1
            if current_order_total % 5 == 0:
                st.balloons()
                st.warning(f"**MILESTONE REACHED!** This is order #{current_order_total}. Triggering 20% OFF Coupon distribution automatically.")
            else:
                st.info(f"This is order #{current_order_total}. Needs {5 - (current_order_total % 5)} more orders for the next reward.")

# ==========================================
# 页面 2: 后台店长看板 (Phase 4)
# ==========================================
elif page == "2. Manager Dashboard":
    st.title("📊 Restaurant Analytics Dashboard")
    st.markdown("Monitor internal performance and external market competitiveness.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Orders (Today)", "142", "12%")
    col2.metric("Recommendation CTR", "34.5%", "4.2%")
    col3.metric("Combo Upsell Rate", "18.2%", "5.1%") # 把转化率改成了套餐追加率，更贴合功能
    col4.metric("Coupon Redemption Rate", "45.0%", "-2.1%")
    
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Conversion by Weather Context")
        chart_data = pd.DataFrame({
            "Context": ["Cold/Rainy", "Hot/Sunny", "Mild"],
            "Conversion Rate (%)": [22, 19, 15]
        })
        fig = px.bar(chart_data, x="Context", y="Conversion Rate (%)", color="Context", title="Context-Aware Conversion")
        st.plotly_chart(fig, use_container_width=True)
        
    with col_chart2:
        st.subheader("Coupon Milestone Funnel")
        funnel_data = dict(
            number=[1000, 200, 90],
            stage=["Coupons Issued", "Coupons Viewed", "Coupons Redeemed"]
        )
        fig2 = px.funnel(funnel_data, x='number', y='stage', title="Loyalty Coupon Performance")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    
    st.subheader("📍 Local Market Competitor Benchmarking")
    if not google_df.empty:
        st.markdown("Comparing our projected ratings against top local restaurants in State College area.")
        our_data = pd.DataFrame({'name': ['Our Toast POS Restaurant'], 'rating': [4.8], 'reviewCount': [150]})
        combined_df = pd.concat([our_data, google_df.head(6)])
        
        fig3 = px.scatter(combined_df, x="reviewCount", y="rating", 
                          size="reviewCount", color="name",
                          hover_name="name", size_max=40,
                          title="Competitor Analysis: Rating vs. Review Volume")
        fig3.update_layout(xaxis_title="Number of Google Reviews", yaxis_title="Average Rating")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Google Maps dataset not found. Please ensure the CSV file is in the same directory.")

    st.markdown("*Note: Competitor data is live-scraped from Google Maps for State College, PA.*")