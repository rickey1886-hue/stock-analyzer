"""Phase 1 scoring logic."""

from src.utils.config import SCORING_THRESHOLDS


def calculate_phase1_score(df, fund: dict) -> tuple[int, dict, list[str], list[str]]:
    score = 50
    reasons = []
    risks = []
    breakdown = {"株価トレンド": 50, "テクニカル": 50, "バリュエーション": 50, "業績・CF": 50}

    if not df.empty:
        last = df.iloc[-1]
        if last.get("Close") > last.get("MA25", float("inf")):
            score += 5; breakdown["株価トレンド"] += 10; reasons.append("株価が25日移動平均線を上回る")
        if last.get("Close") > last.get("MA75", float("inf")):
            score += 5; breakdown["株価トレンド"] += 10; reasons.append("株価が75日移動平均線を上回る")
        if last.get("RSI") is not None:
            if last["RSI"] >= 70:
                score -= 5; breakdown["テクニカル"] -= 10; risks.append("RSI高水準で過熱感")
            elif last["RSI"] <= 30:
                score += 3; breakdown["テクニカル"] += 6; reasons.append("RSI低水準で反発余地")
        if last.get("MACD") is not None and last.get("MACD_SIGNAL") is not None:
            if last["MACD"] > last["MACD_SIGNAL"]:
                score += 4; breakdown["テクニカル"] += 8; reasons.append("MACDがシグナルを上回る")
            else:
                score -= 4; breakdown["テクニカル"] -= 8; risks.append("MACDがシグナルを下回る")

    per = fund.get("per")
    if per is not None and per > 40:
        score -= 7; breakdown["バリュエーション"] -= 14; risks.append("PERが高く割高感")
    elif per is not None and per < 15:
        score += 5; breakdown["バリュエーション"] += 10; reasons.append("PERが相対的に低い")

    if fund.get("net_income") is not None and fund["net_income"] > 0:
        score += 5; breakdown["業績・CF"] += 10; reasons.append("純利益が黒字")
    else:
        score -= 8; breakdown["業績・CF"] -= 16; risks.append("純利益データ未取得または赤字")

    if fund.get("operating_cf") is not None and fund["operating_cf"] > 0:
        score += 5; breakdown["業績・CF"] += 10; reasons.append("営業CFがプラス")
    else:
        score -= 8; breakdown["業績・CF"] -= 16; risks.append("営業CFデータ未取得またはマイナス")

    score = max(0, min(100, score))
    for k, v in breakdown.items():
        breakdown[k] = max(0, min(100, v))
    return score, breakdown, reasons, risks


def judgment_from_score(score: int) -> str:
    if score >= SCORING_THRESHOLDS["buy"]:
        return "買い寄り"
    if score >= SCORING_THRESHOLDS["neutral"]:
        return "中立"
    return "売り寄り"
