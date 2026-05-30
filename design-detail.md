# A股开盘预测智能体 — 轻量设计方案

## 一、总体架构（云服务器 + iPhone Safari 访问）

### 1.1 访问方式

```
你的 iPhone
   │
   │  Safari 打开 http://你的服务器IP:8501
   │  添加到主屏幕 → 用起来跟 App 一样
   │
   ▼
云服务器 (阿里云/腾讯云轻量应用服务器, ¥50-70/月)
   │
   ├── main.py                     # 核心逻辑
   ├── data_fetchers/              # 数据采集（AkShare，免费）
   ├── analytics/                  # 技术指标计算（纯 Python）
   ├── compliance/                 # 合规校验（规则引擎）
   ├── prompts/                    # Prompt 模板
   ├── web_app.py                  # 移动端网页界面
   ├── output/                     # 生成的报告
   └── config.yaml                 # API Key、偏好设置
```

**核心思路**：全部数据计算用 Python（消除幻觉），LLM 只负责"把数据写成合规的中文报告"。服务跑在一台最便宜的云服务器上，iPhone 用浏览器就能访问。如果加一个飞书/微信机器人，甚至可以做到每天早上自动推送到手机。

### 1.2 云服务器选型

| 方案 | 配置 | 月费 | 够用吗 |
|------|------|------|--------|
| **阿里云轻量应用服务器** | 2核 2GB, 3Mbps | ¥50-60 | ✅ 完全够用 |
| **腾讯云轻量应用服务器** | 2核 2GB, 3Mbps | ¥50-65 | ✅ 完全够用 |
| **华为云 Flexus** | 2核 2GB | ¥45-55 | ✅ 完全够用 |
| 自己电脑 + 内网穿透（frp） | 无需额外费用 | ¥0 | ⚠️ 电脑必须一直开着 |

> 推荐阿里云或腾讯云轻量服务器，选 Ubuntu 22.04 镜像，开箱即用。2核2GB 跑一个小 Python 服务 + 网页绰绰有余。

### 1.3 iPhone 端体验

不需要开发 iOS App。用 **Streamlit** 写一个移动端适配的网页，Safari 打开后**添加到主屏幕**，图标、全屏体验和原生 App 几乎一样：

```
┌──────────────────────────┐
│  A股开盘预测          📅 │  ← 顶部栏
├──────────────────────────┤
│                          │
│   📅 日期: 2026-05-22   │  ← 默认今天
│                          │
│   ┌──────────────────┐   │
│   │  ⚡ 生成今日报告   │   │  ← 点一下就开始生成
│   └──────────────────┘   │
│                          │
│   ── 历史报告 ──         │
│   📄 2026-05-21 开盘预测 │  ← 可滑动查看历史
│   📄 2026-05-20 开盘预测 │
│   📄 2026-05-19 开盘预测 │
│                          │
└──────────────────────────┘
```

附加能力：
- **定时自动生成**：服务器每天早上 7:00 自动跑，报告已经在那里了，打开就能看
- **推送通知**：如果想主动收到通知，可以接一个飞书机器人 webhook，生成完成后自动发消息到手机上的飞书

---

## 二、LLM 怎么选

### 直接结论：用 DeepSeek API

| 考虑因素 | 结论 |
|----------|------|
| **能不能私有化部署？** | 个人使用不需要私有化。你传给 DeepSeek API 的都是**公开行情数据**（指数、成交量、融资余额），不涉及客户持仓或交易记录，合规上没有数据出境风险（DeepSeek 服务器在国内） |
| **中文金融文本质量？** | DeepSeek 中文金融语料积累深厚，S&P Kensho 金融测试 91.72%，生成研报风格自然 |
| **多少钱？** | DeepSeek API 定价约 ¥1/百万 token。生成一份 500 字报告约消耗 3000-5000 token，成本约 **¥0.003-0.005**。一个月 22 个交易日 ≈ **¥0.1-0.2** |
| **要不要备选模型？** | 可以顺手接一个 Qwen API（通义千问）当备选，价格差不多，某一家挂了自动切 |

