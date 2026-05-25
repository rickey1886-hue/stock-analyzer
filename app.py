import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.analysis.fundamental_analysis import build_fundamental_summary
from src.analysis.scoring import calculate_market_environment_score, calculate_phase1_score, judgment_from_score
from src.analysis.technical_analysis import add_technical_indicators
from src.analysis.valuation_analysis import valuation_comment
from src.data.fundamental_data import get_fundamental_snapshot
from src.data.market_data import get_market_environment
from src.data.price_data import get_latest_price_stats, get_price_history
from src.utils.config import PERIOD_OPTIONS
from src.utils.formatting import format_number, format_percent, is_valid_number
from src.utils.ticker_utils import normalize_ticker

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("株式投資分析ツール（Phase 1 MVP）")
st.caption("これは投資助言ではありません。最終判断は自己責任で行ってください。")
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .summary-card {
        border: 1px solid #dbe2ea;
        border-radius: 12px;
        padding: 14px 16px;
        background: #f8fafc;
        margin-bottom: 0.5rem;
    }
    .summary-title {font-size: 0.85rem; color: #5b6675; margin-bottom: 0.25rem;}
    .summary-value {font-size: 1.25rem; font-weight: 700; color: #0f172a;}
    .section-card {
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        background: #ffffff;
        margin-bottom: 1rem;
    }
    .badge-strong {color: #047857; font-weight: 700;}
    .badge-neutral {color: #1d4ed8; font-weight: 700;}
    .badge-caution {color: #b45309; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

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

    score, breakdown, horizons, buy_factors, caution_factors, _, summary_comment = calculate_phase1_score(price_df, fund)
    judgment = judgment_from_score(score)
    stats = get_latest_price_stats(price_df)

    with st.spinner("市場環境を取得中..."):
        market_env = get_market_environment(PERIOD_OPTIONS[period_label])

    stock_return = None
    if len(price_df) >= 2:
        first_close = price_df["Close"].iloc[0]
        last_close = price_df["Close"].iloc[-1]
        if is_valid_number(first_close, allow_zero=False) and is_valid_number(last_close):
            stock_return = (float(last_close) / float(first_close)) - 1.0

    comparison_rows = []
    market_score, market_comment = calculate_market_environment_score(market_env["market_returns"])
    for idx_name, idx_return in market_env["market_returns"].items():
        diff = None
        if not is_valid_number(stock_return) or not is_valid_number(idx_return):
            relative = "データ未取得"
        else:
            diff = stock_return - idx_return
            if diff >= 0.02:
                relative = "上回る"
            elif diff <= -0.02:
                relative = "下回る"
            else:
                relative = "ほぼ同等"
        comparison_rows.append({
            "比較対象": idx_name,
            "個別株騰落率": stock_return,
            "指数騰落率": idx_return,
            "差分": diff,
            "相対強弱": relative,
        })

    if stock_return is not None:
        score += int((market_score - 50) * 0.2)
        score = max(0, min(100, score))
        breakdown["市場環境"] = {
            "score": market_score,
            "comment": f"補助情報（総合スコアへの反映は限定的）: {market_comment}",
        }

    def judgment_class(text: str) -> str:
        if text in ["強気", "やや強気"]:
            return "badge-strong"
        if text in ["弱気", "やや弱気"]:
            return "badge-caution"
        return "badge-neutral"

    st.subheader("分析サマリー")
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    short_horizon = horizons.get("短期", {})
    mid_horizon = horizons.get("中期", {})
    long_horizon = horizons.get("長期", {})

    short_view = short_horizon.get("view", "データ未取得")
    mid_view = mid_horizon.get("view", "データ未取得")
    long_view = long_horizon.get("view", "データ未取得")

    cards = [
        ("総合判定", f"<span class='{judgment_class(judgment)}'>{judgment}</span>"),
        ("総合スコア", f"{score} / 100"),
        ("直近終値", format_number(stats["latest_close"], 2)),
        ("短期判定", f"<span class='{judgment_class(short_view)}'>{short_view}</span>"),
        ("中期判定", f"<span class='{judgment_class(mid_view)}'>{mid_view}</span>"),
        ("長期判定", f"<span class='{judgment_class(long_view)}'>{long_view}</span>"),
    ]
    for col, (title, value) in zip([s1, s2, s3, s4, s5, s6], cards):
        col.markdown(
            f"<div class='summary-card'><div class='summary-title'>{title}</div><div class='summary-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )

    tab_summary, tab_chart, tab_technical, tab_fundamental, tab_market, tab_reason, tab_data = st.tabs(
        ["サマリー", "チャート", "テクニカル", "ファンダメンタル", "市場環境", "判定理由・リスク", "データ取得状況"]
    )

    with tab_chart:
        st.subheader("株価チャート（ローソク足 + 移動平均 + 出来高）")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=price_df.index, open=price_df["Open"], high=price_df["High"], low=price_df["Low"], close=price_df["Close"], name="OHLC"), row=1, col=1)
        for ma_col, name in [("MA25", "MA25"), ("MA75", "MA75"), ("MA200", "MA200")]:
            fig.add_trace(go.Scatter(x=price_df.index, y=price_df[ma_col], mode="lines", name=name), row=1, col=1)
        fig.add_trace(go.Bar(x=price_df.index, y=price_df["Volume"], name="Volume"), row=2, col=1)
        fig.update_layout(height=700, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    with tab_technical:
        st.subheader("テクニカル指標")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**RSI**")
            st.line_chart(price_df[["RSI"]])
        with c2:
            st.markdown("**MACD**")
            st.line_chart(price_df[["MACD", "MACD_SIGNAL", "MACD_HIST"]])
        st.markdown("**ボリンジャーバンド（終値比較）**")
        st.line_chart(price_df[["Close", "BB_HIGH", "BB_MID", "BB_LOW"]])

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
    with tab_fundamental:
        st.subheader("ファンダメンタル（取得データ）")
        st.dataframe(pd.DataFrame(fundamental_rows.items(), columns=["項目", "値"]), use_container_width=True)

    market_table = pd.DataFrame(market_env["market_rows"])
    market_table["終値"] = market_table["終値"].apply(lambda v: format_number(v, 2))
    market_table["期間騰落率"] = market_table["期間騰落率"].apply(lambda v: format_percent(v, 2))
    with tab_market:
        st.subheader("市場環境")
        st.markdown("### 1) 市場指数一覧")
        st.dataframe(market_table, use_container_width=True)

        st.markdown("### 2) 個別株 vs 市場指数比較")
        comparison_df = pd.DataFrame(comparison_rows)
        comparison_df["個別株騰落率"] = comparison_df["個別株騰落率"].apply(lambda v: format_percent(v, 2))
        comparison_df["指数騰落率"] = comparison_df["指数騰落率"].apply(lambda v: format_percent(v, 2))
        comparison_df["差分"] = comparison_df["差分"].apply(lambda v: format_percent(v, 2))
        st.dataframe(comparison_df, use_container_width=True)

        st.markdown("### 3) 市場環境コメント")
        if stock_return is None:
            st.write("個別株騰落率が算出できないため比較コメントはデータ未取得")
        else:
            outperform_count = sum(1 for row in comparison_rows if row["相対強弱"] == "上回る")
            valid_count = sum(1 for row in comparison_rows if row["相対強弱"] in ["上回る", "下回る", "ほぼ同等"])
            underperform_count = sum(1 for row in comparison_rows if row["相対強弱"] == "下回る")
            if valid_count == 0:
                st.write("市場指数比較データ未取得")
            elif outperform_count > valid_count / 2:
                st.write(f"{ticker}は主要指数比で相対的に強い。{market_comment}。")
            elif underperform_count > valid_count / 2:
                st.write(f"{ticker}は指数比では見劣り。{market_comment}。")
            else:
                st.write(f"{ticker}は主要指数比でほぼ同等。{market_comment}。")

    with tab_summary:
        st.subheader("総合判定サマリー")
        st.markdown(f"- **総合判定**: {judgment}")
        st.markdown(f"- **総合スコア**: {score} / 100")
        st.markdown(f"- **AI解釈（ルールベース）**: {summary_comment}")
        st.subheader("スコア内訳")
        breakdown_rows = [{"カテゴリ": k, "スコア(100点満点)": v["score"], "コメント": v["comment"]} for k, v in breakdown.items()]
        st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True)

        st.subheader("短期・中期・長期の分析補助")
        horizon_rows = []
        for term, data in horizons.items():
            buy_items = data.get("buy", [])
            caution_items = data.get("caution", [])
            view = data.get("view", "データ未取得")
            buy_text = "、".join(buy_items) if buy_items else "データ未取得"
            caution_text = "、".join(caution_items) if caution_items else "データ未取得"
            horizon_rows.append({"期間": term, "判定": view, "買い材料": buy_text, "売り材料 / 注意材料": caution_text})
        st.dataframe(pd.DataFrame(horizon_rows), use_container_width=True)

    with tab_reason:
        st.subheader("判定理由・リスク")
        st.markdown("**取得データの要約**")
        st.markdown(f"- バリュエーション: {valuation_comment(fund.get('per'), fund.get('pbr'), fund.get('psr'))}")
        st.markdown(f"- 財務サマリー: {build_fundamental_summary(fund)}")

        left_col, right_col = st.columns(2)
        with left_col:
            st.markdown("#### 買い材料")
            if buy_factors:
                for item in buy_factors:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- データ未取得")
        with right_col:
            st.markdown("#### 売り材料 / 注意材料")
            if caution_factors:
                for item in caution_factors:
                    st.markdown(f"- {item}")
            else:
                st.markdown("- データ未取得")

        st.markdown("#### リスク要因")
        if caution_factors:
            for risk in caution_factors:
                st.markdown(f"- {risk}")
        else:
            st.markdown("- 特記事項なし")

    with tab_data:
        st.subheader("データ取得状況")
        st.markdown("**データ未取得項目一覧**")
        missing = [k for k, v in fundamental_rows.items() if v == "データ未取得"]
        if missing:
            for item in missing:
                st.markdown(f"- {item}: データ未取得")
        else:
            st.markdown("- なし")
        st.markdown("**取得済み項目一覧（ファンダメンタル）**")
        st.dataframe(pd.DataFrame(fundamental_rows.items(), columns=["項目", "値"]), use_container_width=True)

    st.info("免責：これは投資助言ではありません。最終判断は自己責任で行ってください。")
