---
name: 港股量化投资
description: 港股量化投资系统 - 量价因子选股 + 组合优化 + 自动监控。支持市值筛选、多因子评分、组合权重优化、模拟/实盘交易、定期监控。使用富途 OpenD 数据源。
allowed-tools: Bash Read Write Edit Exec
---

# 港股/A 股量化投资系统

**版本**: v1.2  
**日期**: 2026-03-26  
**数据源**: 富途 OpenD（支持港股+A 股）  
**策略**: 
- 动量 + 价值（量价 60% + 价值 40%）
- 动量 + 价值 + 质量（量价 40% + 价值 30% + 质量 30%）

---

## 🎯 功能

- ✅ 量化选股（港股>40 亿/A 股>100 亿，量价因子 60% + 价值因子 40%）
- ✅ 组合优化（Top 15，估值调整权重）
- ✅ 模拟交易（富途模拟盘）
- ✅ 实盘交易（小资金测试）
- ✅ 定期监控（每周自动跟踪）
- ✅ 自动报告（Markdown + CSV + JSON）

---

## 📁 文件结构

```
~/.openclaw/skills/港股量化投资/
├── SKILL.md                    # 本文件
├── scripts/
│   ├── quant_stock_selector.py # 量化选股
│   ├── portfolio_optimizer.py  # 组合优化
│   ├── simulation_trading.py   # 模拟交易
│   ├── real_trading.py         # 实盘交易
│   ├── portfolio_monitor.py    # 组合监控
│   └── run_monitoring.sh       # 监控脚本
├── config/
│   └── quant_config.json       # 配置文件
├── docs/
│   ├── 使用指南.md
│   └── 策略说明.md
└── reports/                    # 输出报告
    ├── stock_selection_*.csv   # 选股结果
    ├── portfolio_*.csv         # 组合权重
    ├── simulation_orders_*.json # 模拟订单
    ├── real_orders_*.json      # 实盘订单
    └── monitoring_*.md         # 监控报告
```

---

## 🚀 快速开始

### 1. 运行量化选股

```bash
cd ~/.openclaw/skills/港股量化投资
python3 scripts/quant_stock_selector.py --market HK --top 20
```

### 2. 组合优化

```bash
python3 scripts/portfolio_optimizer.py \
  --input reports/stock_selection_HK_20260326.csv \
  --top 15
```

### 3. 模拟盘测试

```bash
python3 scripts/simulation_trading.py
```

### 4. 实盘交易

```bash
python3 scripts/real_trading.py
```

### 5. 组合监控

```bash
python3 scripts/portfolio_monitor.py
```

---

## 📊 选股策略

### 因子权重

| 因子 | 权重 | 子因子 |
|------|------|--------|
| **量价因子** | 60% | 20 日涨幅 50% + RSI 30% + 成交量 20% |
| **价值因子** | 40% | PE 50% + PB 30% + 股息率 20% |

### 筛选条件

- 市值：> 40 亿港元
- PE：< 30
- 价格：1-1000 港元
- 成交量：> 50 万

---

## 📅 定时任务

### 配置 crontab

```bash
crontab -e

# 每个交易日 9:00 AM - 自动选股
0 9 * * 1-5 cd ~/.openclaw/skills/港股量化投资 && python3 quant_orchestrator.py

# 每周五 5:00 PM - 组合监控
0 17 * * 5 cd ~/.openclaw/skills/港股量化投资 && python3 scripts/portfolio_monitor.py
```

---

## 📁 输出文件

### 选股结果

**文件**: `reports/stock_selection_HK_YYYYMMDD.csv`

**字段**:
- code, name, last_price, pe_ratio, pb_ratio
- change_20d, rsi_14, volume_ratio
- total_score, value_score, momentum_score

### 组合权重

**文件**: `reports/portfolio_HK_YYYYMMDD.csv`

**字段**:
- code, name, weight, entry_price
- stop_loss, take_profit

### 监控报告

**文件**: `reports/monitoring_YYYYMMDD.md`

**内容**:
- 组合总体表现
- 个股盈亏
- 止损/止盈预警
- 操作建议

---

## ⚙️ 配置选项

### 修改因子权重

编辑 `config/quant_config.json`:

```json
{
  "scoring": {
    "value_weight": 0.4,
    "momentum_weight": 0.6
  }
}
```

### 修改筛选条件

```json
{
  "filters": {
    "min_market_cap": 50,
    "max_pe": 25,
    "min_price": 2
  }
}
```

---

## ⚠️ 风险提示

1. **历史数据不代表未来表现**
2. **量价因子可能失效**
3. **港股流动性风险**
4. **建议先用模拟盘测试 3 个月**

---

## 📞 故障排除

### OpenD 未连接

```bash
# 检查 OpenD 状态
openclaw gateway status

# 重启 OpenD
openclaw gateway restart
```

### 交易未解锁

在 OpenD GUI 界面点击「解锁交易」，输入交易密码。

---

## 📝 更新日志

### v1.0 (2026-03-26)

- ✅ 量化选股（量价 60% + 价值 40%）
- ✅ 组合优化
- ✅ 模拟/实盘交易
- ✅ 定期监控

---

*最后更新：2026-03-26 15:30*
