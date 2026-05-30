"""
消息面采集 (占位, Step 2 实现)
"""
from datetime import date


def fetch_news_data(target_date: date) -> dict:
    return {
        "data": {"summary": "消息面采集功能将在 Step 2 中实现"},
        "source": "财联社 / 新浪财经 (待接入)",
        "updated_at": str(target_date),
    }
