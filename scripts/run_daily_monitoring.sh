#!/bin/bash
# 每日组合跟踪监控 - 每个交易日下午 5 点运行

# 加载环境变量
source ~/.zshrc 2>/dev/null || source ~/.bash_profile 2>/dev/null

# 执行监控脚本
cd /Users/zhaoxf/.openclaw/skills/港股量化投资
python3 scripts/daily_monitoring.py >> monitoring/daily_$(date +%Y%m%d).log 2>&1

echo "✅ 每日监控完成 - $(date)"
