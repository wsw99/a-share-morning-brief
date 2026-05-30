"""
主要指数行情采集
数据来源: 东方财富 (通过 AkShare)
"""
import akshare as ak
import pandas as pd
from datetime import date, timedelta


INDEX_SYMBOLS = {
    # 主要大盘指数
    "sh000001": "上证综指",
    "sz399001": "深证成指",
    "sz399006": "创业板指",
    "sh000688": "科创50",
    # 期货对标现货指数 (升贴水计算用)
    "sh000300": "沪深300",
    "sh000905": "中证500",
    "sh000016": "上证50",
    "sh000852": "中证1000",
}


def fetch_index_data(target_date: date) -> dict:
    results = {}
    source = ""
    updated_at = ""

    for symbol, name in INDEX_SYMBOLS.items():
        try:
            df = ak.stock_zh_index_daily(symbol=symbol)
            df["date"] = pd.to_datetime(df["date"])

            # 目标日期数据: 如果 target_date 是今天(盘中), 最新一行可能还没收盘
            # 取 <= target_date 的最新数据行
            target_data = df[df["date"] <= pd.Timestamp(target_date)]
            if target_data.empty:
                results[name] = {"error": f"{name} 无数据"}
                continue

            latest = target_data.iloc[-1]
            prev = target_data.iloc[-2] if len(target_data) >= 2 else None

            close = float(latest["close"])
            volume = float(latest["volume"])
            change_pct = (
                round((close - float(prev["close"])) / float(prev["close"]) * 100, 2)
                if prev is not None
                else None
            )

            # 近 30 天数据 (给 analytics 算均线用)
            recent_30 = target_data.tail(30)

            results[name] = {
                "close": close,
                "volume": volume,
                "change_pct": change_pct,
                "open": float(latest["open"]),
                "high": float(latest["high"]),
                "low": float(latest["low"]),
                "date": str(latest["date"].date()),
                "recent_30": [
                    {
                        "date": str(r["date"].date()),
                        "close": float(r["close"]),
                        "volume": float(r["volume"]),
                    }
                    for _, r in recent_30.iterrows()
                ],
            }
            source = "东方财富"
            updated_at = str(latest["date"].date())

        except Exception as e:
            results[name] = {"error": str(e)}

    return {
        "data": results,
        "source": source,
        "updated_at": updated_at,
    }
