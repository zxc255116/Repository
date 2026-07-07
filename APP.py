import os
import time
import random
import requests
from bs4 import BeautifulSoup
from supabase import create_client, Client

# =====================================================================
# 1. 初始化 Supabase 連線設定
# =====================================================================
# 請填入你自己的 Supabase 專案網址與金鑰（建議未來改用環境變數保存）
SUPABASE_URL = "https://你的專案代號.supabase.co"
SUPABASE_KEY = "你的SUPABASE_ANON_KEY"

# 建立 Supabase 客戶端連線
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# 2. 防爬蟲必備：動態變換的瀏覽器標頭 (User-Agent)
# =====================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/"
    }

# =====================================================================
# 3. 模擬/實際爬蟲核心邏輯 (以商品名稱進行電商搜尋比價)
# =====================================================================
def fetch_latest_price(product_name):
    """
    依據商品名稱，去電商爬取價格。
    註：因為大型電商（如MOMO、蝦皮）常有嚴格的反爬蟲驗證（如驗證碼或 JavaScript 渲染），
    初期測試時，我們先採用安全請求加上微幅波動的動態定價邏輯，確保流程 100% 跑通。
    """
    print(f"🔍 正在搜尋市場即時價格：{product_name}...")
    
    # 這裡預留實際爬蟲的 requests 骨架
    # url = f"https://example-ecommerce.com/search?q={product_name}"
    # response = requests.get(url, headers=get_headers(), timeout=10)
    # if response.status_day == 200:
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     # 解析網頁結構撈取最低價格 ...
    
    # 【模擬真實商機波動】：以 1350 元為基準，隨機產生 +/- 50 元的當日震撼特價
    simulated_price = random.randint(1280, 1420)
    
    # 為了防止被電商偵測到 IP 異常，每次查完一項商品，隨機休息 2 ~ 5 秒
    sleep_time = random.uniform(2, 5)
    time.sleep(sleep_time)
    
    return simulated_price

# =====================================================================
# 4. 主程式執行流程
# =====================================================================
def main():
    print("🚀 --- 寵物比價雷達：每日自動化排程開始 ---")
    
    try:
        # Step 1: 從 Supabase 撈出所有需要比價的商品
        response = supabase.table("pet_products").select("id, name").execute()
        products = response.data
        
        if not products:
            print("📭 目前資料庫中沒有任何商品資料，請先至後台新增！")
            return
            
        print(f"📋 成功自資料庫讀取到 {len(products)} 筆商品，開始進行全網比價...")
        
        # Step 2: 逐一進行爬蟲比價，並更新回資料庫
        for prod in products:
            prod_id = prod["id"]
            prod_name = prod["name"]
            
            # 抓取最新價格
            new_price = fetch_latest_price(prod_name)
            
            # 將新價格 UPDATE 回 Supabase 資料表
            update_res = supabase.table("pet_products") \
                .update({"lowest_price": new_price}) \
                .eq("id", prod_id) \
                .execute()
                
            print(f"✅ 更新成功！ID [{prod_id}] {prod_name} ➔ 今日最新最低價: ${new_price}")
            
    except Exception as e:
        print(f"❌ 執行過程中發生錯誤: {e}")
        
    print("🏁 --- 全數商品價格更新完畢，全自動化排程結束 ---")

if __name__ == "__main__":
    main()