### 什么时候才需要本地部署 LLM？

如果你后续要处理**包含客户持仓信息的内部研报**，或者公司合规要求数据不能出内网，那时候再考虑本地部署一个 DeepSeek 蒸馏版（单张消费级显卡如 RTX 4090 24GB 就能跑 32B 模型）。

---

## 三、成本

| 项目 | 月费用 |
|------|--------|
| 云服务器（阿里云/腾讯云轻量） | ¥50-70 |
| DeepSeek API | ¥0.1-0.5（按量计费） |
| AkShare 数据源 | ¥0（免费开源） |
| **合计** | **约 ¥50-70/月** |

> 如果暂时不想租服务器，先在自己电脑上跑 `streamlit run web_app.py`，用 frp/ngrok 内网穿透也能从 iPhone 访问，成本为 0。但电脑要一直开着。

---

## 四、数据采集（AkShare 一条龙）

全部数据用 AkShare 免费获取，不需要 API Key：

| 需要的数据 | AkShare 接口 | 什么时候能拿到 |
|-----------|-------------|---------------|
| 指数行情（上证/深证/创业板/科创50） | `stock_zh_index_daily` | T日 18:00 |
| ETF 资金流向 | `fund_etf_spot_em` | T日 18:00 |
| 融资融券余额 | `stock_margin_sse` / `stock_margin_szse` | T日 20:00 |
| 股指期货（IF/IC/IH/IM） | `futures_zh_spot` | T日 15:30 |
| 北向资金 | `stock_hsgt_hist_em` | T日 18:00 |
| 消息面 | 财联社 RSS / 新浪财经 | 实时抓取 |

数据拉下来后本地存一份 JSON 或 SQLite 文件，方便以后回看。

```
数据采集时序（以生成 5/22 报告为例）：

5/21 15:00  收盘 → 指数、成交量可拉
5/21 15:30  期货收盘 → 升贴水可算
5/21 18:00  → ETF资金流向、北向资金可拉
5/21 20:00  → 融资融券可拉
5/21 夜间   → 消息面持续更新
5/22 06:00  全部数据就绪 → 跑脚本生成报告
5/22 07:00  报告出现在 output/ 目录
```

---

## 五、核心流水线

```
┌─────────────┐
│ 1.数据采集    │  Python: AkShare 拉数据 → raw_data.json
└──────┬──────┘
       ▼
┌─────────────┐
│ 2.技术分析    │  Python: 算均线突破、放量、基差、融资趋势 → analytics.json
└──────┬──────┘   这一步完全不用 LLM，确定性计算
       ▼
┌─────────────┐
│ 3.报告生成    │  LLM: 把 analytics.json 写成 500 字合规中文报告
└──────┬──────┘  一次 LLM 调用完成（不需要多 Agent 拆来拆去）
       ▼
┌─────────────┐
│ 4.合规校验    │  Python 规则引擎: 检测个股名、激进词、数据标注完整性
└──────┬──────┘  如果不过 → 返回步骤3重写
       ▼
┌─────────────┐
│ 5.输出       │  写 Markdown 文件，终端打印
└─────────────┘
```

**为什么不需要多 Agent 拆成大纲→分段→润色？**

你的报告总共 500 字，一次 LLM 调用完全能处理。拆成多次调用反而增加延迟、成本和出错概率。只有在报告长度超过 5000 字、需要多轮结构化协作时才值得引入 LangGraph 多 Agent。

---

## 六、代码骨架

### 6.1 项目结构

