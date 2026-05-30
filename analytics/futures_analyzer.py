"""
股指期货升贴水分析
升贴水率 = (期货价 - 现货价) / 现货价 × 100%
负值 = 贴水 (期价低于现价, 市场偏空)
正值 = 升水 (期价高于现价, 市场偏多)
"""


# 期货 → 对应指数代码 (AkShare 命名)
FUTURES_INDEX_MAP = {
    "IF": "沪深300",
    "IC": "中证500",
    "IH": "上证50",
    "IM": "中证1000",
}


def run_futures_analysis(futures_data: dict, index_data: dict) -> dict:
    futures = futures_data.get("data", {})
    indices = index_data.get("data", {})

    results = {}
    for symbol, info in futures.items():
        if "error" in info:
            results[symbol] = info
            continue

        spot_name = FUTURES_INDEX_MAP.get(symbol, "")
        spot_info = indices.get(spot_name, {})

        if "error" in spot_info or not spot_info:
            results[symbol] = {**info, "basis": "现货数据缺失"}
            continue

        future_price = info.get("price")
        spot_price = spot_info.get("close")

        if future_price is None or spot_price is None:
            continue

        basis_rate = round((future_price - spot_price) / spot_price * 100, 2)
        basis_type = "升水" if basis_rate > 0 else "贴水" if basis_rate < 0 else "平水"

        results[symbol] = {
            **info,
            "spot_price": spot_price,
            "basis_rate": basis_rate,
            "basis_type": basis_type,
            "signal": (
                "市场情绪偏多" if basis_rate > 0.3
                else "市场情绪偏空" if basis_rate < -0.5
                else "中性"
            ),
        }

    return results
