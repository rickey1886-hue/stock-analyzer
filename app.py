import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis.fundamental_analysis import build_fundamental_summary
from src.analysis.scoring import calculate_phase1_score, judgment_from_score
from src.analysis.technical_analysis import add_technical_indicators
from src.analysis.valuation_analysis import valuation_comment
from src.data.fundamental_data import get_fundamental_snapshot
from src.data.market_data import compare_with_market, get_market_indices
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

        try:
            market_rows, market_missing = get_market_indices(PERIOD_OPTIONS[period_label])
        except Exception:
            market_rows, market_missing = {}, []

    if price_df.empty:
        st.error("株価データが取得できませんでした。")
        st.stop()

    score, breakdown, horizons, buy_factors, caution_factors, _, summary_comment = calculate_phase1_score(price_df, fund)
    judgment = judgment_from_score(score)
    stats = get_latest_price_stats(price_df)
    market_comparison_rows, market_comment, market_meta = compare_with_market(ticker, price_df, market_rows)

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
    breakdown_rows = [{"カテゴリ": k, "スコア(100点満点)": v["score"], "コメント": v["comment"]} for k, v in breakdown.items()]
    market_score_display = market_meta.get("score") if isinstance(market_meta.get("score"), int) else "データ未取得"
    breakdown_rows.append({"カテゴリ": "市場環境スコア", "スコア(100点満点)": market_score_display, "コメント": market_meta.get("comment", "データ未取得")})
    st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True)

    st.subheader("市場環境（Phase 2-1 / Phase 2-2）")
    market_table_rows = []
    for name, row in market_rows.items():
        market_table_rows.append({
            "指数": name,
            "ティッカー": row.get("ticker"),
            "終値": format_number(row.get("latest"), 2),
            "期間騰落率": format_percent(row.get("change_pct"), 2),
            "取得状況": row.get("status", "データ未取得"),
        })
    st.markdown("**市場指数一覧テーブル**")
    st.dataframe(pd.DataFrame(market_table_rows), use_container_width=True)

    comp_rows = []
    for r in market_comparison_rows:
        comp_rows.append({
            "比較対象": r["比較対象"],
            "個別株騰落率": format_percent(r["個別株騰落率"], 2),
            "指数騰落率": format_percent(r["指数騰落率"], 2),
            "比較": r["比較"],
            "コメント": r["コメント"],
        })
    st.markdown("**個別株 vs 市場指数の騰落率比較**")
    st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)

    st.markdown("**市場環境コメント**")
    st.write(market_comment)

    st.markdown("**データ取得状況**")
    st.markdown(f"- 対象市場: {market_meta.get('対象市場', 'データ未取得')}")
    st.markdown(f"- 比較対象: {market_meta.get('比較対象', 'データ未取得')}")
    if market_missing:
        st.markdown(f"- 未取得指数: {'、'.join(market_missing)}")
    else:
        st.markdown("- 未取得指数: なし")

    st.subheader("短期・中期・長期の分析補助")
    horizon_rows = []
    for term, data in horizons.items():
        buy_text = "、".join(data["buy"]) if data["buy"] else "データ未取得"
        caution_text = "、".join(data["caution"]) if data["caution"] else "データ未取得"
        horizon_rows.append({"期間": term, "判定": data["view"], "買い材料": buy_text, "売り材料 / 注意材料": caution_text})
    st.dataframe(pd.DataFrame(horizon_rows), use_container_width=True)

    st.subheader("判定理由")
    st.markdown("**取得データ**")
    st.markdown(f"- バリュエーション: {valuation_comment(fund.get('per'), fund.get('pbr'), fund.get('psr'))}")
    st.markdown(f"- 財務サマリー: {build_fundamental_summary(fund)}")

    st.markdown("**買い材料**")
    if buy_factors:
        for item in buy_factors:
            st.markdown(f"- {item}")
    else:
        st.markdown("- データ未取得")

    st.markdown("**売り材料 / 注意材料**")
    if caution_factors:
        for item in caution_factors:
            st.markdown(f"- {item}")
    else:
        st.markdown("- データ未取得")

    st.markdown("**AIによる解釈（ルールベース）**")
    st.write(summary_comment)

    st.subheader("リスク要因")
    if caution_factors:
        for risk in caution_factors:
            st.markdown(f"- {risk}")
    else:
        st.markdown("- 特記事項なし")

    st.subheader("データ未取得項目一覧")
    missing = [k for k, v in fundamental_rows.items() if v == "データ未取得"]
    if market_missing:
        missing.extend([f"市場指数: {name}" for name in market_missing])
    if missing:
        for item in missing:
            st.markdown(f"- {item}: データ未取得")
    else:
        st.markdown("- なし")

    st.info("これは投資助言ではありません。最終判断は自己責任で行ってください。")
