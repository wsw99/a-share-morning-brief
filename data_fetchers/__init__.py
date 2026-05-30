from datetime import date
import json
import sys, os

# SSL patch must be first — 国内金融数据源 (上交所/新浪财经) 使用自签名证书
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ssl_patch import *  # noqa

from .index_fetcher import fetch_index_data
from .etf_flow_fetcher import fetch_etf_flow_data
from .margin_fetcher import fetch_margin_data
from .futures_fetcher import fetch_futures_data
from .news_fetcher import fetch_news_data


def _get_or_fetch(data_type: str, target_date: date, fetcher_fn):
    """带 SQLite 缓存的单类数据获取。"""
    from data.cache import get_cached, set_cache

    cached = get_cached(data_type, target_date)
    if cached is not None:
        return cached, True  # (data, from_cache)

    result = fetcher_fn(target_date)
    set_cache(data_type, target_date, result)
    return result, False


def fetch_all(target_date: date) -> dict:
    result = {"target_date": target_date.isoformat()}
    cache_flags = {}

    for data_type, fetcher_fn in [
        ("index", fetch_index_data),
        ("etf_flow", fetch_etf_flow_data),
        ("margin", fetch_margin_data),
        ("futures", fetch_futures_data),
        ("news", fetch_news_data),
    ]:
        data, from_cache = _get_or_fetch(data_type, target_date, fetcher_fn)
        result[data_type] = data
        cache_flags[data_type] = from_cache

    result["_cache_flags"] = cache_flags
    return result
