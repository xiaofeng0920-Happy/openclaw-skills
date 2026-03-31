# 📊 Finnhub API 配置指南

> 为 Marcus 股票日报提供实时行情数据

---

## 🔑 获取 API Key

### 步骤 1: 注册账号
访问：https://finnhub.io/register

1. 填写邮箱和密码
2. 验证邮箱
3. 登录 Dashboard

### 步骤 2: 获取 API Key
1. 登录后访问：https://finnhub.io/dashboard
2. 复制你的 API Key（类似：`xxxxxxxxxxxxxxxxxxxx`）

### 步骤 3: 保存到本地
```bash
# 创建配置目录
mkdir -p ~/.openclaw/workspace/config

# 保存 API Key
echo "YOUR_FINNHUB_API_KEY" > ~/.openclaw/workspace/config/finnhub_api_key.txt

# 设置权限（仅自己可读）
chmod 600 ~/.openclaw/workspace/config/finnhub_api_key.txt
```

---

## 📈 Finnhub 免费计划

| 功能 | 限制 |
|------|------|
| **API 调用** | 60 次/分钟 |
| **实时股价** | ✅ 支持 |
| **盘前/盘后数据** | ✅ 支持 |
| **公司基本面** | ✅ 支持 |
| **新闻数据** | ✅ 支持 |
| **技术指标** | ✅ 支持 |

**足够用吗？** 
- ✅ 每日监控 5-10 只股票完全够用
- ✅ 每次调用只消耗 1 次配额

---

## 🔧 API 使用示例

### 1. 获取实时股价
```bash
API_KEY="你的 API_KEY"
SYMBOL="NVDA"

curl -s "https://finnhub.io/api/v1/quote?symbol=${SYMBOL}&token=${API_KEY}"
```

**返回示例：**
```json
{
  "c": 140.25,  // 当前价格
  "h": 142.50,  // 当日最高
  "l": 138.75,  // 当日最低
  "o": 139.50,  // 开盘价
  "pc": 138.90, // 前收盘价
  "t": 1710504000 // 时间戳
}
```

### 2. 获取盘前价格
```bash
curl -s "https://finnhub.io/api/v1/stock/market-movers?token=${API_KEY}"
```

### 3. 获取公司新闻
```bash
curl -s "https://finnhub.io/api/v1/company-news?symbol=AAPL&from=2026-03-15&to=2026-03-15&token=${API_KEY}"
```

### 4. 获取技术指标
```bash
curl -s "https://finnhub.io/api/v1/stock/technical-indicator?symbol=AAPL&resolution=D&from=1710400000&to=1710500000&indicators=rsi&token=${API_KEY}"
```

---

## 🛠️ 集成到 Marcus

### 更新 generate_report.sh

在脚本开头添加：

```bash
# 加载 Finnhub API Key
API_KEY_FILE="$HOME/.openclaw/workspace/config/finnhub_api_key.txt"
if [ -f "$API_KEY_FILE" ]; then
    FINNHUB_API_KEY=$(cat "$API_KEY_FILE")
else
    echo "❌ 未找到 Finnhub API Key"
    echo "请按 FINNHUB_SETUP.md 配置"
    exit 1
fi

# 获取实时股价函数
get_stock_price() {
    local symbol=$1
    curl -s "https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}" | \
    grep -o '"c":[0-9.]*' | cut -d':' -f2
}

# 获取涨跌幅
get_stock_change() {
    local symbol=$1
    local data=$(curl -s "https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}")
    local current=$(echo "$data" | grep -o '"c":[0-9.]*' | cut -d':' -f2)
    local prev_close=$(echo "$data" | grep -o '"pc":[0-9.]*' | cut -d':' -f2)
    echo "scale=2; (($current - $prev_close) / $prev_close) * 100" | bc
}
```

---

## 📋 配置检查清单

- [ ] 注册 Finnhub 账号
- [ ] 获取 API Key
- [ ] 保存到 `~/.openclaw/workspace/config/finnhub_api_key.txt`
- [ ] 设置文件权限 `chmod 600`
- [ ] 测试 API 调用
- [ ] 更新 Marcus 脚本

---

## 🔍 测试 API

```bash
# 测试脚本
API_KEY=$(cat ~/.openclaw/workspace/config/finnhub_api_key.txt)
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=${API_KEY}"
```

**成功返回：**
```json
{"c":175.25,"h":176.50,"l":174.80,"o":175.00,"pc":174.90,"t":1710504000}
```

**失败返回：**
```json
{"error":"Invalid API key"}
```

---

## 💡 优化建议

### 1. 缓存数据
避免重复调用，缓存 5-15 分钟：
```bash
# 缓存目录
CACHE_DIR="$HOME/.cache/marcus"
mkdir -p "$CACHE_DIR"

# 检查缓存
if [ -f "$CACHE_DIR/AAPL.json" ]; then
    CACHE_TIME=$(stat -f%m "$CACHE_DIR/AAPL.json")
    NOW=$(date +%s)
    if [ $((NOW - CACHE_TIME)) -lt 300 ]; then
        cat "$CACHE_DIR/AAPL.json"
        return
    fi
fi

# 获取新数据并缓存
curl -s "..." > "$CACHE_DIR/AAPL.json"
```

### 2. 错误处理
```bash
# 检查 API 配额
curl -s "https://finnhub.io/api/v1/quote?symbol=AAPL&token=${API_KEY}" | \
grep -q "error" && echo "API 调用失败"
```

### 3. 日志记录
```bash
echo "$(date): API 调用 - AAPL" >> logs/finnhub_usage.log
```

---

## 📞 常见问题

### Q: API 调用失败？
A: 检查：
1. API Key 是否正确
2. 文件权限是否设置
3. 网络是否通畅
4. 是否超过配额限制

### Q: 数据延迟？
A: 免费计划有 15 分钟延迟，考虑升级到付费计划

### Q: 如何升级？
A: 访问 https://finnhub.io/pricing

---

*配置完成后，Marcus 将使用真实股票数据生成报告！*
