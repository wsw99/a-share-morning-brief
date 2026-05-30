"""
股指期货数据采集
数据来源: 新浪财经 (通过 AkShare futures_main_sina)
"""
import akshare as ak
import pandas as pd
from datetime import date, timedelta


FUTURES_CONTRACTS = {
    "IF": {"code": "IF0", "name": "沪深300股指期货", "index": "沪深300"},
    "IC": {"code": "IC0", "name": "中证500股指期货", "index": "中证500"},
    "IH": {"code": "IH0", "name": "上证50股指期货", "index": "上证50"},
    "IM": {"code": "IM0", "name": "中证1000股指期货", "index": "中证1000"},
}


def fetch_futures_data(target_date: date) -> dict:
    dt_str = str(target_date)
    results = {}

    for symbol, info in FUTURES_CONTRACTS.items():
        try:
            df = ak.futures_main_sina(symbol=info["code"], start_date="20240101", end_date=dt_str)
            if df.empty:
                results[symbol] = {"error": f"{info['name']} 无数据", "name": info["name"], "index": info["index"]}
                continue

            df["date_col"] = pd.to_datetime(df["日期"])
            df_target = df[df["date_col"] <= pd.Timestamp(target_date)]

            if df_target.empty:
                results[symbol] = {"error": f"{info['name']} 目标日期无数据", "name": info["name"], "index": info["index"]}
                continue

            latest = df_target.iloc[-1]
            prev = df_target.iloc[-2] if len(df_target) >= 2 else None

            close = float(latest["收盘价"])
            volume = float(latest["成交量"])
            change_pct = (
                round((close - float(prev["收盘价"])) / float(prev["收盘价"]) * 100, 2)
                if prev is not None
                else None
            )

            results[symbol] = {
                "name": info["name"],
                "contract": info["code"],
                "price": close,
                "change_pct": change_pct,
                "volume": volume,
                "spot_index": info["index"],
                "date": str(latest["date_col"].date()),
            }

        except Exception as e:
            results[symbol] = {"error": str(e), "name": info["name"], "index": info["index"]}

    return {
        "data": results,
        "source": "中国金融期货交易所 (新浪财经)",
        "updated_at": dt_str,
    }
