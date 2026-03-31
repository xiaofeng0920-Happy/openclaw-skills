#!/bin/bash
# Marcus - 发送日报到飞书
# 用法：./send_to_feishu.sh [--test]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_SCRIPT="$SCRIPT_DIR/generate_report.sh"
REPORT_DATE=$(date +"%Y-%m-%d")

echo "📤 发送 Marcus 日报到飞书..."

# 生成报告
echo "📊 生成今日报告..."
REPORT=$("$REPORT_SCRIPT" --force 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ 报告生成失败"
    exit 1
fi

echo "✅ 报告生成成功"

# 提取报告内容（去掉日志行）
REPORT_CONTENT=$(echo "$REPORT" | grep -A 1000 "━━━━━")

if [ -z "$REPORT_CONTENT" ]; then
    echo "❌ 报告内容为空"
    exit 1
fi

# 发送到飞书
# 方法 1: 使用 message 工具（推荐）
echo "📱 发送到飞书..."

# 创建临时文件
TEMP_REPORT=$(mktemp)
echo "$REPORT_CONTENT" > "$TEMP_REPORT"

# 使用 OpenClaw message 工具发送
# 注意：实际使用时需要通过 OpenClaw 的 message 工具
# 这里提供一个示例，实际发送由 OpenClaw 处理

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 预览报告内容："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$REPORT_CONTENT"
echo ""

# 清理
rm -f "$TEMP_REPORT"

echo "✅ 报告已准备发送"
echo ""
echo "📌 提示：在真实环境中，这会通过 OpenClaw message 工具发送到飞书群聊"
echo "   配置 cron 任务后，每个交易日自动发送"
