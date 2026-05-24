"""Fundamental interpretation helpers."""


def build_fundamental_summary(fund: dict) -> str:
    positives = []
    risks = []
    if fund.get("net_income") is not None and fund["net_income"] > 0:
        positives.append("純利益が黒字")
    else:
        risks.append("純利益データ未取得または赤字")

    if fund.get("operating_cf") is not None and fund["operating_cf"] > 0:
        positives.append("営業CFがプラス")
    else:
        risks.append("営業CFデータ未取得またはマイナス")

    return f"強み: {', '.join(positives) if positives else 'データ未取得'} / 注意: {', '.join(risks) if risks else '特になし'}"
