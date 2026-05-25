"""Phase 1 scoring logic."""

from src.utils.config import SCORING_THRESHOLDS


def _safe_gt(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) > float(b)
    except (TypeError, ValueError):
        return False


def _safe_lt(a, b) -> bool:
    if a is None or b is None:
        return False
    try:
        return float(a) < float(b)
    except (TypeError, ValueError):
        return False


def _safe_ratio(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return float(a) / float(b)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def calculate_phase1_score(df, fund: dict) -> tuple[int, dict, dict, list[str], list[str], dict, str]:
    score = 50
    buy_factors = []
    caution_factors = []

    breakdown = {
        "トレンド": {"score": 50, "comment": "移動平均との位置関係を評価"},
        "モメンタム": {"score": 50, "comment": "RSI・MACD・短期変動を評価"},
        "バリュエーション": {"score": 50, "comment": "PER/PBR/PSRの水準"},
        "ファンダメンタル": {"score": 50, "comment": "利益と成長性の基礎体力"},
        "キャッシュフロー": {"score": 50, "comment": "営業CF/FCFの健全性"},
        "リスク": {"score": 50, "comment": "過熱・急騰・反落リスク"},
    }

    horizons = {
        "短期": {"view": "データ未取得", "buy": [], "caution": []},
        "中期": {"view": "データ未取得", "buy": [], "caution": []},
        "長期": {"view": "データ未取得", "buy": [], "caution": []},
    }

    if not df.empty:
        last = df.iloc[-1]
        close = last.get("Close")
        ma25 = last.get("MA25")
        ma75 = last.get("MA75")
        ma200 = last.get("MA200")
        rsi = last.get("RSI")
        macd = last.get("MACD")
        macd_signal = last.get("MACD_SIGNAL")
        bb_high = last.get("BB_HIGH")
        vol_ratio = _safe_ratio(last.get("Volume"), last.get("VOL_MA20"))
        jump_20d = _safe_ratio(close, df["Close"].iloc[-21]) - 1 if len(df) > 21 else None

        if _safe_gt(close, ma25):
            score += 4; breakdown["トレンド"]["score"] += 8
            buy_factors.append("株価が25日線を上回る")
            horizons["中期"]["buy"].append("25日線より上で推移")
        else:
            caution_factors.append("25日線を下回り短中期の戻りは不安定")
            horizons["中期"]["caution"].append("25日線を下回る")

        if _safe_gt(close, ma75):
            score += 4; breakdown["トレンド"]["score"] += 8
            buy_factors.append("株価が75日線を上回る")
            horizons["中期"]["buy"].append("75日線より上でトレンド継続")
        else:
            caution_factors.append("75日線を下回り中期トレンドは弱含み")
            horizons["中期"]["caution"].append("75日線を下回る")

        if _safe_gt(close, ma200):
            score += 4; breakdown["トレンド"]["score"] += 8; breakdown["ファンダメンタル"]["score"] += 4
            buy_factors.append("株価が200日線を上回る")
            horizons["長期"]["buy"].append("200日線を上回り長期基調は堅調")
        else:
            score -= 4; breakdown["リスク"]["score"] -= 8
            caution_factors.append("200日線を下回り長期の下振れリスク")
            horizons["長期"]["caution"].append("200日線を下回る")

        if rsi is not None:
            if rsi >= 70:
                score -= 5; breakdown["モメンタム"]["score"] -= 10; breakdown["リスク"]["score"] -= 10
                caution_factors.append("RSIが高く短期的に過熱気味")
                horizons["短期"]["caution"].append("RSI高水準で過熱感")
            elif rsi <= 30:
                score += 3; breakdown["モメンタム"]["score"] += 6
                buy_factors.append("RSIが低水準で反発余地")
                horizons["短期"]["buy"].append("RSI低水準で自律反発余地")

        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 3; breakdown["モメンタム"]["score"] += 6
                buy_factors.append("MACDがシグナルを上回る")
            else:
                score -= 3; breakdown["モメンタム"]["score"] -= 6
                caution_factors.append("MACDがシグナルを下回り勢い鈍化")

        if bb_high is not None and _safe_gt(close, bb_high):
            score -= 3; breakdown["リスク"]["score"] -= 6
            caution_factors.append("ボリンジャーバンド上限超えで短期反落に注意")
            horizons["短期"]["caution"].append("BB上限付近で反落リスク")

        if jump_20d is not None:
            if jump_20d > 0.15:
                score -= 4; breakdown["リスク"]["score"] -= 8
                caution_factors.append("20営業日で急騰しており押し目待ちが妥当")
                horizons["短期"]["caution"].append("短期急騰で利確売りリスク")
            elif jump_20d < -0.1:
                horizons["短期"]["buy"].append("短期下落後で戻り余地")

        if vol_ratio is not None:
            if vol_ratio >= 1.5:
                horizons["短期"]["buy"].append("出来高増加で関心が高い")
            elif vol_ratio <= 0.7:
                horizons["短期"]["caution"].append("出来高低下で上昇持続に注意")

    per = fund.get("per")
    pbr = fund.get("pbr")
    if per is not None and per > 40:
        score -= 6; breakdown["バリュエーション"]["score"] -= 12
        caution_factors.append("PERが高く割高感")
        horizons["長期"]["caution"].append("PER高水準で評価先行")
    elif per is not None and per < 15:
        score += 4; breakdown["バリュエーション"]["score"] += 8
        buy_factors.append("PERが相対的に低め")

    if pbr is not None and pbr > 5:
        breakdown["バリュエーション"]["score"] -= 4
        caution_factors.append("PBRが高く期待先行の可能性")

    net_income = fund.get("net_income")
    if net_income is not None and net_income > 0:
        score += 4; breakdown["ファンダメンタル"]["score"] += 8
        buy_factors.append("純利益が黒字")
        horizons["長期"]["buy"].append("利益体質を維持")
    else:
        score -= 6; breakdown["ファンダメンタル"]["score"] -= 12
        caution_factors.append("純利益データ未取得または赤字")
        horizons["長期"]["caution"].append("収益力の確認が必要")

    operating_cf = fund.get("operating_cf")
    if operating_cf is not None and operating_cf > 0:
        score += 4; breakdown["キャッシュフロー"]["score"] += 8
        buy_factors.append("営業キャッシュフローがプラス")
    else:
        score -= 6; breakdown["キャッシュフロー"]["score"] -= 12
        caution_factors.append("営業CFデータ未取得またはマイナス")

    free_cf = fund.get("free_cf")
    if free_cf is not None and free_cf > 0:
        breakdown["キャッシュフロー"]["score"] += 5
        horizons["長期"]["buy"].append("フリーCFが確保されている")
    elif free_cf is not None and free_cf < 0:
        breakdown["キャッシュフロー"]["score"] -= 5
        horizons["長期"]["caution"].append("フリーCFがマイナス")

    score = max(0, min(100, score))
    for item in breakdown.values():
        item["score"] = max(0, min(100, item["score"]))

    for horizon in horizons.values():
        if horizon["buy"] and not horizon["caution"]:
            horizon["view"] = "やや強含み"
        elif horizon["caution"] and not horizon["buy"]:
            horizon["view"] = "注意シグナルあり"
        elif horizon["buy"] and horizon["caution"]:
            horizon["view"] = "強弱材料が混在"

    summary = (
        f"総合判定は{judgment_from_score(score)}ですが、短期は{horizons['短期']['view']}、"
        f"中期は{horizons['中期']['view']}、長期は{horizons['長期']['view']}です。"
        "分析補助情報として、過熱感やトレンド継続性を併せてご確認ください。"
    )

    return score, breakdown, horizons, buy_factors, caution_factors, {
        "valuation": "データ未取得" if per is None and pbr is None else "主要バリュエーションを反映",
        "fundamental": "データ未取得" if net_income is None and operating_cf is None else "収益性・CFを反映",
    }, summary


def judgment_from_score(score: int) -> str:
    if score >= SCORING_THRESHOLDS["buy"]:
        return "買い寄り"
    if score >= SCORING_THRESHOLDS["neutral"]:
        return "中立"
    return "売り寄り"
