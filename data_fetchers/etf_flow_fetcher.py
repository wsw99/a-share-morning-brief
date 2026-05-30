"""
ETF 资金流向采集
数据来源: 东方财富 (通过 AkShare)
"""
import akshare as ak
import pandas as pd
from datetime import date


def fetch_etf_flow_data(target_date: date) -> dict:
    try:
        df = ak.fund_etf_spot_em()

        # 关键列: 基金名称, 最新价, 涨跌幅, 成交额, 换手率
        # 按成交额降序, 取前 30 只
        df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
        df_top = df.nlargest(30, "成交额")

        etf_list = []
        for _, row in df_top.iterrows():
            etf_list.append({
                "name": str(row["名称"]),
                "code": str(row["代码"]),
                "price": float(row["最新价"]) if pd.notna(row["最新价"]) else None,
                "change_pct": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else None,
                "volume": float(row["成交额"]) if pd.notna(row["成交额"]) else None,
            })

        return {
            "data": {"top_etfs": etf_list},
            "source": "东方财富 ETF 风向标",
            "updated_at": str(target_date),
        }

    except Exception as e:
        return {"data": {"error": str(e)}, "source": "东方财富 ETF 风向标", "updated_at": ""}
