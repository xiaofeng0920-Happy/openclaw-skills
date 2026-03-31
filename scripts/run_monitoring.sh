#!/bin/bash
# 量化组合监控 - 每周五下午 5 点运行

# 加载环境变量
source ~/.zshrc 2>/dev/null || source ~/.bash_profile 2>/dev/null

# 执行监控脚本
cd /Users/zhaoxf/.openclaw/workspace/agents/stock-system
python3 scripts/portfolio_monitor.py >> logs/monitoring_$(date +%Y%m%d).log 2>&1

echo "✅ 组合监控完成 - $(date)"
