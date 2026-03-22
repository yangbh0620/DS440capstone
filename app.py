import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ==========================================
# 页面基本配置
# ==========================================
st.set_page_config(page_title="Toast Smart Recs & Loyalty", layout="wide", page_icon="🍽️")

# ==========================================
# ✨ 核心增强：购物车状态管理 ✨
# ==========================================
# 必须在页面加载之初初始化 st.session_state
# st.session_state.cart 是一个列表，里面存放字典，如 [{'name': 'Soup', 'price': 8.99}, ...]
if 'cart' not in st.session_state:
    st.session_state.cart = []

# 定义加入购物车的回调函数
def add_to_cart(item_name, price):
    # 将商品（字典形式）添加到 session_state 列表中
    st.session_state.cart.append({'name': item_name, 'price': price})
    st.toast(f"✅ Added **{item_name}** to cart!") # 弹窗提示，体验更好

# 定义从购物车删除的回调函数
def remove_from_cart(index):
    # 根据索引删除商品
    if 0 <= index < len(st.session_state.cart):
        removed_item = st.session_state.cart.pop(index)
        st.toast(f"🗑️ Removed **{removed_item['name']}**")

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
        # 读取你抓取的真实数据集 (确保文件名正确且在同一目录下)
        df = pd.read_csv("dataset_google-maps-scraper_2026-03-05_01-37-24-459.csv")
        return df[['name', 'rating', 'reviewCount']].dropna().head(10)
    except Exception as e:
        return pd.DataFrame()

menu_df = load_menu_data()
google_df = load_google_data()

# ==========================================
# 侧边栏导航
# ==========================================
st.sidebar.title("🍽️ Smart POS System")
st.sidebar.markdown("Integration Prototype for Toast")
page = st.sidebar.radio("Navigation", ["1. Front-of-House (POS View)", "2. Manager Dashboard"])

st.sidebar.divider()
st.sidebar.info("Team: Bohan Yang & Luping Zhou\n\nCourse: DS 440\n\nProject: Improve your eating experience")

