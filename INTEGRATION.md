# 📊 财报数据集成文档

## 更新内容

已将财报查询功能集成到 **小巴华尔街股票日报 Agent** (xiaoba-stock-agent)

## 集成模块

### 1. 财报查询工具
**位置**: `~/.openclaw/workspace/agents/xiaoba-portfolio/scripts/fetch_earnings.py`

**功能**:
- 查询持仓股票最新财报
- 获取营收、净利润、EPS 及同比
- 记录是否超预期
- 输出到 `market_data_*.json`

**用法**:
```bash
# 批量查询所有持仓
python3 fetch_earnings.py

# 查询单只股票
python3 fetch_earnings.py --ticker NVDA

# 查看现有数据
python3 fetch_earnings.py --show
```

### 2. 财报分析模块
**位置**: `~/.openclaw/workspace/agents/xiaoba-stock-agent/scripts/analyze_earnings.py`

**功能**:
- 加载财报数据
- 生成摘要报告
- 超预期/低于预期统计
- 投资启示建议

**用法**:
```bash
# 生成摘要报告
python3 analyze_earnings.py --summary

# 查询单只股票
python3 analyze_earnings.py --ticker NVDA

# JSON 格式输出
python3 analyze_earnings.py --ticker MSFT --json
```

### 3. 日报生成集成
**位置**: `~/.openclaw/workspace/agents/xiaoba-stock-agent/generate_report.sh`

**更新内容**:
1. 在报告生成前自动获取财报数据
2. 在日报中添加"持仓财报数据"章节
3. 显示超预期股票亮点

**报告流程**:
```bash
1. 获取市场数据 (VIX, 期货)
2. 🆕 获取持仓财报数据
3. 确定市场立场
4. 生成观察名单
5. 🆕 添加财报数据摘要
6. 输出完整报告
```

## 报告示例

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 DAILY MOMENTUM REPORT
📅 2026-03-19 | 小巴 | 华尔街晨间分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 小巴的市场立场

【Conservative Buy】

市场震荡整理 (FNG: 45)。建议小仓位参与，精选个股形态机会，控制风险。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 持仓财报数据

**财报概览**:
- 总计：15 只股票
- ✅ 超预期：8 只 (53.3%)
- ❌ 低于预期：3 只 (20.0%)
- ➖ 符合预期：4 只

**超预期亮点**:
- **NVDA**: EPS $1.52 (+3.6%)
- **GOOGL**: EPS $1.48 (+4.2%)
- **AAPL**: EPS $2.18 (+4.2%)

**投资启示**:
- ✅ 财报季整体乐观，多数公司超预期
- 建议：积极参与，重点关注超预期股票的后续表现

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 5% 观察名单

1) 股票代码：NVDA (科技)
   • 胜率概率：85%
   • 选择理由：财报超预期 + 盘前成交量放大 3 倍 + 突破 52 周新高
...
```

## 数据流

```
持仓配置 (feng_portfolio.json)
    ↓
财报查询 (fetch_earnings.py)
    ↓
market_data_YYYY-MM-DD.json
    ↓
财报分析 (analyze_earnings.py)
    ↓
日报生成 (generate_report.sh)
    ↓
飞书推送 (send_to_feishu.sh)
```

## 定时任务配置

### 财报查询（每个交易日 7:30）
```bash
# 编辑 crontab
crontab -e

# 添加任务
30 7 * * 1-5 python3 ~/.openclaw/workspace/agents/xiaoba-portfolio/scripts/fetch_earnings.py
```

### 日报生成（每个交易日 9:00）
```bash
0 9 * * 1-5 ~/.openclaw/workspace/agents/xiaoba-stock-agent/send_to_feishu.sh
```

## 文件结构

```
xiaoba-stock-agent/
├── generate_report.sh          # 主脚本（已集成财报）
├── send_to_feishu.sh          # 飞书推送
├── scripts/
│   └── analyze_earnings.py    # 🆕 财报分析模块
└── reports/
    └── report-YYYY-MM-DD.md   # 生成的报告

xiaoba-portfolio/
├── scripts/
│   └── fetch_earnings.py      # 🆕 财报查询工具
└── data/
    └── market_data_*.json     # 🆕 财报数据
```

## API 配置

**Finnhub API Key**: `~/.openclaw/workspace/config/finnhub_api_key.txt`

**配额限制**: 60 次/分钟（免费计划）

**数据覆盖**:
- 美股：实时财报数据
- 港股：延迟财报数据

## 测试验证

### 1. 测试财报查询
```bash
cd ~/.openclaw/workspace/agents/xiaoba-portfolio/scripts
python3 fetch_earnings.py --ticker NVDA
```

### 2. 测试财报分析
```bash
cd ~/.openclaw/workspace/agents/xiaoba-stock-agent/scripts
python3 analyze_earnings.py --summary
```

### 3. 测试完整报告
```bash
cd ~/.openclaw/workspace/agents/xiaoba-stock-agent
./generate_report.sh --force
```

### 4. 查看生成的报告
```bash
cat reports/report-$(date +%Y-%m-%d).md
```

## 故障排查

### 财报数据为空
```
⚠️  暂无财报数据
```
**解决**: 运行 `fetch_earnings.py` 获取最新数据

### API Key 未配置
```
❌ Finnhub API Key 未配置
```
**解决**: 创建 `~/.openclaw/workspace/config/finnhub_api_key.txt`

### 脚本权限问题
```
Permission denied
```
**解决**: `chmod +x scripts/*.py`

## 下一步优化

- [ ] 添加财报日历提醒
- [ ] 集成财报电话会议记录分析
- [ ] 添加分析师评级变化
- [ ] 财报后股价表现追踪
- [ ] 自动生成财报季总结报告

---

*更新时间：2026-03-19*
*集成者：小巴 (◍•ᴗ•◍)*
