import time
import random
import urllib.parse
from supabase import create_client, Client

# =====================================================================
# 1. 初始化 Supabase 連線設定
# =====================================================================
SUPABASE_URL = "https://ykkncbfqrdslavsugreg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inlra25jYmZxcmRzbGF2c3VncmVnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODIzNDQ0NDUsImV4cCI6MjA5NzkyMDQ0NX0.x2p_mJlXZVEnZF7VkcJXGDb8opUPdoBMTydZiYf_ErQ"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================================
# 2. 自動產生電商關鍵字搜尋網址的邏輯
# =====================================================================
def generate_ecommerce_urls(product_name):
    """
    依據商品名稱，自動將中文字轉碼（URL Encode），
    並拼湊出蝦皮與 MOMO 官方的即時搜尋結果頁面網址。
    這樣使用者點過去，永遠都會看到該商品當下最新、最便宜的賣場清單！
    """
    # 將中文商品名稱轉換為網頁看得懂的編碼 (例如: "皇家 腎臟" 轉為 "%E7%9A%87%E5%AE%B6...")
    encoded_name = urllib.parse.quote(product_name)
    
    # 建立蝦皮與 MOMO 的即時搜尋網址（已帶入關鍵字）
    shopee_search_url = f"https://shopee.tw/search?keyword={encoded_name}"
    momo_search_url = f"https://www.momoshop.com.tw/search/searchMain.jsp?keyword={encoded_name}"
    
    return shopee_search_url, momo_search_url

def simulate_real_price(product_name):
    """模擬真實市場價格波動"""
    print(f"🔍 正在透過自動化排程分析市場價格: {product_name}")
    # 以 1350 為基準進行隨機上下波動測試
    return random.randint(1250, 1450)

# =====================================================================
# 3. 主程式執行流程
# =====================================================================
def main():
    print("🚀 --- 寵物比價雷達：全自動網址與價格同步開始 ---")
    
    try:
        # Step 1: 從 Supabase 撈出所有需要更新的商品
        response = supabase.table("pet_products").select("id, name").execute()
        products = response.data
        
        if not products:
            print("📭 資料庫中沒有商品資料。")
            return
            
        print(f"📋 成功讀取到 {len(products)} 筆商品，開始全自動化更新...")
        
        # Step 2: 逐一計算最新網址與價格，並 UPDATE 回雲端
        for prod in products:
            prod_id = prod["id"]
            prod_name = prod["name"]
            
            # 1. 全自動產生最新的搜尋結果網址
            shopee_url, momo_url = generate_ecommerce_urls(prod_name)
            
            # 2. 獲取最新價格
            new_price = simulate_real_price(prod_name)
            
            # 3. 把「新價格」加上「自動產生的精準搜尋網址」一併 UPDATE 回 Supabase
            supabase.table("pet_products").update({
                "lowest_price": new_price,
                "shopee_url": shopee_url,
                "momo_url": momo_url
            }).eq("id", prod_id).execute()
            
            print(f"✅ 自動同步成功！ID [{prod_id}] {prod_name}")
            print(f"   🔗 蝦皮連結更新為: {shopee_search_url}")
            print(f"   📦 MOMO 連結更新為: {momo_search_url}")
            print(f"   💰 今日最低價更新為: ${new_price}")
            
            # 稍微休息，模擬人類行為
            time.sleep(random.uniform(1, 2))
            
    except Exception as e:
        print(f"❌ 執行發生錯誤: {e}")
        
    print("🏁 --- 全自動網址與價格更新完畢 ---")

if __name__ == "__main__":
    main()
