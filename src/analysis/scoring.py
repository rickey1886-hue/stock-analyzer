"""Phase 1 scoring logic with horizon-based helper judgments."""

from __future__ import annotations

from src.utils.config import SCORING_THRESHOLDS


def _clamp(v: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, v))


def _safe_pct(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return (a / b) - 1
    except Exception:
        return None


def calculate_phase1_score(df, fund: dict) -> tuple[int, dict, list[str], list[str], list[str], list[dict], dict, str]:
    """Return score package for UI.

    Returns:
    - total score
    - legacy breakdown dict
    - buy reasons
    - risk reasons
    - combined reason lines (compat)
    - category table rows
    - horizon judgments
    - natural language summary
    """
    score = 50
    buy_reasons: list[str] = []
    risk_reasons: list[str] = []

    trend = 50
    momentum = 50
    valuation = 50
    fundamental = 50
    cashflow = 50
    risk = 0

    short_score = 50
    mid_score = 50
    long_score = 50

    if not df.empty:
        last = df.iloc[-1]
        close = last.get("Close")
        ma25 = last.get("MA25")
        ma75 = last.get("MA75")
        ma200 = last.get("MA200")
        rsi = last.get("RSI")

        if close is not None and ma25 is not None and close > ma25:
            score += 5; trend += 10; mid_score += 8
            buy_reasons.append("株価が25日移動平均線を上回る")
        if close is not None and ma75 is not None and close > ma75:
            score += 5; trend += 10; mid_score += 8
            buy_reasons.append("株価が75日移動平均線を上回る")
        if close is not None and ma200 is not None and close > ma200:
            trend += 8; long_score += 12
            buy_reasons.append("株価が200日移動平均線を上回る")

        if ma25 is not None and ma75 is not None and ma25 > ma75:
            trend += 6; mid_score += 8
            buy_reasons.append("短期線(25日)が中期線(75日)を上回る")

        if rsi is not None:
            if rsi >= 70:
                score -= 5; momentum -= 12; short_score -= 18; risk -= 8
                risk_reasons.append("RSI高水準で短期過熱感")
            elif rsi <= 30:
                score += 3; momentum += 8; short_score += 8
                buy_reasons.append("RSI低水準で反発余地")

        if last.get("MACD") is not None and last.get("MACD_SIGNAL") is not None:
            if last["MACD"] > last["MACD_SIGNAL"]:
                score += 4; momentum += 8; short_score += 6
                buy_reasons.append("MACDがシグナルを上回る")
            else:
                score -= 4; momentum -= 8; short_score -= 6; risk -= 3
                risk_reasons.append("MACDがシグナルを下回る")

        if close is not None and last.get("BB_HIGH") is not None and close >= last.get("BB_HIGH"):
            momentum -= 6; short_score -= 10; risk -= 6
            risk_reasons.append("ボリンジャーバンド+2σ近辺で過熱気味")

        if len(df) >= 21:
            month_ago = df["Close"].iloc[-21]
            mom_1m = _safe_pct(close, month_ago)
            if mom_1m is not None and mom_1m > 0.2:
                short_score -= 8; risk -= 6
                risk_reasons.append("1ヶ月で急騰しており反落リスク")
            elif mom_1m is not None and mom_1m < -0.15:
                short_score += 4

        if len(df) >= 21:
            vol20 = df["Volume"].tail(20).mean()
            if vol20 and vol20 > 0 and last.get("Volume") is not None:
                vol_ratio = last["Volume"] / vol20
                if vol_ratio > 1.8 and last.get("Close") < df["Close"].iloc[-2]:
                    short_score -= 8; risk -= 8
                    risk_reasons.append("出来高急増を伴う下落で需給悪化懸念")
                elif vol_ratio > 1.3 and last.get("Close") > df["Close"].iloc[-2]:
                    short_score += 4; momentum += 4
                    buy_reasons.append("出来高を伴う上昇でモメンタム改善")

    per = fund.get("per")
    if per is not None and per > 40:
        score -= 7; valuation -= 14; risk -= 4
        risk_reasons.append("PERが高く割高感")
    elif per is not None and per < 15:
        score += 5; valuation += 10
        buy_reasons.append("PERが相対的に低い")

    if fund.get("net_income") is not None and fund["net_income"] > 0:
        score += 5; fundamental += 12; long_score += 8
        buy_reasons.append("純利益が黒字")
    else:
        score -= 8; fundamental -= 16; long_score -= 8; risk -= 6
        risk_reasons.append("純利益データ未取得または赤字")

    if fund.get("operating_cf") is not None and fund["operating_cf"] > 0:
        score += 5; cashflow += 15; long_score += 8
        buy_reasons.append("営業CFがプラス")
    else:
        score -= 8; cashflow -= 18; long_score -= 10; risk -= 8
        risk_reasons.append("営業CFデータ未取得またはマイナス")

    if fund.get("free_cf") is not None and fund["free_cf"] > 0:
        cashflow += 8; long_score += 6
        buy_reasons.append("フリーCFがプラス")
    elif fund.get("free_cf") is not None and fund["free_cf"] < 0:
        cashflow -= 8; long_score -= 6; risk -= 4
        risk_reasons.append("フリーCFがマイナス")

    score = int(_clamp(score))
    trend = int(_clamp(trend)); momentum = int(_clamp(momentum)); valuation = int(_clamp(valuation))
    fundamental = int(_clamp(fundamental)); cashflow = int(_clamp(cashflow)); risk = int(max(-40, min(0, risk)))
    short_score = int(_clamp(short_score)); mid_score = int(_clamp(mid_score)); long_score = int(_clamp(long_score))

    breakdown = {"株価トレンド": trend, "テクニカル": momentum, "バリュエーション": valuation, "業績・CF": int((fundamental + cashflow) / 2)}

    category_rows = [
        {"カテゴリ": "トレンド", "スコア": f"{trend} / 100", "コメント": "移動平均線とトレンド継続性を評価"},
        {"カテゴリ": "モメンタム", "スコア": f"{momentum} / 100", "コメント": "RSI/MACD/ボリンジャー/出来高を評価"},
        {"カテゴリ": "バリュエーション", "スコア": f"{valuation} / 100", "コメント": "PER中心に割高・割安感を評価"},
        {"カテゴリ": "ファンダメンタル", "スコア": f"{fundamental} / 100", "コメント": "EPS・純利益など基礎業績を評価"},
        {"カテゴリ": "キャッシュフロー", "スコア": f"{cashflow} / 100", "コメント": "営業CF/フリーCFの健全性を評価"},
        {"カテゴリ": "リスク", "スコア": f"{risk}", "コメント": "過熱・急騰・需給悪化等の減点要因"},
    ]

    horizon = {
        "短期判定": "利確寄り / 新規買いは押し目待ち" if short_score < 45 else ("中立" if short_score < 65 else "買い寄り"),
        "中期判定": "売り寄り" if mid_score < 45 else ("中立〜買い寄り" if mid_score < 70 else "買い寄り"),
        "長期判定": "売り寄り" if long_score < 45 else ("中立 / 押し目買い候補" if long_score < 70 else "買い寄り"),
    }

    summary = (
        "上昇トレンドは維持されていますが、短期的にはRSIや騰落率から過熱感が出る場合があります。"
        "新規買いは押し目待ち、保有者は一部利確を検討するなど、補助的な判定として活用してください。"
    )

    combined = buy_reasons + risk_reasons
    return score, breakdown, buy_reasons, risk_reasons, combined, category_rows, horizon, summary


def judgment_from_score(score: int) -> str:
    if score >= SCORING_THRESHOLDS["buy"]:
        return "買い寄り"
    if score >= SCORING_THRESHOLDS["neutral"]:
        return "中立"
    return "売り寄り"
