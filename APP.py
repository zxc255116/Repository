import streamlit as st
import pandas as pd
import datetime
import requests
import time

st.set_page_config(page_title="台股全市場強勢選股器", layout="wide")

st.title("📈 智慧全台股：均線多頭 + 大股東吸籌選股")
st.caption("【穩定優化版】內建市場核心股票池，跳過不穩定的清單 API，專注計算技術面與大戶籌碼。")

# 你的永久 Token
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoienhjMjU1MTE2IiwiZW1haWwiOiJsb3ZlbWU4MDQyNEBnbWFpbC5jb20iLCJ0b2tlbl92ZXJzaW9uIjowfQ.4Eb5SRie0vj5L1Q6OrbSVe2_WcNKsrrekwKQsAPj420"

def fetch_data(dataset, kwargs={}):
    url = f"https://api.finmindtrade.com/v4/data?dataset={dataset}&token={FINMIND_TOKEN}"
    for k, v in kwargs.items():
        url += f"&{k}={v}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return pd.DataFrame(r.json()['data'])
    except:
        pass
    return pd.DataFrame()

# --- 側邊欄參數設定 ---
st.sidebar.header("⚙️ 選股參數設定")
holder_type = st.sidebar.selectbox("大股東持股定義", ["1,000張以上", "400張以上"], index=0)
holding_stage_map = {"1,000張以上": "1,000,000以上", "400張以上": "400,000-600,000"}
selected_stage = holding_stage_map[holder_type]

# 內建台股核心觀察池（包含你的自選股、熱門半導體、老牌電子、傳產等強勢主流股）
# 這樣可以直接避開 TaiwanStockInfo 斷線問題，且精準掃描主力最愛操作的股票
STOCK_POOL = {
    "1725": "元禎", "2204": "中華", "6443": "元晶", "5291": "邑昇",
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2382": "廣達",
    "3231": "緯創", "2308": "台達電", "2357": "華碩", "2324": "仁寶",
    "2301": "光寶科", "2303": "聯電", "2603": "長榮", "2609": "陽明",
    "2615": "萬海", "2618": "長榮航", "2610": "華航", "2881": "富邦金",
    "2882": "國泰金", "2891": "中信金", "2886": "兆豐金", "1301": "台塑",
    "1303": "南亞", "1326": "台化", "1101": "台泥", "2002": "中鋼"
}

# --- 主要選股流程 ---
if st.button("🚀 開始全市場掃描 (約需 1 分鐘)", type="primary"):
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    
    final_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(STOCK_POOL)
    
    for idx, (stock_id, stock_name) in enumerate(STOCK_POOL.items()):
        progress_bar.progress((idx + 1) / total_stocks)
        status_text.text(f"正在分析 {stock_id} {stock_name} 的技術線型...")
        
        time.sleep(0.05) # 微調延遲防止被鎖
        
        # 1. 抓歷史股價
        df_price = fetch_data("TaiwanStockPrice", {"stock_id": stock_id, "start_date": start_date})
        if df_price.empty or len(df_price) < 60:
            continue
            
        df_price = df_price.sort_values('date').reset_index(drop=True)
        df_price['MA5'] = df_price['close'].rolling(5).mean()
        df_price['MA10'] = df_price['close'].rolling(10).mean()
        df_price['MA20'] = df_price['close'].rolling(20).mean()
        df_price['MA60'] = df_price['close'].rolling(60).mean()
        
        p_latest = df_price.iloc[-1]
        
        # 條件 1 & 2：均線多頭排列且股價大於 20MA
        cond_ma = p_latest['MA5'] > p_latest['MA10'] > p_latest['MA20'] > p_latest['MA60']
        cond_price = p_latest['close'] > p_latest['MA20']
        
        if not (cond_ma and cond_price):
            continue
            
        # 條件 3：技術面過關，查大股東
        status_text.text(f"🔥 {stock_id} 技術面符合！正在驗證大戶籌碼...")
        df_share = fetch_data("TaiwanStockShareholding", {"stock_id": stock_id, "start_date": start_date})
        if df_share.empty:
            continue
            
        df_target_holder = df_share[df_share['holding_stage'] == selected_stage].sort_values('date').reset_index(drop=True)
        if len(df_target_holder) < 4:
            continue
            
        latest_share = df_target_holder.iloc[-1]['proportions']
        month_ago_share = df_target_holder.iloc[-4]['proportions']
        
        if latest_share > month_ago_share:
            final_results.append({
                "股票代號": stock_id,
                "股票名稱": stock_name,
                "今日收盤": p_latest['close'],
                "5MA": round(p_latest['MA5'], 2),
                "20MA": round(p_latest['MA20'], 2),
                f"最新{holder_type}%": f"{latest_share}%",
                "近月大戶增減": f"{round(latest_share - month_ago_share, 2)}%"
            })

    status_text.empty()

    if final_results:
        st.success(f"🔥 篩選完成！共有 {len(final_results)} 檔標的完全符合條件：")
        df_res = pd.DataFrame(final_results)
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("今日觀察池中暫無完全符合所有條件的股票。")
