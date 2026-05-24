import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis.fundamental_analysis import build_fundamental_summary
from src.analysis.scoring import calculate_phase1_score, judgment_from_score
from src.analysis.technical_analysis import add_technical_indicators
from src.analysis.valuation_analysis import valuation_comment
from src.data.fundamental_data import get_fundamental_snapshot
from src.data.price_data import get_latest_price_stats, get_price_history
from src.utils.config import PERIOD_OPTIONS
from src.utils.formatting import format_number, format_percent
from src.utils.ticker_utils import normalize_ticker

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("株式投資分析ツール（Phase 1 MVP）")
st.caption("これは投資助言ではありません。最終判断は自己責任で行ってください。")

with st.sidebar:
    ticker_raw = st.text_input("ティッカー", value="AAPL", help="例: AAPL, NVDA, 7203.T")
    period_label = st.selectbox("分析期間", list(PERIOD_OPTIONS.keys()), index=3)
    run = st.button("分析開始", type="primary")

if run:
    ticker = normalize_ticker(ticker_raw)
    if not ticker:
        st.error("ティッカーを入力してください。")
        st.stop()

    with st.spinner("データを取得中..."):
        try:
            price_df = get_price_history(ticker, PERIOD_OPTIONS[period_label])
            price_df = add_technical_indicators(price_df)
        except Exception as e:
            st.error(f"株価データの取得に失敗: {e}")
            st.stop()

        try:
            fund = get_fundamental_snapshot(ticker)
        except Exception as e:
            fund = {}
            st.warning(f"ファンダメンタル取得エラー: {e}")

    if price_df.empty:
        st.error("株価データが取得できませんでした。")
        st.stop()

    score, breakdown, buy_reasons, risk_reasons, _reasons, category_rows, horizon, summary = calculate_phase1_score(price_df, fund)
    judgment = judgment_from_score(score)
    stats = get_latest_price_stats(price_df)

    col1, col2, col3 = st.columns(3)
    col1.metric("総合判定", judgment)
    col2.metric("総合スコア", f"{score} / 100")
    col3.metric("直近終値", format_number(stats["latest_close"], 2))

    st.subheader("株価チャート（ローソク足 + 移動平均 + 出来高）")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
    fig.add_trace(go.Candlestick(x=price_df.index, open=price_df["Open"], high=price_df["High"], low=price_df["Low"], close=price_df["Close"], name="OHLC"), row=1, col=1)
    for ma_col, name in [("MA25", "MA25"), ("MA75", "MA75"), ("MA200", "MA200")]:
        fig.add_trace(go.Scatter(x=price_df.index, y=price_df[ma_col], mode="lines", name=name), row=1, col=1)
    fig.add_trace(go.Bar(x=price_df.index, y=price_df["Volume"], name="Volume"), row=2, col=1)
    fig.update_layout(height=700, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("テクニカル指標")
    c1, c2 = st.columns(2)
    with c1:
        st.line_chart(price_df[["RSI"]])
    with c2:
        st.line_chart(price_df[["MACD", "MACD_SIGNAL", "MACD_HIST"]])
    st.line_chart(price_df[["Close", "BB_HIGH", "BB_MID", "BB_LOW"]])

    st.subheader("ファンダメンタル（取得データ）")
    fundamental_rows = {
        "時価総額": format_number(fund.get("market_cap"), 0),
        "PER": format_number(fund.get("per"), 2),
        "PBR": format_number(fund.get("pbr"), 2),
        "PSR": format_number(fund.get("psr"), 2),
        "配当利回り": format_percent(fund.get("dividend_yield"), 2),
        "EPS": format_number(fund.get("eps"), 2),
        "売上高": format_number(fund.get("revenue"), 0),
        "純利益": format_number(fund.get("net_income"), 0),
        "営業キャッシュフロー": format_number(fund.get("operating_cf"), 0),
        "フリーキャッシュフロー": format_number(fund.get("free_cf"), 0),
        "直近高値": format_number(stats.get("recent_high"), 2),
        "直近安値": format_number(stats.get("recent_low"), 2),
    }
    st.dataframe(pd.DataFrame(fundamental_rows.items(), columns=["項目", "値"]), use_container_width=True)

    st.subheader("スコア内訳")
    st.dataframe(pd.DataFrame(category_rows), use_container_width=True)

    st.subheader("短期・中期・長期の補助判定")
    h1, h2, h3 = st.columns(3)
    h1.metric("短期判定", horizon["短期判定"])
    h2.metric("中期判定", horizon["中期判定"])
    h3.metric("長期判定", horizon["長期判定"])

    st.subheader("判定理由")
    st.markdown("**取得データ**")
    st.markdown(f"- バリュエーション: {valuation_comment(fund.get('per'), fund.get('pbr'), fund.get('psr'))}")
    st.markdown(f"- 財務サマリー: {build_fundamental_summary(fund)}")

    st.markdown("**計算データ（買い材料 / 売り材料）**")
    c_buy, c_sell = st.columns(2)
    with c_buy:
        st.markdown("### 買い材料")
        if buy_reasons:
            for r in buy_reasons:
                st.markdown(f"- {r}")
        else:
            st.markdown("- データ未取得")
    with c_sell:
        st.markdown("### 売り材料 / 注意材料")
        if risk_reasons:
            for r in risk_reasons:
                st.markdown(f"- {r}")
        else:
            st.markdown("- 特記事項なし")

    st.markdown("**AIによる解釈（ルールベース）**")
    st.write(f"総合判定は **{judgment}**。{summary}")

    st.subheader("リスク要因")
    if risk_reasons:
        for risk in risk_reasons:
            st.markdown(f"- {risk}")
    else:
        st.markdown("- 特記事項なし")

    st.subheader("データ未取得項目一覧")
    missing = [k for k, v in fundamental_rows.items() if v == "データ未取得"]
    if missing:
        for item in missing:
            st.markdown(f"- {item}: データ未取得")
    else:
        st.markdown("- なし")

    st.info("これは投資助言ではありません。最終判断は自己責任で行ってください。")