```
project_agent/
├── main.py                    # 入口脚本
├── config.yaml                # 配置（API Key、偏好板块）
├── requirements.txt           # 依赖
├── data_fetchers/
│   ├── __init__.py
│   ├── index_fetcher.py       # 指数行情
│   ├── etf_flow_fetcher.py    # ETF资金流向
│   ├── margin_fetcher.py      # 融资融券
│   ├── futures_fetcher.py     # 股指期货
│   └── news_fetcher.py        # 消息面
├── analytics/
│   ├── __init__.py
│   ├── technical.py           # 均线突破、放量检测
│   ├── margin_analyzer.py     # 融资趋势分析
│   ├── futures_analyzer.py    # 升贴水计算
│   └── etf_analyzer.py        # 板块资金排名
├── compliance/
│   ├── __init__.py
│   └── checker.py             # 合规校验规则
├── prompts/
│   └── system_prompt.txt      # System Prompt 模板
├── output/                    # 生成的报告
│   └── 2026-05-22_开盘预测.md
└── utils/
    ├── __init__.py
    └── llm_client.py          # DeepSeek API 调用封装
```

### 6.2 主流程 (main.py)

```python
import json
from datetime import date
from data_fetchers import fetch_all
from analytics import run_analytics
from compliance import check
from utils.llm_client import call_deepseek

def generate_report(target_date: date) -> str:
    # Step 1: 拉数据（纯 Python）
    raw_data = fetch_all(target_date)

    # Step 2: 技术分析（纯 Python）
    analytics = run_analytics(raw_data)

    # Step 3: LLM 生成报告（一次调用）
    draft = call_deepseek(
        system_prompt="prompts/system_prompt.txt",
        user_message=json.dumps(analytics, ensure_ascii=False)
    )

    # Step 4: 合规校验
    result = check(draft)
    retry = 0
    while not result["passed"] and retry < 3:
        draft = call_deepseek(
            system_prompt="prompts/system_prompt.txt",
            user_message=json.dumps(analytics, ensure_ascii=False),
            extra_instruction=f"上次校验未通过：{result['issues']}，请修正。"
        )
        result = check(draft)
        retry += 1

    # Step 5: 输出
    output_path = f"output/{target_date.isoformat()}_开盘预测.md"
    with open(output_path, "w") as f:
        f.write(draft)

    return draft
```

### 6.3 数据采集示例

```python
# data_fetchers/margin_fetcher.py
import akshare as ak
from datetime import date, timedelta

def fetch_margin_data(target_date: date):
    """获取沪深两市融资融券数据，包含近一周变化"""
    df_sse = ak.stock_margin_sse(start_date="20200101", end_date=str(target_date))
    df_szse = ak.stock_margin_szse(start_date="20200101", end_date=str(target_date))

    # 计算近一周趋势
    one_week_ago = target_date - timedelta(days=7)
    recent = df_sse[df_sse["日期"] >= str(one_week_ago)]

    return {
        "latest_margin_sse": float(df_sse.iloc[-1]["融资余额"]),
        "latest_margin_szse": float(df_szse.iloc[-1]["融资余额"]),
        "total_margin": float(df_sse.iloc[-1]["融资余额"] + df_szse.iloc[-1]["融资余额"]),
        "one_week_change_pct": float((recent.iloc[-1]["融资余额"] - recent.iloc[0]["融资余额"]) / recent.iloc[0]["融资余额"] * 100),
        "source": "沪深交易所",
        "updated_at": str(target_date)
    }
```

### 6.4 技术分析示例

