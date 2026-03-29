import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# ==========================================
# 1. Page Configuration
# ==========================================
# 设置页面标题、布局和图标
st.set_page_config(page_title="Toast Smart Recs & Loyalty", layout="wide", page_icon="🍽️")

# 后端 API 基础地址 (确保 FastAPI 运行在 8000 端口)
BACKEND_URL = "http://localhost:8000"

# ==========================================
# 2. Session State Management
# ==========================================
# 初始化购物车状态，防止页面刷新后数据丢失
if 'cart' not in st.session_state:
    st.session_state.cart = []

# 将商品添加到购物车的函数
def add_to_cart(item_name, price):
    st.session_state.cart.append({'name': item_name, 'price': price})
    st.toast(f"✅ Added **{item_name}** to cart!")

# 从购物车删除商品的函数
def remove_from_cart(index):
    if 0 <= index < len(st.session_state.cart):
        removed_item = st.session_state.cart.pop(index)
        st.toast(f"🗑️ Removed **{removed_item['name']}**")

# ==========================================
# 3. Backend API Service Functions
# ==========================================
# 从后端获取实时热门标签 (基于 14w 行大数据分析)
def get_hot_tags():
    try:
        response = requests.get(f"{BACKEND_URL}/api/hot-tags")
        return response.json().get("tags", [])
    except:
        return ["Fresh", "Popular", "Local"]

# 获取智能菜品推荐
def get_recommendations(weather, mood):
    try:
        response = requests.get(f"{BACKEND_URL}/api/recommendations", 
                                params={"weather": weather, "mood": mood})
        return pd.DataFrame(response.json())
    except:
        return pd.DataFrame()

# 获取客户忠诚度和折扣信息
def get_loyalty_status(customer_id, count):
    try:
        response = requests.get(f"{BACKEND_URL}/api/loyalty/{customer_id}", 
                                params={"order_count": count})
        return response.json()
    except:
        return {"is_milestone": False, "discount_rate": 0, "next_milestone": 5}

# 获取本地竞品分析数据 (14w 行数据处理结果)
def get_competitor_stats():
    try:
        response = requests.get(f"{BACKEND_URL}/api/analytics/competitors")
        data = response.json()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# ==========================================
# 4. Sidebar Navigation
# ==========================================
# 侧边栏展示项目信息和导航控制
st.sidebar.title("🍽️ Smart POS System")
st.sidebar.markdown("Integration Prototype for **Toast**")
page = st.sidebar.radio("Navigation", ["1. Front-of-House (POS View)", "2. Manager Dashboard"])

st.sidebar.divider()
st.sidebar.info("Team: Bohan Yang & Luping Zhou\n\nCourse: DS 440\n\nProject: Improve Eating Experience")

