"""
融资融券余额采集
数据来源: 沪深交易所 (通过 AkShare)

注意: 沪市数据单位为元, 深市数据单位为亿元
"""
import akshare as ak
import pandas as pd
from datetime import date, timedelta


def fetch_margin_data(target_date: date) -> dict:
    try:
        dt_str = str(target_date)

        # 沪市融资融券 (支持日期范围, 单位: 元)
        df_sse = ak.stock_margin_sse(start_date="20240101", end_date=dt_str)
        df_sse = df_sse.rename(columns={"信用交易日期": "date_col"})
        df_sse["date_col"] = pd.to_datetime(df_sse["date_col"])

        # 深市融资融券 (仅支持单日, 单位: 亿元, 无日期列; 深交所接口偶发 SSL 错误)
        margin_szse = 0
        short_szse = 0
        try:
            df_szse = ak.stock_margin_szse(date=dt_str)
            if not df_szse.empty:
                szse_row = df_szse.iloc[0]
                margin_szse = float(szse_row["融资余额"]) * 1e8
                short_szse = float(szse_row["融券余额"]) * 1e8
        except Exception:
            pass  # 深市数据不可用时用沪市数据兜底

        sse_in_range = df_sse[df_sse["date_col"] <= pd.Timestamp(target_date)]
        if sse_in_range.empty:
            return {"data": {"error": "融资融券数据暂未更新"}, "source": "沪深交易所", "updated_at": dt_str}

        sse_row = sse_in_range.iloc[-1]
        margin_sse = float(sse_row["融资余额"])
        short_sse = float(sse_row["融券余量金额"])

        total_margin = margin_sse + margin_szse

        # 近一周趋势 (用沪市历史数据)
        one_week_ago = target_date - timedelta(days=10)
        recent_sse = sse_in_range[sse_in_range["date_col"] >= pd.Timestamp(one_week_ago)]

        recent_daily = [
            {"date": str(r["date_col"].date()), "total_margin": round(float(r["融资余额"]) + margin_szse, 2)}
            for _, r in recent_sse.iterrows()
        ]

        return {
            "data": {
                "margin_sse": round(margin_sse, 2),
                "margin_szse": round(margin_szse, 2),
                "total_margin": round(total_margin, 2),
                "short_sell_total": round(short_sse + short_szse, 2),
                "margin_buy_amount": round(float(sse_row.get("融资买入额", 0)), 2),
                "recent_daily": recent_daily,
            },
            "source": "沪深交易所",
            "updated_at": str(sse_row["date_col"].date()),
        }

    except Exception as e:
        return {"data": {"error": str(e)}, "source": "沪深交易所", "updated_at": str(target_date)}
