import os
import streamlit as st
from supabase import create_client, Client

# =====================================================================
# 1. 頁面基本設定（手機端優化）
# =====================================================================
st.set_page_config(
    page_title="毛孩省錢比價雷達",
    page_icon="🐾",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 自訂網頁風格 CSS
st.markdown("""
    <style>
    .main { background-color: #fcf9f2; }
    .stButton>button {
        background-color: #ff9f43;
        color: white;
        border-radius: 10px;
        border: none;
        width: 100%;
    }
    .price-card {
        background-color: white;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. 安全讀取金鑰並連線 Supabase
# =====================================================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # 本地備用方案
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://你的專案代號.supabase.co")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "你的anon密鑰")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# 3. 網頁前端畫面呈現
# =====================================================================
st.title("🐾 毛孩處方與保健品：省錢比街雷達")
st.write("為您的生病毛孩減輕荷包負擔，全台各大電商即時最低價一覽！")

# 搜尋框
search_query = st.text_input("🔍 輸入想比價的處方飼料或保健品名稱：", placeholder="例如：皇家 腎臟、魚油...")

st.markdown("---")

try:
    # 從 Supabase 資料庫抓取最新的商品資料
    if search_query:
        # 如果用戶有輸入，就進行模糊搜尋
        response = supabase.table("pet_products").select("*").ilike("name", f"%{search_query}%").execute()
    else:
        # 預設顯示全部商品
        response = supabase.table("pet_products").select("*").execute()
        
    products = response.data

    if not products:
        st.warning("📭 目前搜尋不到相關商品，或是資料庫裡還是空的喔！")
    else:
        st.subheader("🔥 今日震撼最低價清單")
        
        # 逐一將資料庫的商品渲染成網頁卡片
        for prod in products:
            with st.container():
                st.markdown(f"""
                <div class="price-card">
                    <span style="background-color:#ffeaa7; padding:3px 8px; border-radius:5px; font-size:12px; color:#d63031; font-weight:bold;">
                        {prod['category']}
                    </span>
                    <h3 style="margin-top:5px; color:#2d3436;">{prod['name']}</h3>
                    <p style="font-size:20px; color:#27ae60; font-weight:bold; margin-bottom:10px;">
                        今日網購最低價：${int(prod['lowest_price'])} 元起
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # 建立兩大主要電商的跳轉按鈕
                col1, col2 = st.columns(2)
                with col1:
                    if prod.get('shopee_url'):
                        st.link_button("🛒 前往蝦皮商城購買", prod['shopee_url'])
                with col2:
                    if prod.get('momo_url'):
                        st.link_button("📦 前往 MOMO 購物網", prod['momo_url'])
                
                st.markdown("<br>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"❌ 無法連線至雲端資料庫，請檢查 Streamlit Secrets 設定！錯誤原因: {e}")
