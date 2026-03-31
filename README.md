# ✅ 港股量化投资技能 - 保存完成

**保存时间**: 2026-03-26 15:31  
**技能位置**: `~/.openclaw/skills/港股量化投资/`

---

## 📁 文件结构

```
~/.openclaw/skills/港股量化投资/
├── SKILL.md                          # 技能说明 ⭐
├── config/
│   └── quant_config.json             # 配置文件
├── docs/
│   ├── 使用指南.md                   # 快速入门 ⭐
│   └── 策略说明.md                   # 策略详解 ⭐
├── scripts/
│   ├── quant_stock_selector.py       # 量化选股 (9.1KB)
│   ├── portfolio_optimizer.py        # 组合优化 (4.9KB)
│   ├── simulation_trading.py         # 模拟交易 (5.3KB)
│   ├── real_trading.py               # 实盘交易 (7.1KB)
│   ├── portfolio_monitor.py          # 组合监控 (9.1KB)
│   └── run_monitoring.sh             # 监控脚本 (352B)
└── reports/                          # 输出报告（运行时生成）
```

**总计**: 6 个脚本 + 3 个文档 + 1 个配置

---

## 🚀 快速开始

### 1. 量化选股

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

### 3. 模拟盘

```bash
python3 scripts/simulation_trading.py
```

### 4. 实盘

```bash
python3 scripts/real_trading.py
```

### 5. 监控

```bash
python3 scripts/portfolio_monitor.py
```

---

## 📊 策略核心

### 因子权重

| 因子 | 权重 | 说明 |
|------|------|------|
| **量价因子** | 60% | 20 日涨幅 + RSI + 成交量 |
| **价值因子** | 40% | PE + PB + 股息率 |

### 筛选条件

- 市值：> 40 亿港元
- PE：< 30
- 价格：1-1000 港元
- 成交量：> 50 万

---

## 📁 文档说明

### SKILL.md

技能主文档，包含：
- 功能介绍
- 文件结构
- 快速开始
- 配置选项
- 故障排除

### docs/使用指南.md

详细使用教程，包含：
- 安装说明
- 每个功能的详细用法
- 输出文件说明
- 定时任务配置
- 最佳实践

### docs/策略说明.md

策略详解，包含：
- 因子构建逻辑
- 评分规则
- 组合优化方法
- 风险控制
- 预期收益

---

## 📅 定时任务

已配置 crontab（工作区版本）：

```bash
# 每个交易日 9:00 AM - 自动选股
0 9 * * 1-5 cd /Users/zhaoxf/.openclaw/workspace/agents/stock-system && python3 quant_orchestrator.py

# 每周五 5:00 PM - 组合监控
0 17 * * 5 cd /Users/zhaoxf/.openclaw/workspace/agents/stock-system && python3 scripts/portfolio_monitor.py
```

**技能版本定时任务**（需手动配置）：

```bash
crontab -e

# 添加：
0 9 * * 1-5 cd ~/.openclaw/skills/港股量化投资 && python3 quant_orchestrator.py
0 17 * * 5 cd ~/.openclaw/skills/港股量化投资 && python3 scripts/portfolio_monitor.py
```

---

## 📊 今日成果

### 选股结果

- **选股数量**: 395 只（市值>40 亿）
- **Top 1**: 中升控股 (00881.HK) - 评分 42.78
- **平均 PE**: 7.16（低估 43%）
- **破净股**: 67%

### 推荐组合

- **股票数量**: Top 15
- **平均 PE**: 7.16
- **平均 PB**: 0.74
- **行业分布**: 保险 41% + 公用事业 15% + 其他 44%

### 模拟盘

- **总资金**: 100 万 HKD
- **订单数量**: 15 只
- **输出**: `reports/simulation_orders_20260326.json`

---

## 🎯 下一步建议

### 观察期（1-2 周）

1. ✅ **每日选股** - 观察选股稳定性
2. ✅ **模拟盘跟踪** - 记录模拟盘表现
3. ✅ **监控报告** - 每周五查看监控报告

### 测试期（1-3 个月）

4. ⏳ **小资金实盘** - 10 万 HKD 开始
5. ⏳ **业绩跟踪** - 每周对比恒指
6. ⏳ **策略优化** - 根据表现调整参数

### 正式期（3 个月后）

7. ⏳ **扩大资金** - 根据表现增加投入
8. ⏳ **自动化** - 完全依赖定时任务
9. ⏳ **策略迭代** - 加入新因子

---

## 📞 使用方式

### 方式 1: 直接使用脚本

```bash
cd ~/.openclaw/skills/港股量化投资
python3 scripts/quant_stock_selector.py --help
```

### 方式 2: 通过 OpenClaw 调用

```
/港股量化投资 选股
/港股量化投资 优化
/港股量化投资 监控
```

---

## ⚠️ 重要提示

1. **先模拟后实盘** - 建议模拟盘测试 3 个月
2. **小资金测试** - 实盘从 10 万开始
3. **严格止损** - -10% 坚决止损
4. **长期视角** - 至少持有 1 年
5. **定期再平衡** - 每季度调整权重

---

## 📝 更新日志

### v1.0 (2026-03-26)

- ✅ 量化选股（量价 60% + 价值 40%）
- ✅ 组合优化（Top 15，估值调整）
- ✅ 模拟交易（100 万 HKD）
- ✅ 实盘交易（10 万 HKD 测试）
- ✅ 组合监控（每周自动）
- ✅ 定时任务（选股 + 监控）
- ✅ 完整文档（使用指南 + 策略说明）

---

*技能保存完成时间：2026-03-26 15:31*  
*小巴量化投资系统 v1.0*
