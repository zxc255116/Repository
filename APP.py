import os
import time
import random
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client
import streamlit as st

# =====================================================================
# 1. 自動讀取 Streamlit Secrets 安全金鑰
# =====================================================================
try:
    # 優先讀取 Streamlit 雲端保險箱的設定
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    # 如果在本地電腦執行，則讀取本地環境變數
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://你的專案代號.supabase.co")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "你的anon密鑰")

# 建立 100% 安全的雲端資料庫連線
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 防爬蟲設定：動態切換瀏覽器身份
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def fetch_latest_price(product_name):
    """模擬全網搜尋比價邏輯"""
    print(f"🔍 正在搜尋市場即時價格：{product_name}...")
    
    # 這裡未來可由 Python 爬蟲自動抓取 MOMO/蝦皮 實際數字
    # 目前先以 1350 元為基準，隨機產生 +/- 50 元的當日波動特價測試
    simulated_price = random.randint(1280, 1420)
    
    # 隨機休息 2-4 秒，防止速度太快被電商伺服器封鎖
    time.sleep(random.uniform(2, 4))
    return simulated_price

def main():
    print("🚀 --- 寵物比價雷達：自動化排程開始 ---")
    
    try:
        # Step 1: 從 Supabase 撈出所有需要比價的商品
        response = supabase.table("pet_products").select("id, name").execute()
        products = response.data
        
        if not products:
            print("📭 資料庫裡空空的，請先去 Supabase 塞入商品資料喔！")
            return
            
        print(f"📋 成功讀取到 {len(products)} 筆商品，開始更新價格...")
        
        # Step 2: 逐一進行比價並寫回資料庫
        for prod in products:
            prod_id = prod["id"]
            prod_name = prod["name"]
            
            # 獲取今日最新低價
            new_price = fetch_latest_price(prod_name)
            
            # 自動將最新價格 UPDATE 回 Supabase 雲端
            supabase.table("pet_products") \
                .update({"lowest_price": new_price}) \
                .eq("id", prod_id) \
                .execute()
                
            print(f"✅ 更新成功！ID [{prod_id}] {prod_name} ➔ 最新低價: ${new_price}")
            
    except Exception as e:
        print(f"❌ 執行發生錯誤: {e}")
        
    print("🏁 --- 全數商品價格更新完畢，排程結束 ---")

if __name__ == "__main__":
    main()
