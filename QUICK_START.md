# 🚀 Marcus 股票日报 - 快速配置

## 3 步配置 Finnhub 数据源

### 步骤 1: 获取 Finnhub API Key

1. 访问：https://finnhub.io/dashboard
2. 如果没有账号，先注册（免费）
3. 复制你的 API Key（一串字母数字）

### 步骤 2: 保存 API Key

```bash
# 创建配置目录
mkdir -p ~/.openclaw/workspace/config

# 保存 API Key（替换 YOUR_API_KEY 为你的真实 Key）
echo "YOUR_API_KEY" > ~/.openclaw/workspace/config/finnhub_api_key.txt

# 设置权限（安全）
chmod 600 ~/.openclaw/workspace/config/finnhub_api_key.txt
```

### 步骤 3: 测试

```bash
cd ~/.openclaw/workspace/agents/marcus-stock-agent
./generate_report.sh --force
```

---

## 📊 配置后的效果

**未配置 API Key：**
- 使用模拟数据
- VIX 和期货使用 Yahoo Finance
- 股票数据为示例

**配置 API Key 后：**
- ✅ 使用 Finnhub 实时数据
- ✅ 获取真实股价和涨跌幅
- ✅ 数据更准确、延迟更低

---

## 🔍 验证配置

```bash
# 检查 API Key 文件
cat ~/.openclaw/workspace/config/finnhub_api_key.txt

# 测试 API 调用
API_KEY=$(cat ~/.openclaw/workspace/config/finnhub_api_key.txt)
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=${API_KEY}"
```

**成功返回：**
```json
{"c":175.25,"h":176.50,"l":174.80,"o":175.00,"pc":174.90,"t":1710504000}
```

---

## 📝 注意事项

1. **API Key 安全**
   - 不要分享到公开平台
   - 文件权限设置为 600
   - 不要提交到 Git

2. **配额限制**
   - 免费计划：60 次/分钟
   - Marcus 日报每次运行约消耗 10-15 次
   - 完全够用！

3. **数据延迟**
   - 免费计划有 15 分钟延迟
   - 对于日报来说足够

---

## 🆘 遇到问题？

### API 调用失败
```bash
# 检查 API Key 是否正确
cat ~/.openclaw/workspace/config/finnhub_api_key.txt

# 测试网络连接
curl https://finnhub.io
```

### 权限错误
```bash
chmod 600 ~/.openclaw/workspace/config/finnhub_api_key.txt
```

### 查看详细日志
```bash
tail -f ~/.openclaw/workspace/agents/marcus-stock-agent/logs/cron.log
```

---

*配置完成后，Marcus 将使用真实股票数据为你生成报告！*