```python
# analytics/technical.py
import numpy as np

def detect_ma_breakout(df, ma_periods=[10, 20]):
    """检测主要指数是否突破关键均线"""
    results = {}
    for period in ma_periods:
        df[f"MA{period}"] = df["close"].rolling(period).mean()
        latest_close = df.iloc[-1]["close"]
        latest_ma = df.iloc[-1][f"MA{period}"]
        yesterday_close = df.iloc[-2]["close"]
        yesterday_ma = df.iloc[-2][f"MA{period}"]

        # 今日站上均线 且 昨日在均线下方 = 突破
        if latest_close > latest_ma and yesterday_close < yesterday_ma:
            results[f"MA{period}"] = "向上突破"
        elif latest_close < latest_ma and yesterday_close > yesterday_ma:
            results[f"MA{period}"] = "向下跌破"
        else:
            results[f"MA{period}"] = "线上" if latest_close > latest_ma else "线下"

    return results

def detect_volume_surge(df):
    """检测成交量是否放大（对比20日均量）"""
    vol_ma20 = df["volume"].rolling(20).mean()
    latest_vol = df.iloc[-1]["volume"]
    avg_vol = vol_ma20.iloc[-1]
    ratio = latest_vol / avg_vol

    if ratio > 1.5:
        return {"status": "显著放量", "ratio": round(ratio, 2)}
    elif ratio > 1.2:
        return {"status": "温和放量", "ratio": round(ratio, 2)}
    else:
        return {"status": "正常", "ratio": round(ratio, 2)}
```

### 6.5 合规校验示例

```python
# compliance/checker.py
import re

# 硬规则
FORBIDDEN_WORDS = [
    "暴涨", "暴跌", "必涨", "翻倍", "抄底", "逃顶",
    "保证", "肯定", "绝对", "稳赚", "内幕", "消息股"
]

# A股个股名称（简化示例，实际需加载全量名单）
STOCK_NAMES = load_stock_name_list()  # 从文件加载 A 股全量名单

def check(report_text: str) -> dict:
    issues = []

    # 1. 个股名称检测
    for name in STOCK_NAMES:
        if len(name) >= 3 and name in report_text:  # 过滤太短的（避免误伤常用词）
            issues.append(f"包含个股名称: {name}")

    # 2. 激进用语检测
    for word in FORBIDDEN_WORDS:
        if word in report_text:
            issues.append(f"包含违规用语: {word}")

    # 3. 数据来源标注检测
    if "数据来源" not in report_text:
        issues.append("缺少数据来源标注")

    # 4. 字数检测
    if len(report_text) > 550:  # 留 10% 余量
        issues.append(f"超出字数限制: {len(report_text)}字")

    return {
        "passed": len(issues) == 0,
        "issues": issues
    }
```

### 6.6 LLM 调用封装

```python
# utils/llm_client.py
from openai import OpenAI

# DeepSeek API 兼容 OpenAI 格式
client = OpenAI(
    api_key="your-deepseek-api-key",
    base_url="https://api.deepseek.com"
)

def call_deepseek(system_prompt: str, user_message: str,
                  extra_instruction: str = None) -> str:
    messages = [{"role": "system", "content": system_prompt}]

    user_content = user_message
    if extra_instruction:
        user_content += f"\n\n额外要求：{extra_instruction}"

    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model="deepseek-chat",  # 或 deepseek-reasoner
        messages=messages,
        temperature=0.2,
        max_tokens=1500
    )

    return response.choices[0].message.content
```

---

## 七、Prompt 模板

```markdown
你是一位经验丰富的证券投资顾问，请根据以下数据撰写一篇A股开盘预测报告。

## 今日数据
{analytics_json}

## 写作要求
1. 全文不超过500字，根据文意自然分段，不要用数字标题
2. 所有论点必须有数据支撑，不得做无依据的判断
3. 每个数据点后标注来源和截止时间，如（数据来源：上交所，截至X月X日）
4. 全文末尾汇总所有数据来源
5. 严禁提及任何具体个股名称或股票代码
6. 严禁使用"暴涨""暴跌""必涨""翻倍""抄底"等激进用语
7. 用语专业、客观、合规

## 报告结构建议
- 前一日市场概述（指数涨跌、成交量变化）
- 热点板块与ETF资金流向
- 股指期货升贴水与融资融券人气指标
- 消息面影响
- 后市判断
```

---

## 八、移动端网页（web_app.py）

