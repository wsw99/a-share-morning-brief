"""
A股开盘预测数据面板 — 移动端适配
本地运行: streamlit run web_app.py --server.port 8501
"""
import streamlit as st
from datetime import date, timedelta, datetime
from data_fetchers import fetch_all
from analytics import run_analytics

st.set_page_config(page_title="A股开盘预测", page_icon="📊", layout="wide")

# ─── iPhone 适配样式 ───
st.markdown("""
<style>
    .stButton button {
        width: 100%; height: 50px; font-size: 18px;
        border-radius: 10px; background-color: #1677ff; color: white;
        border: none;
    }
    .stButton button:hover { background-color: #4096ff; }
    .block-container { padding: 1rem; }
    .metric-box {
        background: #f5f7fa; border-radius: 10px; padding: 12px;
        text-align: center; margin-bottom: 8px;
    }
    .metric-value { font-size: 20px; font-weight: bold; }
    .metric-label { font-size: 12px; color: #888; }
    .source-tag { font-size: 11px; color: #999; margin-top: 8px; }
    .signal-bull { color: #cf1322; }
    .signal-bear { color: #16a34a; }
    hr { margin: 8px 0; }
    @media (max-width: 480px) {
        .metric-value { font-size: 16px; }
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 A股开盘预测数据面板")

# ─── 日期选择 ───
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    target_date = st.date_input("选择日期", value=date.today(), max_value=date.today())
with col2:
    st.write("")  # spacer
with col3:
    st.write("")

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    if st.button("⚡ 刷新数据", use_container_width=True):
        with st.spinner("正在从交易所获取数据..."):
            try:
                raw_data = fetch_all(target_date)
                analytics = run_analytics(raw_data)
                st.session_state["raw_data"] = raw_data
                st.session_state["analytics"] = analytics
                st.session_state["has_data"] = True
                st.session_state["last_fetch"] = datetime.now().strftime("%H:%M:%S")
            except Exception as e:
                st.error(f"数据获取失败: {e}")
                st.session_state["has_data"] = False
with col_btn2:
    if st.button("🔄 强制刷新", use_container_width=True, help="清除 SQLite 缓存并重新拉取"):
        from data.cache import clear_cache
        clear_cache()
        st.rerun()

# 缓存状态提示
if st.session_state.get("has_data") and st.session_state.get("last_fetch"):
    flags = st.session_state["raw_data"].get("_cache_flags", {})
    from_cache = [k for k, v in flags.items() if v]
    from_net = [k for k, v in flags.items() if not v]
    parts = []
    if from_cache:
        parts.append(f"缓存命中: {', '.join(from_cache)}")
    if from_net:
        parts.append(f"网络获取: {', '.join(from_net)}")
    st.caption(f"数据获取时间: {st.session_state['last_fetch']} | {' | '.join(parts)}（历史数据永久缓存，当日数据10分钟有效）")

# ─── 数据展示 ───
if st.session_state.get("has_data"):
    raw = st.session_state["raw_data"]
    anl = st.session_state["analytics"]

    # ═══════ 一、主要指数行情 ═══════
    st.markdown("---")
    st.subheader("📈 主要指数行情")

    idx_data = raw["index"]["data"]
    cols = st.columns(len(idx_data))
    for i, (name, info) in enumerate(idx_data.items()):
        with cols[i]:
            if "error" in info:
                st.metric(name, "N/A", delta="数据异常")
            else:
                delta_str = f"{info['change_pct']:+.2f}%" if info["change_pct"] is not None else "N/A"
                st.metric(
                    name,
                    f"{info['close']:,.0f}",
                    delta=delta_str,
                )
                vol_yi = info["volume"] / 1e8
                st.caption(f"成交 {vol_yi:.0f}亿")
    st.caption(f"（数据来源: 东方财富，截至 {raw['index']['updated_at']}）")

    # ═══════ 技术形态 ═══════
    st.markdown("---")
    st.subheader("🔍 技术形态分析")

    tech = anl.get("technical", {})
    cols = st.columns(len(tech))
    for i, (name, t) in enumerate(tech.items()):
        with cols[i]:
            if "error" in t:
                st.caption(f"{name}: 数据不足")
                continue

            ma = t.get("ma", {})
            vol = t.get("volume", {})
            cons = t.get("consolidation", {})

            ma10_s = ma.get("MA10", {}).get("status", "N/A")
            ma20_s = ma.get("MA20", {}).get("status", "N/A")

            st.markdown(f"**{name}**")
            st.caption(f"MA10: {ma10_s} | MA20: {ma20_s}")
            st.caption(f"成交量: {vol.get('signal', 'N/A')} ({vol.get('ratio', 'N/A')}x)")

            if cons.get("is_consolidating"):
                st.caption(f"横盘整理中 (振幅 {cons.get('amplitude_5d_pct', '')}%)")
    st.caption("（数据来源: 东方财富，Python 本地计算）")

    # ═══════ 三、ETF 资金流向 ═══════
    st.markdown("---")
    st.subheader("💰 ETF 资金流向 Top 5 (按成交额)")

    etf = anl.get("etf", {})
    top_etfs = etf.get("top_by_volume", [])
    if top_etfs:
        cols = st.columns(len(top_etfs))
        for i, e in enumerate(top_etfs):
            with cols[i]:
                change = e.get("change_pct")
                color = "#cf1322" if (change and change > 0) else "#16a34a" if (change and change < 0) else "#666"
                st.markdown(
                    f"<div style='font-weight:bold;font-size:14px'>{e['name'][:12]}</div>"
                    f"<div style='font-size:20px;color:{color}'>{change:+.2f}%</div>"
                    f"<div style='font-size:11px;color:#999'>成交 {e.get('volume',0)/1e8:.1f}亿</div>"
                    if change is not None
                    else f"<div style='font-weight:bold'>{e['name'][:12]}</div>",
                    unsafe_allow_html=True,
                )
    st.caption(f"（数据来源: 东方财富 ETF 风向标，截至 {raw['etf_flow']['updated_at']}）")

    # ═══════ 四、融资融券 ═══════
    st.markdown("---")
    st.subheader("📊 融资融券（市场人气指标）")

    margin = anl.get("margin", {})
    if "error" not in margin:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("两市融资余额", f"{margin['latest_total_margin']/1e8:.0f}亿")
        with col2:
            st.metric("近一周变化", f"{margin['one_week_change_pct']:+.2f}%")
        with col3:
            st.metric("连续趋势", f"{margin['trend_direction']}{margin['trend_days']}日")
        with col4:
            st.metric("人气判断", margin.get("signal", "N/A"))
    else:
        st.warning(margin.get("error", "数据暂不可用"))
    st.caption(f"（数据来源: 沪深交易所，截至 {raw['margin']['updated_at']}）")

    # ═══════ 五、股指期货升贴水 ═══════
    st.markdown("---")
    st.subheader("📉 股指期货升贴水")

    futures = anl.get("futures", {})
    if futures:
        cols = st.columns(len(futures))
        for i, (sym, f) in enumerate(futures.items()):
            with cols[i]:
                if "error" in f:
                    st.caption(f"{sym}: 数据暂缺")
                    continue
                basis = f.get("basis_rate")
                if basis is not None:
                    basis_display = f"{basis:+.2f}%"
                    basis_color = "#cf1322" if basis > 0 else "#16a34a" if basis < 0 else "#666"
                    st.markdown(
                        f"<div style='font-weight:bold'>{sym} ({f.get('name','')})</div>"
                        f"<div style='font-size:20px'>{f.get('price','N/A')}</div>"
                        f"<div style='font-size:14px;color:{basis_color}'>{f.get('basis_type','')} {basis_display}</div>"
                        f"<div style='font-size:11px;color:#999'>{f.get('signal','')}</div>",
                        unsafe_allow_html=True,
                    )
    st.caption(f"（数据来源: 中国金融期货交易所，截至 {raw['futures']['updated_at']}）")

    # ═══════ 六、消息面（占位） ═══════
    st.markdown("---")
    st.subheader("📰 消息面")
    st.info("消息面采集功能将在 Step 2 中接入（财联社 / 新浪财经 RSS）")
    st.caption(f"（数据来源: 待接入，截至 {raw['news']['updated_at']}）")

elif not st.session_state.get("has_data"):
    st.info("👆 点击「刷新数据」按钮开始获取今日市场数据")

# ─── 底部 ───
st.markdown("---")
st.caption("A股开盘预测数据面板 v0.1 | 数据先行, LLM 生成将在 Step 2 接入")
