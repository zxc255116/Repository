import streamlit as st
import pandas as pd
import datetime
import requests
import time

st.set_page_config(page_title="台股全市場強勢選股器", layout="wide")

st.title("📈 智慧全台股：均線多頭 + 大股東吸籌選股")
st.caption("【自動同步 API 版】直接線上抓取證交所與櫃買中心所有最新股票，免複製代碼，絕不短缺。")

FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoienhjMjU1MTE2IiwiZW1haWwiOiJsb3ZlbWU4MDQyNEBnbWFpbC5jb20iLCJ0b2tlbl92ZXJzaW9uIjowfQ.4Eb5SRie0vj5L1Q6OrbSVe2_WcNKsrrekwKQsAPj420"

def fetch_data(dataset, kwargs={}):
    url = f"https://api.finmindtrade.com/v4/data?dataset={dataset}&token={FINMIND_TOKEN}"
    for k, v in kwargs.items():
        url += f"&{k}={v}"
    try:
        r = requests.get(url, timeout=10)
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

# --- 主要選股流程 ---
if st.button("🚀 開始全市場上市上櫃強勢掃描", type="primary"):
    with st.spinner("正在向 FinMind 伺服器同步最新上市上櫃股票清單..."):
        # 直接從 API 抓取全台灣所有股票基本資料
        df_info = fetch_data("TaiwanStockInfo")
        if df_info.empty:
            st.error("無法取得股票清單，請檢查網路或 API Token！")
            st.stop()
        
        # 過濾出正常的上市與上櫃普通股（剔除權證、ETF、特別股）
        df_normal = df_info[
            (df_info['type'].isin(['twse', 'tpex'])) & 
            (df_info['stock_id'].str.len() == 4) & 
            (df_info['stock_id'].str.isdigit())
        ]
        ALL_STOCKS_LIST = df_normal['stock_id'].unique().tolist()
        ALL_STOCKS_LIST.sort()

    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    
    st.success(f"🔥 成功線上加載共 {len(ALL_STOCKS_LIST)} 檔上市上櫃股票清單！開始逐一過濾...")
        
    final_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_stocks = len(ALL_STOCKS_LIST)
    
    for idx, stock_id in enumerate(ALL_STOCKS_LIST):
        progress_bar.progress((idx + 1) / total_stocks)
        
        if idx % 5 == 0:
            status_text.text(f"進度: {idx + 1} / {total_stocks} 檔 | 正在掃描個股代號: {stock_id}")
            
        time.sleep(0.01)
        
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
            
        # 條件 3：技術面初篩過關，才查大股東
        df_share = fetch_data("TaiwanStockShareholding", {"stock_id": stock_id, "start_date": start_date})
        if df_share.empty:
            continue
            
        df_target_holder = df_share[df_share['holding_stage'] == selected_stage].sort_values('date').reset_index(drop=True)
        if len(df_target_holder) < 4:
            continue
            
        latest_share = df_target_holder.iloc[-1]['proportions']
        month_ago_share = df_target_holder.iloc[-4]['proportions']
        
        if latest_share > month_ago_share:
            # 取得股票名稱
            stock_name = df_normal[df_normal['stock_id'] == stock_id]['stock_name'].values[0]
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
        st.success(f"🔥 篩選完成！全市場共有 {len(final_results)} 檔完全符合條件：")
        df_res = pd.DataFrame(final_results)
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("今日全台股市中，暫時沒有完全符合所有條件的股票。")
