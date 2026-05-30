"""
ETF 资金流向分析: 板块排名
"""
import pandas as pd


def run_etf_analysis(etf_data: dict) -> dict:
    data = etf_data.get("data", {})
    top_etfs = data.get("top_etfs", [])

    if not top_etfs:
        return {"error": "ETF 数据为空"}

    # 按成交额排序
    df = pd.DataFrame(top_etfs)

    # 净流入排名 (涨跌幅 > 0 的, 按成交额加权)
    inflow = sorted(
        [e for e in top_etfs if e.get("change_pct", 0) is not None and e["change_pct"] > 0],
        key=lambda x: x.get("volume", 0),
        reverse=True,
    )[:5]
    outflow = sorted(
        [e for e in top_etfs if e.get("change_pct", 0) is not None and e["change_pct"] < 0],
        key=lambda x: x.get("volume", 0),
        reverse=True,
    )[:5]

    # 宽基 vs 行业 ETF 分布
    total_volume = sum(e.get("volume", 0) or 0 for e in top_etfs)

    return {
        "top_by_volume": top_etfs[:5],
        "inflow_top5": inflow,
        "outflow_top5": outflow,
        "total_volume_top30": round(total_volume, 2),
        "avg_change_pct": round(
            sum(e.get("change_pct", 0) or 0 for e in top_etfs) / len(top_etfs), 2
        ) if top_etfs else 0,
    }