# ==========================================
# 页面 1: 前台点餐系统 (Phase 2, 3, 5 - Cart Enhanced)
# ==========================================
if page == "1. Front-of-House (POS View)":
    st.title("🛎️ Waitstaff POS Interface")
    
    # 将布局改为 3 列，最后一列留给购物车
    col1, col2, col3 = st.columns([1, 1.8, 1.2]) # 调整了比例
    
    with col1:
        st.subheader("1. Context & Customer")
        customer_id = st.text_input("Customer ID (Hashed)", value="CUST-8F92A")
        
        # 将历史订单数也存入 session_state，防止刷新丢失
        if 'orders_completed' not in st.session_state:
            st.session_state.orders_completed = 4
        
        orders_completed = st.number_input("Historical Order Count", min_value=0, value=st.session_state.orders_completed, step=1)
        st.session_state.orders_completed = orders_completed # 更新状态

        st.divider()
        st.markdown("**Real-time Environmental Tags**")
        current_weather = st.selectbox("Current Weather", ["Cold/Rainy", "Hot/Sunny", "Mild"])
        current_mood = st.selectbox("Customer Mood (Optional)", ["Neutral", "Happy", "Stressed"])
        
        # 增加一个清空购物车的按钮，方便测试
        if st.session_state.cart:
            if st.button("🚫 Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

    with col2:
        st.subheader("2. Smart Recommendations")
        
        # --- 模块 A: 单品推荐 ---
        st.markdown("### 🌟 Contextual Suggestions")
        
        # 简单的筛选逻辑，这里假设推荐按钮被“隐式”点击，直接展示符合当前天气的
        recommendations = menu_df[(menu_df['Ideal_Weather'] == current_weather) | (menu_df['Ideal_Mood'] == current_mood)].head(2)
        if recommendations.empty:
            recommendations = menu_df.sample(2) 
            
        for index, row in recommendations.iterrows():
            with st.expander(f"⭐ **{row['Dish']}** - `${row['Base_Price']:.2f}`", expanded=True):
                reason = f"Perfect choice for {current_weather} weather."
                
                st.write(f"**Reason:** {reason}")
                
                if not google_df.empty:
                    mock_google = google_df.sample(1).iloc[0]
                    st.caption(f"📈 Rated **{mock_google['rating']} / 5.0** locally")
                
                # ✨ 修改：加入购物车按钮，关联回调函数 ✨
                st.button(f"Add **{row['Dish']}** to Cart", 
                          key=f"add_single_{index}_{row['Dish']}", # 键必须唯一
                          use_container_width=True,
                          on_click=add_to_cart, # 绑定加入购物车函数
                          args=(row['Dish'], row['Base_Price'])) # 传递参数
        
        # --- 模块 B: 智能套餐 (Combo Deals) ---
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
            combo_name = f"{selected_food['Dish']} + {selected_drink['Dish']} (Combo)"
            
            with st.container(border=True):
                st.markdown(f"🍔 **{selected_food['Dish']}** : `${selected_food['Base_Price']:.2f}`")
                st.markdown(f"🥤 **{selected_drink['Dish']}** : `${selected_drink['Base_Price']:.2f}`")
                
                st.divider() 
                
                st.markdown(f"Original: ~~${original_price:.2f}~~ ➡️ **Combo: ${combo_price:.2f}**")
                
                # ✨ 修改：加入购物车按钮，关联回调函数 ✨
                st.button("Add **Combo Deal** to Cart", 
                          key="add_combo_btn", # 唯一键
                          type="primary", 
                          use_container_width=True,
                          on_click=add_to_cart, # 绑定函数
                          args=(combo_name, combo_price)) # 传递 Combo 名字和折扣价

    # ==========================================
    # ✨ 核心增强：右侧实时的购物车界面 (Col3) ✨
    # ==========================================
    with col3:
        st.subheader("🛒 Current Order")
        
        cart_items = st.session_state.cart
        
        if not cart_items:
            st.info("Cart is empty. Add items from the suggestions.")
        else:
            total_price = 0
            # 循环购物车里的商品，展示名字、价格和删除按钮
            for idx, item in enumerate(cart_items):
                # 使用 container 装饰每一项，排版更好看
                with st.container(border=False):
                    c_name, c_price, c_del = st.columns([2, 1, 0.5])
                    c_name.write(f"**{item['name']}**")
                    c_price.write(f"`${item['price']:.2f}`")
                    
                    # ✨ 核心功能：能从购物车删除的界面 ✨
                    # 使用唯一的 key 绑定 remove 回调函数
                    if c_del.button("🗑️", key=f"del_{idx}_{item['name']}"):
                        remove_from_cart(idx)
                        st.rerun() # 删除后需要立即强制刷新页面更新列表
                    
                    st.divider()
                    total_price += item['price']
            
            # --- 模块 C: 忠诚度与优惠券 ---
            # 检查这个订单是否是忠诚度里程碑
            current_order_total_count = st.session_state.orders_completed + 1
            is_milestone = (current_order_total_count % 5 == 0)
            
            final_price = total_price
            
            if is_milestone:
                discount = total_price * 0.20
                final_price = total_price * 0.80
                with st.container(border=True):
                    st.warning(f"🎁 **Milestone Discount Applied (20% OFF)!**")
                    st.caption(f"This is order #{current_order_total_count} for this hashed customer.")
                    st.write(f"Subtotal: `${total_price:.2f}`")
                    st.write(f"Discount: `- ${discount:.2f}`")
            else:
                next_milestone = 5 - (current_order_total_count % 5)
                st.caption(f"Order #{current_order_total_count}. {next_milestone} more order(s) for a 20% OFF reward.")

            # 展示总价
            st.divider()
            st.metric("Total (USD)", f"${final_price:.2f}")
            
            # 提交订单按钮 (Mock)
            if st.button("Complete Order & Check Out", type="primary", use_container_width=True):
                if total_price > 0:
                    st.balloons()
                    st.success("Order received by Toast! (Simulated Check Out)")
                    # 这里如果是真实 POS，会清空购物车并更新数据库，这里略过
                    st.session_state.cart = [] # 模拟结账后清空
                    st.rerun()
                else:
                    st.error("Cart is empty.")

# ==========================================
# 页面 2: 后台店长看板 (Phase 4)
# ==========================================
elif page == "2. Manager Dashboard":
    st.title("📊 Restaurant Analytics Dashboard")
    # ... Dashboard 代码保持不变，省略以节省空间，直接把之前的 Dashboard 代码粘贴到这里即可 ...
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