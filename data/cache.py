"""
SQLite 数据缓存层
- 历史日期: 永久缓存（收盘数据不会变）
- 当日数据: TTL 后可刷新（盘中可能更新）
"""
import json
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "market_cache.db"
TTL_MINUTES = 10  # 当日数据缓存有效期


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS market_cache (
            data_type TEXT NOT NULL,
            target_date TEXT NOT NULL,
            data_json TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            PRIMARY KEY (data_type, target_date)
        )"""
    )
    return conn


def get_cached(data_type: str, target_date: date) -> dict | None:
    """查询缓存。历史日期直接返回，当日数据检查 TTL。"""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT data_json, fetched_at FROM market_cache WHERE data_type = ? AND target_date = ?",
            (data_type, str(target_date)),
        ).fetchone()

        if row is None:
            return None

        data_json, fetched_at = row
        fetched_dt = datetime.fromisoformat(fetched_at)
        today = date.today()

        # 历史日期: 永久有效
        if target_date < today:
            return json.loads(data_json)

        # 当日数据: TTL 检查
        if datetime.now() - fetched_dt < timedelta(minutes=TTL_MINUTES):
            return json.loads(data_json)

        return None  # TTL 过期
    finally:
        conn.close()


def set_cache(data_type: str, target_date: date, data: dict):
    """写入缓存。INSERT OR REPLACE 自动覆盖旧数据。"""
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO market_cache (data_type, target_date, data_json, fetched_at) VALUES (?, ?, ?, ?)",
            (data_type, str(target_date), json.dumps(data, ensure_ascii=False), datetime.now().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def clear_cache(data_type: str = None, target_date: date = None):
    """清除缓存。不传参数清空全部。"""
    conn = _connect()
    try:
        if data_type and target_date:
            conn.execute("DELETE FROM market_cache WHERE data_type = ? AND target_date = ?", (data_type, str(target_date)))
        elif data_type:
            conn.execute("DELETE FROM market_cache WHERE data_type = ?", (data_type,))
        else:
            conn.execute("DELETE FROM market_cache")
        conn.commit()
    finally:
        conn.close()


def get_cache_stats() -> dict:
    """缓存统计: 各数据类型的记录数和最新日期"""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT data_type, COUNT(*) as cnt, MAX(target_date) as latest FROM market_cache GROUP BY data_type"
        ).fetchall()
        return {r[0]: {"count": r[1], "latest_date": r[2]} for r in rows}
    finally:
        conn.close()
