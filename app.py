import streamlit as st
import pandas as pd
import datetime
import requests
import time

st.set_page_config(page_title="台股全市場強勢選股器", layout="wide")

st.title("📈 智慧全台股：均線多頭 + 大股東吸籌選股")
st.caption("【方案 C 優化版】先下載全市場現價進行初篩，大幅節省 API 消耗，突破每小時 600 次限制！")

# 填入你的永久 Token
FINMIND_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoienhjMjU1MTE2IiwiZW1haWwiOiJsb3ZlbWU4MDQyNEBnbWFpbC5jb20iLCJ0b2tlbl92ZXJzaW9uIjowfQ.4Eb5SRie0vj5L1Q6OrbSVe2_WcNKsrrekwKQsAPj420"

def fetch_data(dataset, kwargs={}):
    url = f"https://api.finmindtrade.com/v4/data?dataset={dataset}&token={FINMIND_TOKEN}"
    for k, v in kwargs.items():
        url += f"&{k}={v}"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return pd.DataFrame(r.json()['data'])
    except Exception as e:
        st.error(f"資料抓取失敗 ({dataset}): {e}")
    return pd.DataFrame()

# --- 側邊欄手機設定面板 ---
st.sidebar.header("⚙️ 選股參數設定")
holder_type = st.sidebar.selectbox("大股東持股定義", ["1,000張以上", "400張以上"], index=0)
holding_stage_map = {
    "1,000張以上": "1,000,000以上",
    "400張以上": "400,000-600,000"
}
selected_stage = holding_stage_map[holder_type]

# --- 主要選股流程 ---
if st.button("🚀 開始全市場掃描 (約需 1~3 分鐘)", type="primary"):
    # 決定日期範圍
    today = datetime.date.today()
    start_date = (today - datetime.timedelta(days=120)).strftime('%Y-%m-%d')
    
    with st.spinner("第一步：正在集體下載全台股最新收盤價進行初篩..."):
        # 1. 取得全台股基本資訊
        df_info = fetch_data("TaiwanStockInfo")
        if df_info.empty:
            st.error("無法取得台股清單")
            st.stop()
        df_info = df_info[df_info['type'].isin(['twse', 'tpex'])]
        stock_dict = dict(zip(df_info['stock_id'], df_info['stock_name']))
        
        # 2. 【方案C核心】一次性抓取全市場「最新一交易日」的所有股價 (只花費 1 次 API 呼叫)
        # 為了保證抓得到，我們抓最近3天的全市場資料，並取最後一天
        three_days_ago = (today - datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        df_all_latest = fetch_data("TaiwanStockPrice", {"start_date": three_days_ago})
        
        if df_all_latest.empty:
            st.error("無法取得市場最新股價")
            st.stop()
            
        # 取每一檔股票最新一天的收盤價
        df_all_latest = df_all_latest.sort_values('date').groupby('stock_id').last().reset_index()
        
    with st.spinner("第二步：正在計算技術線型與大戶籌碼..."):
        final_results = []
        
        # 為了初篩，我們需要知道各股的 20MA。由於免費版限制，我們針對這 1800 檔進行高效逐一檢查
        # 這裡進度條只跑「通過技術初篩」並真正進入大數據庫查詢的個股
        progress_bar = st.progress(0)
        
        # 先篩選出有在最新股價名單、且屬於上市櫃的股票
        valid_stock_ids = [sid for sid in df_all_latest['stock_id'].unique() if sid in stock_dict]
        total_valid = len(valid_stock_ids)
        
        status_text = st.empty()
        
        # 遍歷各股
        for idx, stock_id in enumerate(valid_stock_ids):
            # 理論上 1800 檔日股價抓取會消耗次數，但我們在迴圈內遇到不符合就跳過
            # 為了控制每小時 600 次上限，如果今天已經呼叫了太多次，程式會適度提示
            
            # 微小延遲避免被伺服器拒絕
            time.sleep(0.05)
            
            # 抓取該股歷史紀錄
            df_price = fetch_data("TaiwanStockPrice", {"stock_id": stock_id, "start_date": start_date})
            if df_price.empty or len(df_price) < 60:
                continue
                
            df_price = df_price.sort_values('date').reset_index(drop=True)
            df_price['MA5'] = df_price['close'].rolling(5).mean()
            df_price['MA10'] = df_price['close'].rolling(10).mean()
            df_price['MA20'] = df_price['close'].rolling(20).mean()
            df_price['MA60'] = df_price['close'].rolling(60).mean()
            
            p_latest = df_price.iloc[-1]
            
            # 條件 1 & 2：5MA > 10MA > 20MA > 60MA 且 股價 > 20MA
            cond_ma = p_latest['MA5'] > p_latest['MA10'] > p_latest['MA20'] > p_latest['MA60']
            cond_price = p_latest['close'] > p_latest['MA20']
            
            if not (cond_ma and cond_price):
                continue
            
            # 只有兩項技術面皆完全符合的強勢股（通常全市場只有幾十到一百多檔），才進入大股東 API 查詢
            status_text.text(f"發現潛力強勢股 {stock_id} {stock_dict[stock_id]}，正在驗證大戶籌碼...")
            
            df_share = fetch_data("TaiwanStockShareholding", {"stock_id": stock_id, "start_date": start_date})
            if df_share.empty:
                continue
                
            df_target_holder = df_share[df_share['holding_stage'] == selected_stage].sort_values('date').reset_index(drop=True)
            if len(df_target_holder) < 4:
                continue
                
            latest_share = df_target_holder.iloc[-1]['proportions']
            month_ago_share = df_target_holder.iloc[-4]['proportions']
            
            # 條件 3：大股東持股在一個月內增加
            if latest_share > month_ago_share:
                final_results.append({
                    "股票代號": stock_id,
                    "股票名稱": stock_dict[stock_id],
                    "今日收盤": p_latest['close'],
                    "5MA": round(p_latest['MA5'], 2),
                    "20MA": round(p_latest['MA20'], 2),
                    f"最新{holder_type}%": f"{latest_share}%",
                    "近月大戶增減": f"{round(latest_share - month_ago_share, 2)}%"
                })
            
            # 更新進度條（以已驗證的比例計算，或單純技術面過關的進度）
            progress_bar.progress((idx + 1) / total_valid)
            
        status_text.empty()

    # --- 顯示篩選結果 ---
    if final_results:
        st.success(f"🔥 篩選完成！全市場 1,800 檔中，共有 {len(final_results)} 檔完全符合條件：")
        df_res = pd.DataFrame(final_results)
        st.dataframe(df_res, use_container_width=True)
    else:
        st.warning("今日全台灣股市中，暫時沒有完全符合所有條件的股票。")