### 8.1 完整代码

```python
# web_app.py
import streamlit as st
from datetime import date, timedelta
from pathlib import Path
from main import generate_report

st.set_page_config(
    page_title="A股开盘预测",
    page_icon="📊",
    layout="wide"
)

# --- iPhone 适配 ---
st.markdown("""
<style>
    /* 让按钮更大，方便手指点击 */
    .stButton button {
        width: 100%;
        height: 50px;
        font-size: 18px;
        border-radius: 10px;
    }
    /* 报告正文行距，方便手机阅读 */
    .report-text {
        line-height: 1.8;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 A股开盘预测")

# --- 日期选择 ---
target_date = st.date_input(
    "选择日期",
    value=date.today(),
    max_value=date.today()
)

# --- 生成按钮 ---
if st.button("⚡ 生成报告", use_container_width=True):
    with st.spinner("正在采集数据并生成报告..."):
        try:
            report = generate_report(target_date)
            st.success("报告已生成")

            # 显示报告
            st.markdown("---")
            st.markdown(f"## {target_date.isoformat()} A股开盘预测")
            st.markdown(report)

            # 复制按钮
            st.button("📋 复制全文", use_container_width=True,
                      on_click=lambda: st.write(report))
        except Exception as e:
            st.error(f"生成失败: {e}")

# --- 历史报告列表 ---
st.markdown("---")
st.subheader("📂 历史报告")

output_dir = Path("output")
if output_dir.exists():
    files = sorted(output_dir.glob("*.md"), reverse=True)
    for f in files[:10]:  # 最近10篇
        date_str = f.stem.split("_")[0]
        with open(f) as fp:
            content = fp.read()
        with st.expander(f"📄 {date_str} 开盘预测"):
            st.markdown(content)
else:
    st.info("暂无历史报告")
```

### 8.2 添加到 iPhone 主屏幕（变成"假 App"）

1. iPhone Safari 打开 `http://你的服务器IP:8501`
2. 点底部中间的**分享按钮**（方框带箭头）
3. 往下滑，点**「添加到主屏幕」**
4. 改个名字，点「添加」

效果：主屏幕上多一个图标，点开就是全屏网页，和 App 体验一样。

---

## 九、飞书推送详细方案

### 9.1 整体流程

```
每天早上 7:00
     │
     ▼
云服务器定时任务 (systemd timer / cron)
     │
     ▼
scheduler.py 触发 generate_report()
     │
     ├── 拉数据 (AkShare)
     ├── 算指标 (Python)
     ├── LLM 写报告 (DeepSeek API)
     └── 合规校验
     │
     ▼
报告生成完毕
     │
     ├── 存为 Markdown 文件 (output/2026-05-22_开盘预测.md)
     │
     └── 飞书机器人 webhook 推送
          │
          ▼
    你的 iPhone 上的飞书 App 收到消息
    ┌─────────────────────────────┐
    │  📊 5月22日 A股开盘预测      │
    │                             │
    │  昨日上证综指收报3,421.23点， │
    │  涨幅0.32%，两市成交...      │
    │                             │
    │  [查看完整报告]              │  ← 点击跳转网页看完整版
    └─────────────────────────────┘
```

### 9.2 第一步：创建飞书机器人

1. **打开飞书 App**（电脑端操作比较方便），在左侧找到「工作台」→ 搜索「飞书机器人」

2. **创建一个群聊**（你和机器人两个人的群就行）：
   - 飞书右上角 `+` → 「发起群聊」
   - 随便拉一个同事然后踢掉，或者创建一个只有自己的群
   - 群名称比如「A股早报」

3. **在群里添加机器人**：
   - 群聊界面右上角「设置」→ 「群机器人」→ 「添加机器人」
   - 选择「自定义机器人」
   - 机器人名字填「A股早报助手」
   - 安全设置选「自定义关键词」，填 `📊`（这样只有包含 📊 的消息才能发出去，防止 webhook 泄露后被滥用）
   - 点「完成」后会得到一个 **Webhook 地址**，长这样：
     ```
     https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxxx
     ```
   - 把这个地址记下来，后面要填到 config.yaml 里

