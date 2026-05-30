"""
融资融券分析: 近一周变化率、趋势方向
"""
import numpy as np


def run_margin_analysis(margin_data: dict) -> dict:
    data = margin_data.get("data", {})

    recent_daily = data.get("recent_daily", [])
    if not recent_daily or len(recent_daily) < 2:
        return {"error": "融资融券数据不足"}

    margins = [d["total_margin"] for d in recent_daily]
    latest = margins[-1]
    one_week_ago = margins[0]

    change = latest - one_week_ago
    change_pct = round(change / one_week_ago * 100, 2) if one_week_ago > 0 else 0

    # 连续变化天数
    trend_days = 0
    trend_direction = "持平"
    for i in range(len(margins) - 1, 0, -1):
        if margins[i] > margins[i - 1]:
            if trend_direction == "持平":
                trend_direction = "增加"
                trend_days = 1
            elif trend_direction == "增加":
                trend_days += 1
            else:
                break
        elif margins[i] < margins[i - 1]:
            if trend_direction == "持平":
                trend_direction = "减少"
                trend_days = 1
            elif trend_direction == "减少":
                trend_days += 1
            else:
                break
        else:
            break

    return {
        "latest_total_margin": round(latest, 2),
        "one_week_change": round(change, 2),
        "one_week_change_pct": change_pct,
        "trend_direction": trend_direction,
        "trend_days": trend_days,
        "signal": (
            "人气回暖"
            if change_pct > 2 and trend_direction == "增加"
            else "人气降温" if change_pct < -2 and trend_direction == "减少"
            else "杠杆资金观望" if abs(change_pct) < 1
            else "正常波动"
        ),
        "total_short_sell": data.get("short_sell_total", 0),
    }
