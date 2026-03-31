#!/bin/bash
# 小巴定时任务安装脚本

echo "⏰ 安装小巴股票日报定时任务..."
echo ""

# 显示要安装的任务
echo "📋 将要安装的任务："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "0 8 * * 1-5 每天早上 8:00 (周一到周五)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建临时文件
CRON_CONTENT="0 8 * * 1-5 $HOME/.openclaw/workspace/agents/xiaoba-stock-agent/generate_report.sh --force >> $HOME/.openclaw/workspace/agents/xiaoba-stock-agent/logs/cron.log 2>&1"

echo "$CRON_CONTENT" > /tmp/xiaoba_cron_$$.txt

# 安装
echo "⏳ 安装中..."
crontab /tmp/xiaoba_cron_$$.txt

if [ $? -eq 0 ]; then
    echo "✅ 安装成功！"
    echo ""
    echo "📅 任务说明："
    echo "   - 时间：每个交易日（周一至周五）早上 8:00"
    echo "   - 任务：生成小巴每日动量报告"
    echo "   - 日志：$HOME/.openclaw/workspace/agents/xiaoba-stock-agent/logs/cron.log"
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
    echo ""
    echo "请手动运行以下命令："
    echo ""
    echo "crontab ~/.openclaw/workspace/agents/xiaoba-stock-agent/xiaoba.cron"
fi

# 清理
rm -f /tmp/xiaoba_cron_$$.txt