### 9.3 第二步：消息格式设计

500 字报告 + 飞书纯文本消息的 20KB 限制完全够用。但为了让手机上看更舒服，用飞书的**富文本/卡片消息**会更好：

```python
# feishu_pusher.py
import requests
import hashlib
import base64
import hmac
import time

class FeishuPusher:
    def __init__(self, webhook_url: str, secret: str = None):
        self.webhook_url = webhook_url
        self.secret = secret

    def _sign(self) -> dict:
        """如果设置了签名校验，生成签名"""
        if not self.secret:
            return {}
        timestamp = str(int(time.time()))
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode(), string_to_sign.encode(), hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode()
        return {"timestamp": timestamp, "sign": sign}

    def send_report(self, report_text: str, target_date: str, web_url: str = None):
        """推送报告到飞书"""

        # 飞书消息最长 20KB，500 字报告完全没问题
        # 如果报告太长，就截一段预览 + 链接
        if len(report_text) > 1000:
            preview = report_text[:400] + "\n\n...（完整报告请点击下方链接查看）"
        else:
            preview = report_text

        payload = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {"tag": "plain_text", "content": f"📊 {target_date} A股开盘预测"},
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": preview
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {"tag": "plain_text", "content": f"⏰ 生成时间: {target_date} 07:00 | 数据来源见报告末尾"}
                        ]
                    }
                ]
            }
        }

        # 如果有网页链接，加一个跳转按钮
        if web_url:
            payload["card"]["elements"].insert(-1, {
                "tag": "action",
                "actions": [{
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": "🔗 查看完整报告"},
                    "type": "primary",
                    "url": web_url
                }]
            })

        # 加签名（如果配置了）
        payload.update(self._sign())

        resp = requests.post(self.webhook_url, json=payload)
        if resp.status_code == 200 and resp.json().get("code") == 0:
            print("✅ 飞书推送成功")
        else:
            print(f"❌ 飞书推送失败: {resp.text}")

    def send_error(self, error_msg: str):
        """推送错误告警"""
        requests.post(self.webhook_url, json={
            "msg_type": "text",
            "content": {"text": f"⚠️ 早报生成失败\n{error_msg}"}
        })
```

### 9.4 第三步：定时任务

用 systemd timer（比 cron 更可靠，失败有日志）：

**scheduler.py**

```python
# scheduler.py
from datetime import date
from main import generate_report
from feishu_pusher import FeishuPusher
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)

pusher = FeishuPusher(
    webhook_url=config["feishu"]["webhook"],
    secret=config["feishu"].get("secret")
)

SERVER_IP = config["server"]["ip"]  # 云服务器公网 IP

def daily_job():
    today = date.today()
    target_date_str = today.isoformat()

    try:
        report = generate_report(today)
        print(f"{target_date_str} 报告生成成功，{len(report)}字")

        # 推飞书，附带网页链接
        web_url = f"http://{SERVER_IP}:8501"
        pusher.send_report(
            report_text=report,
            target_date=target_date_str,
            web_url=web_url
        )
    except Exception as e:
        pusher.send_error(f"{target_date_str}: {e}")
        raise

if __name__ == "__main__":
    daily_job()
```

**注册 systemd 定时任务**（在云服务器上执行）：

