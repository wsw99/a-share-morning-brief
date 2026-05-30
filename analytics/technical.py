"""
技术形态分析: 均线突破、成交量放大、横盘整理
纯 Python 计算, 不调用 LLM
"""
import numpy as np


def analyze_ma_breakout(closes: list) -> dict:
    """检测价格 vs MA10/MA20 的关系"""
    if len(closes) < 21:
        return {"error": "数据不足, 至少需要 21 个交易日"}

    closes_arr = np.array(closes)
    ma10 = np.mean(closes_arr[-10:])
    ma20 = np.mean(closes_arr[-20:])
    latest = closes_arr[-1]
    prev = closes_arr[-2]

    prev_ma10 = np.mean(closes_arr[-11:-1])
    prev_ma20 = np.mean(closes_arr[-21:-1])

    def status(now_price, now_ma, prev_price, prev_ma):
        if now_price > now_ma and prev_price < prev_ma:
            return "向上突破"
        elif now_price < now_ma and prev_price > prev_ma:
            return "向下跌破"
        return "线上" if now_price > now_ma else "线下"

    return {
        "MA10": {
            "value": round(ma10, 2),
            "status": status(latest, ma10, prev, prev_ma10),
        },
        "MA20": {
            "value": round(ma20, 2),
            "status": status(latest, ma20, prev, prev_ma20),
        },
        "latest_close": latest,
    }


def analyze_volume(volumes: list) -> dict:
    """检测成交量是否放大 (对比 20 日均量)"""
    if len(volumes) < 21:
        return {"error": "数据不足"}

    vols = np.array(volumes)
    ma20 = np.mean(vols[-21:-1])  # 不含当日的 20 日均量
    latest = vols[-1]

    ratio = round(latest / ma20, 2) if ma20 > 0 else 1.0

    if ratio > 1.5:
        signal = "显著放量"
    elif ratio > 1.2:
        signal = "温和放量"
    elif ratio < 0.5:
        signal = "显著缩量"
    else:
        signal = "正常"

    return {"signal": signal, "ratio": ratio, "latest_volume": float(latest), "ma20_volume": round(float(ma20), 2)}


def analyze_consolidation(closes: list) -> dict:
    """检测近 5 日是否横盘整理 (振幅 < 2%)"""
    if len(closes) < 5:
        return {"is_consolidating": False}

    recent = np.array(closes[-5:])
    amplitude = round((np.max(recent) - np.min(recent)) / np.mean(recent) * 100, 2)
    return {
        "is_consolidating": amplitude < 2.0,
        "amplitude_5d_pct": amplitude,
    }


def run_technical_analysis(index_data: dict) -> dict:
    """对各主要指数逐一分析"""
    results = {}
    for name, info in index_data.get("data", {}).items():
        if "error" in info:
            results[name] = info
            continue
        recent = info.get("recent_30", [])
        closes = [d["close"] for d in recent]
        volumes = [d["volume"] for d in recent]

        results[name] = {
            "ma": analyze_ma_breakout(closes) if len(closes) >= 21 else {"error": "数据不足"},
            "volume": analyze_volume(volumes) if len(volumes) >= 21 else {"error": "数据不足"},
            "consolidation": analyze_consolidation(closes),
        }
    return results
