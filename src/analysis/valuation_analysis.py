"""Valuation analysis logic."""


def valuation_comment(per, pbr, psr) -> str:
    comments = []
    if per is not None:
        comments.append(f"PER={per:.2f}")
    if pbr is not None:
        comments.append(f"PBR={pbr:.2f}")
    if psr is not None:
        comments.append(f"PSR={psr:.2f}")
    return " / ".join(comments) if comments else "データ未取得"
