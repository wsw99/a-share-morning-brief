# 开发日志

## 2026-05-28

### 优化: 数据缓存从 Streamlit 内存缓存迁移至 SQLite

- **背景**: 每次点「刷新数据」都要重新拉取所有接口（指数/ETF/融资融券/期货/消息），等待时间长
- **方案**: SQLite 本地数据库做持久化缓存（`data/market_cache.db`）
- **缓存策略**:
  - 历史日期（非今日）: 收盘数据不会变，永久缓存
  - 当日数据: TTL=10分钟，超时后重新拉取（盘中数据可能更新）
- **新增文件**:
  - `data/cache.py` — `get_cached()` / `set_cache()` / `clear_cache()` / `get_cache_stats()`
  - `data/market_cache.db` — SQLite 文件，WAL 模式
- **修改文件**:
  - `data_fetchers/__init__.py` — `fetch_all()` 每类数据先查缓存，未命中才走网络；返回 `_cache_flags` 标记每类数据的来源
  - `web_app.py` — 去掉 `@st.cache_data`，缓存状态栏显示每类数据命中情况（缓存命中: index, margin | 网络获取: futures）
- **验证**: 首次拉取全部走网络，二次拉取全部命中缓存（SQLite 查询 <1ms）

## 2026-05-27

### 问题 1: SSL 证书错误 — `query.sse.com.cn` 自签名证书

- **现象**: 调用融资融券沪市接口 `ak.stock_margin_sse()` 时报 SSL 验证失败
- **原因**: 上交所 `query.sse.com.cn` 使用自签名证书，Python 默认 SSL 严格校验不通过
- **解决**: 创建 `utils/ssl_patch.py`，全局禁用 SSL 证书验证：
  ```python
  ssl._create_default_https_context = ssl._create_unverified_context
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  ```
- **注意**: 此 patch 必须在所有 AkShare 调用之前 import，已在 `data_fetchers/__init__.py` 最顶部执行

### 问题 2: SSL 错误 — `hq.sinajs.cn` 新浪财经

- **现象**: `ak.futures_zh_spot()` 调用时报 SSL 错误
- **原因**: 新浪财经数据接口同样使用自签名证书
- **解决**: 同问题 1，`ssl_patch.py` 覆盖

### 问题 3: SSL EOF 错误 — `www.szse.cn` 深交所

- **现象**: 融资融券深市接口 `ak.stock_margin_szse()` 间歇性 SSL EOF 错误
- **原因**: 深交所服务器端 SSL 实现问题，不是每次必现，属于服务端不稳定
- **解决**: 用 try/except 包裹深市调用，失败时静默降级，仅使用沪市数据兜底
- **影响**: 融资融券总余额在深市不可用时只统计沪市，数据仍可用但不完整

### 问题 4: `stock_margin_szse()` 参数不兼容

- **现象**: 传入 `start_date` 关键字参数时报错
- **原因**: 深市接口只接受单个 `date` 参数，不支持日期范围查询（与沪市接口不同）
- **解决**: 改为 `ak.stock_margin_szse(date=dt_str)` 仅查询目标日期

### 问题 5: 深市融资融券列名不匹配

- **现象**: 尝试 rename `信用交易日期` 列时报 KeyError
- **原因**: 深市数据为单行汇总，无 `信用交易日期` 列，列名结构也与沪市不同（如 `融资余额`、`融券余额`）
- **解决**: 移除对深市数据的列重命名，直接按实际列名读取

### 问题 6: 深市融资融券单位不一致

- **现象**: 深市数值与其他数据源相差 1e8 倍
- **原因**: 沪市数据单位为**元**，深市数据单位为**亿元**
- **解决**: 深市数据乘以 `1e8` 统一为元

### 问题 7: `futures_zh_spot()` 返回 "list index out of range"

- **现象**: `ak.futures_zh_spot(symbol="IF")` 等调用时报 list index out of range
- **原因**: AkShare 对 Sina 期货实时行情的 HTML 解析失败，可能是 Sina 页面结构变更
- **解决**: 切换到 `ak.futures_main_sina(symbol='IF0')` 主力连续合约接口，该接口工作正常
- **变更**: 合约代码从 `IF` → `IF0`、`IC` → `IC0` 等

### 问题 8: 期货升贴水率返回 N/A

- **现象**: `futures_analyzer.py` 计算升贴水率时，4 个合约全部返回 N/A
- **原因**: 升贴水 = (期货价 - 现货价) / 现货价，需要对应现货指数（沪深300、中证500、上证50、中证1000），但 `index_fetcher.py` 最初只采集了上证综指、深证成指、创业板指、科创50
- **解决**: 在 `index_fetcher.py` 的 `INDEX_SYMBOLS` 中补充 4 个期货对标的现货指数

### 问题 9: Streamlit 首次启动交互式提示阻塞

- **现象**: 首次运行 `streamlit run web_app.py` 时，弹出交互式邮箱确认提示，阻塞启动
- **原因**: Streamlit 首次启动会询问是否收集使用统计
- **解决**: 创建 `.streamlit/config.toml` 配置文件，设置 `headless = true` 和 `gatherUsageStats = false`，静默启动