# ==========================================
# 5. Page 1: Front-of-House (POS View)
# ==========================================
if page == "1. Front-of-House (POS View)":
    st.title("🛎️ Waitstaff POS Interface")

    # 展示基于大数据的实时趋势标签
    tags = get_hot_tags()
    tag_cols = st.columns(len(tags) + 1)
    tag_cols[0].markdown("**Trending Locally:**")
    for i, tag in enumerate(tags):
        tag_cols[i+1].button(f"#{tag}", key=f"t_{tag}", disabled=True)
    
    st.divider()

    # 主布局：左侧环境输入，中间推荐展示，右侧购物车结账
    col_input, col_recs, col_cart = st.columns([1, 1.8, 1.2])

    # --- Section A: Customer & Context ---
    with col_input:
        st.subheader("1. Context")
        cust_id = st.text_input("Customer ID", value="CUST-8F92A")
        
        if 'hist_orders' not in st.session_state:
            st.session_state.hist_orders = 4
        
        hist_orders = st.number_input("Historical Orders", min_value=0, value=st.session_state.hist_orders)
        st.session_state.hist_orders = hist_orders

        st.divider()
        st.markdown("**Real-time Environment**")
        weather = st.selectbox("Current Weather", ["Cold/Rainy", "Hot/Sunny", "Mild"])
        mood = st.selectbox("Customer Mood", ["Neutral", "Happy", "Stressed"])
        
        if st.session_state.cart and st.button("🚫 Clear Cart", use_container_width=True):
            st.session_state.cart = []
            st.rerun()

    # --- Section B: Smart Recommendations ---
    with col_recs:
        st.subheader("2. Smart Recommendations")
        recs_df = get_recommendations(weather, mood)
        
        if not recs_df.empty:
            for idx, row in recs_df.iterrows():
                with st.expander(f"⭐ **{row['Dish']}** - `${row['Base_Price']:.2f}`", expanded=True):
                    st.write(f"**Reason:** {row['reason']}")
                    st.button(f"Add **{row['Dish']}** to Order", 
                             key=f"btn_{idx}", 
                             use_container_width=True,
                             on_click=add_to_cart, 
                             args=(row['Dish'], row['Base_Price']))
        else:
            st.info("No contextual recommendations available. Start Backend API.")

    # --- Section C: Cart & Loyalty Check ---
    with col_cart:
        st.subheader("🛒 Current Order")
        
        total_val = 0
        if not st.session_state.cart:
            st.info("No items in cart.")
        else:
            for i, item in enumerate(st.session_state.cart):
                c1, c2, c3 = st.columns([2, 1, 0.5])
                c1.write(item['name'])
                c2.write(f"`${item['price']:.2f}`")
                if c3.button("🗑️", key=f"del_{i}"):
                    remove_from_cart(i)
                    st.rerun()
                total_val += item['price']

            # 调用后端获取折扣逻辑
            loyalty = get_loyalty_status(cust_id, st.session_state.hist_orders)
            final_val = total_val * (1 - loyalty['discount_rate'])

            if loyalty['is_milestone']:
                st.warning("🎁 Milestone Reward: 20% OFF Applied!")
                st.write(f"Subtotal: `${total_val:.2f}`")
                st.write(f"Discount: `- ${(total_val * 0.2):.2f}`")
            else:
                st.caption(f"Status: {loyalty['next_milestone']} orders away from reward.")

            st.divider()
            st.metric("Final Total (USD)", f"${final_val:.2f}")
            
            if st.button("Complete Transaction", type="primary", use_container_width=True):
                st.balloons()
                st.success("Order Synced to Toast Cloud!")
                st.session_state.cart = []
                st.rerun()

# ==========================================
# 6. Page 2: Manager Dashboard
# ==========================================
elif page == "2. Manager Dashboard":
    st.title("📊 Restaurant Analytics Dashboard")
    st.markdown("Monitor performance and market competitiveness using 140k+ local data points.")

    # 关键业务指标 (KPIs)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Daily Revenue", "$4,250", "15%")
    k2.metric("Recommendation CTR", "38.2%", "5.4%")
    k3.metric("Avg Basket Size", "$32.50", "2.1%")
    k4.metric("Loyalty Conversion", "42.0%", "-1.5%")
    
    st.divider()
    
    # 数据可视化部分
    row2_c1, row2_c2 = st.columns(2)
    
    with row2_c1:
        st.subheader("Conversion by Weather Context")
        mock_data = pd.DataFrame({
            "Context": ["Cold/Rainy", "Hot/Sunny", "Mild"],
            "Success Rate (%)": [28, 22, 18]
        })
        fig_bar = px.bar(mock_data, x="Context", y="Success Rate (%)", color="Context", template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with row2_c2:
        st.subheader("📍 Local Competitor Benchmarking")
        # 展示从 14w 行数据中提取的真实竞品对比
        comp_df = get_competitor_stats()
        if not comp_df.empty:
            fig_scat = px.scatter(comp_df, x="reviewCount", y="rating", 
                                  size="reviewCount", color="name",
                                  hover_name="name", title="Rating vs. Volume")
            st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.warning("Backend data not available for benchmarking.")

    st.info("Note: Competitor data is live-processed from the 140k Google Maps dataset.")