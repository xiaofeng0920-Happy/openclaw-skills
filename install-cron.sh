#!/bin/bash
# 安装 Marcus 定时任务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="$SCRIPT_DIR/marcus.cron"

echo "🕐 安装 Marcus 定时任务..."
echo ""

# 检查 cron 文件
if [ ! -f "$CRON_FILE" ]; then
    echo "❌ 找不到 cron 文件：$CRON_FILE"
    exit 1
fi

# 显示将要安装的任务
echo "📋 将要安装的定时任务："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$CRON_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 安装
echo "⏳ 安装中..."
crontab "$CRON_FILE"

if [ $? -eq 0 ]; then
    echo "✅ 安装成功！"
    echo ""
    echo "📅 任务说明："
    echo "   - 时间：每个交易日（周一至周五）早上 9:00"
    echo "   - 任务：生成 Marcus 每日动量报告"
    echo "   - 日志：~/.openclaw/workspace/agents/xiaoba-stock-agent/logs/cron.log"
    echo ""
    echo "🔍 查看已安装的任务："
    echo "   crontab -l"
    echo ""
    echo "📝 查看日志："
    echo "   tail -f ~/.openclaw/workspace/agents/xiaoba-stock-agent/logs/cron.log"
    echo ""
    echo "🗑️  卸载任务："
    echo "   crontab -r"
else
    echo "❌ 安装失败"
    exit 1
fi