```bash
# 1. 创建 service 文件
sudo tee /etc/systemd/system/morning-brief.service << 'EOF'
[Unit]
Description=A股开盘预测早报生成
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/project_agent
ExecStart=/usr/bin/python3 /home/ubuntu/project_agent/scheduler.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 2. 创建 timer 文件（每天早上 7:00 执行）
sudo tee /etc/systemd/system/morning-brief.timer << 'EOF'
[Unit]
Description=A股早报定时任务 - 每日7:00
Requires=morning-brief.service

[Timer]
OnCalendar=daily
OnCalendar=07:00
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target
EOF

# 3. 起用
sudo systemctl daemon-reload
sudo systemctl enable morning-brief.timer
sudo systemctl start morning-brief.timer
```

**常用管理命令**：

```bash
# 查看定时任务状态
systemctl status morning-brief.timer

# 查看最近一次执行日志
journalctl -u morning-brief.service -n 50

# 手动触发一次（测试用）
sudo systemctl start morning-brief.service

# 查看下次执行时间
systemctl list-timers morning-brief.timer
```

### 9.5 第四步：测试

部署完后，先在服务器上手动跑一次确认没问题：

```bash
cd /home/ubuntu/project_agent
python3 scheduler.py
```

如果一切正常，iPhone 上的飞书应该立刻收到一条消息。确认收到后再启用定时任务。

### 9.6 最终体验

每天早上的流程就变成了：

```
iPhone 通知栏弹出飞书消息 🛎️
   │
   ▼
打开飞书 → 群聊「A股早报」
   │
   ├── 📊 5月22日 A股开盘预测（卡片消息，直接在聊天里看完500字）
   │
   └── 想细看？点「🔗 查看完整报告」→ 跳转 Safari 网页（历史报告都在）
```

**不需要打开电脑、不需要主动去任何地方**，报告每天准时推送。万一某天生成失败了（比如数据源挂了），会收到一条 `⚠️ 早报生成失败` 的告警消息，知道需要去检查一下。

---

## 十、几步跑起来（含飞书推送）

| 步骤 | 做什么 | 预估时间 |
|------|--------|----------|
| 1 | 购买云服务器（阿里云轻量，Ubuntu 22.04），获取公网 IP | 10 分钟 |
| 2 | SSH 登录，装 Python 和依赖 `pip install akshare openai streamlit pyyaml` | 10 分钟 |
| 3 | 申请 DeepSeek API Key（platform.deepseek.com），充 10 块钱够用一年 | 10 分钟 |
| 4 | 写 `config.yaml`，填入 API Key | 1 分钟 |
| 5 | 实现 5 个 data_fetcher，每个 ~30 行 | 半天 |
| 6 | 实现 analytics 模块（4 个分析器） | 半天 |
| 7 | 写 Prompt 模板 + 调 LLM 调用 | 2 小时 |
| 8 | 写合规校验规则 | 1 小时 |
| 9 | 串起来 main.py，跑通第一份报告 | 1 小时 |
| 10 | 部署 web_app.py（`streamlit run web_app.py --server.port 8501`） | 10 分钟 |
| 11 | 配置云服务器防火墙（放行 8501 端口） | 5 分钟 |
| 12 | iPhone Safari 访问 IP:8501，添加到主屏幕 | 2 分钟 |
| 13 | （可选）配置飞书机器人 + 定时任务 | 1 小时 |
| 14 | 反复调试 Prompt + 规则，直到报告质量满意 | 1-2 天 |
| **合计** | | **大约一周** |

---

## 十一、什么时候才需要升级到"重"架构？

| 信号 | 当前方案不够用的原因 | 升级方向 |
|------|---------------------|---------|
| 每天要生成超过 10 份不同板块的报告 | 单次调用太慢 | 加并发（asyncio + 批量 LLM 调用） |
| 公司合规要求 LLM 必须本地部署 | API 数据出境问题 | 加一张 RTX 4090 跑 DeepSeek 蒸馏版 |
| 多人使用，需要权限管理 | 单机脚本管不了多人 | 加 Streamlit + SQLite 用户管理 |
| 报告质量需要持续评估 | 靠人工看太累 | 加自动化评测 + 历史回溯对比 |

在此之前，越简单越好。
