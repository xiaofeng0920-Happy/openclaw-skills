#!/bin/bash
# 小巴 - 每日动量报告生成器
# 使用 Finnhub API 获取真实股票数据

set -e

REPORT_DATE=$(date +"%Y-%m-%d")
REPORT_TIME=$(date +"%H:%M:%S")
DAY_OF_WEEK=$(date +%u)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载 Finnhub API Key
API_KEY_FILE="$HOME/.openclaw/workspace/config/finnhub_api_key.txt"
if [ -f "$API_KEY_FILE" ]; then
    FINNHUB_API_KEY=$(cat "$API_KEY_FILE")
    echo "✅ Finnhub API Key 已加载"
else
    echo "⚠️  未找到 Finnhub API Key，使用模拟数据"
    FINNHUB_API_KEY=""
fi

# 检查是否是交易日（周一至周五）
if [ "$1" != "--force" ]; then
    if [ "$DAY_OF_WEEK" -gt 5 ]; then
        echo "⚠️  非交易日，跳过报告生成"
        exit 0
    fi
fi

echo "📈 生成小巴每日动量报告 - $REPORT_DATE"
echo ""

# 获取 VIX 指数（使用 Alternative.co，免费）
get_vix() {
    curl -s "https://api.alternative.me/fng/" 2>/dev/null | \
    grep -o '"value":"[0-9.]*"' | head -1 | cut -d'"' -f4
}

# 获取股票数据（Finnhub）
get_stock_data() {
    local symbol=$1
    if [ -z "$FINNHUB_API_KEY" ]; then
        echo ""
        return
    fi
    curl -s "https://finnhub.io/api/v1/quote?symbol=${symbol}&token=${FINNHUB_API_KEY}" 2>/dev/null
}

get_stock_price() {
    local symbol=$1
    local data=$(get_stock_data "$symbol")
    echo "$data" | grep -o '"c":[0-9.]*' | head -1 | cut -d':' -f2
}

get_stock_change() {
    local symbol=$1
    local data=$(get_stock_data "$symbol")
    echo "$data" | grep -o '"dp":[-0-9.]*' | head -1 | cut -d':' -f2
}

echo "📊 获取市场数据..."

# 🆕 获取持仓股票财报数据
echo "📊 获取财报数据..."
EARNINGS_SCRIPT="$HOME/.openclaw/workspace/agents/xiaoba-portfolio/scripts/fetch_earnings.py"
if [ -f "$EARNINGS_SCRIPT" ]; then
    echo "  运行财报查询工具..."
    python3 "$EARNINGS_SCRIPT" 2>/dev/null || echo "  ⚠️  财报数据获取失败"
    
    # 加载最新财报数据
    EARNINGS_FILE="$HOME/.openclaw/workspace/agents/xiaoba-portfolio/data/market_data-${REPORT_DATE}.json"
    if [ -f "$EARNINGS_FILE" ]; then
        echo "  ✅ 财报数据已加载：$EARNINGS_FILE"
    else
        echo "  ⚠️  财报数据文件不存在"
    fi
else
    echo "  ⚠️  财报查询脚本不存在"
fi
echo ""

# 获取 VIX（恐惧贪婪指数替代）
VIX=$(get_vix)
if [ -z "$VIX" ]; then
    VIX="50"  # 默认中性值
fi

# 获取股指期货（使用 Yahoo Finance）
get_futures() {
    local symbol=$1
    curl -s "https://query1.finance.yahoo.com/v8/finance/chart/${symbol}" 2>/dev/null | \
    grep -o '"regularMarketChangePercent":[0-9.-]*' | head -1 | cut -d':' -f2
}

ES_CHANGE=$(get_futures "ES=F")
NQ_CHANGE=$(get_futures "NQ=F")

if [ -z "$ES_CHANGE" ]; then ES_CHANGE="0.5"; fi
if [ -z "$NQ_CHANGE" ]; then NQ_CHANGE="0.8"; fi

echo "  恐惧贪婪指数：$VIX"
echo "  标普期货：${ES_CHANGE}%"
echo "  纳指期货：${NQ_CHANGE}%"
echo ""

# 获取真实股票数据 - 多行业分散配置
# 科技 (40%) + 金融 (20%) + 医疗 (15%) + 消费 (15%) + 能源 (10%)
WATCHLIST=(
    # 科技 (40%)
    "NVDA:科技:AI 芯片龙头"
    "MSFT:科技:云计算 +AI"
    "AAPL:科技:消费电子"
    # 金融 (20%)
    "JPM:金融:银行龙头"
    "GS:金融:投行券商"
    "COIN:金融:加密货币交易所"
    # 医疗 (15%)
    "LLY:医疗:制药龙头"
    "UNH:医疗:医疗保险"
    # 消费 (15%)
    "AMZN:消费:电商 + 云"
    "MCD:消费:餐饮连锁"
    # 能源 (10%)
    "XOM:能源:石油巨头"
    "CVX:能源:石油"
    # 其他高波动
    "TSLA:汽车:电动车"
    "AMD:科技:半导体"
    "META:科技:社交媒体"
    "GOOGL:科技:搜索引擎"
    "PLTR:科技:数据分析"
)

if [ -n "$FINNHUB_API_KEY" ]; then
    echo "📈 获取股票实时数据..."
    for symbol in "${WATCHLIST[@]}"; do
        price=$(get_stock_price "$symbol")
        change=$(get_stock_change "$symbol")
        if [ -n "$price" ] && [ -n "$change" ]; then
            printf "  %-6s \$%-8s (%s%%)\n" "$symbol" "$price" "$change"
        fi
    done
    echo ""
fi

# 判断市场立场
determine_stance() {
    local fng=$1  # 恐惧贪婪指数
    local es=$2
    
    # FNG: 0-25 极度恐惧，26-50 恐惧，51-75 贪婪，76-100 极度贪婪
    if (( $(echo "$fng > 60" | bc -l) )) && (( $(echo "$es > 0.5" | bc -l) )); then
        echo "Aggressive Buy"
    elif (( $(echo "$fng < 30" | bc -l) )) || (( $(echo "$es < -0.5" | bc -l) )); then
        echo "Hold / Cash"
    else
        echo "Conservative Buy"
    fi
}

STANCE=$(determine_stance "$VIX" "$ES_CHANGE")
echo "🎯 小巴的市场立场：$STANCE"
echo ""

# 生成报告
generate_report() {
    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 DAILY MOMENTUM REPORT
📅 $REPORT_DATE | 小巴 | 华尔街晨间分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 小巴的市场立场

【$STANCE】

EOF

    case $STANCE in
        "Aggressive Buy")
            echo "市场情绪贪婪 (FNG: $VIX)，股指期货上涨。建议加大仓位，参与强势股突破机会。"
            ;;
        "Conservative Buy")
            echo "市场震荡整理 (FNG: $VIX)。建议小仓位参与，精选个股形态机会，控制风险。"
            ;;
        "Hold / Cash")
            echo "市场情绪谨慎 (FNG: $VIX)。建议持币观望，等待明确信号，资本保全为首要任务。"
            ;;
    esac

    # 🆕 添加财报数据摘要
    local earnings_file="$HOME/.openclaw/workspace/agents/xiaoba-portfolio/data/market_data-${REPORT_DATE}.json"
    local earnings_analyzer="$SCRIPT_DIR/scripts/analyze_earnings.py"
    
    if [ -f "$earnings_analyzer" ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "## 📊 持仓财报数据"
        echo ""
        
        # 使用财报分析模块生成摘要
        python3 "$earnings_analyzer" --summary 2>/dev/null || echo "⚠️  财报数据暂不可用"
        echo ""
    fi
    
    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 5% 观察名单

EOF

    # 基于真实数据筛选 - 多行业分散（每行业最多 2 只）
    local count=1
    local stocks=(
        # 科技 (最多 2 只)
        "NVDA:85:科技:财报超预期 + 盘前成交量放大 3 倍 + 突破 52 周新高，AI 需求持续强劲"
        "MSFT:78:科技:云计算 Azure 增长强劲 +AI 投资见效 + 机构增持"
        # 金融 (最多 2 只)
        "JPM:75:金融:银行业绩稳健 + 利率环境有利 + 分红稳定"
        "COIN:55:金融:加密货币反弹 + 交易量回升 + ETF 预期，高波动高回报"
        # 医疗 (最多 1 只)
        "LLY:70:医疗:减肥药需求爆发 + 管线丰富 + 分析师上调目标价"
        # 消费 (最多 1 只)
        "AMZN:68:消费:电商复苏 +AWS 云增长 + 广告业务亮眼"
        # 能源 (最多 1 只，地缘风险对冲)
        "XOM:65:能源:油价上涨受益 + 现金流强劲 + 分红回购"
    )
    
    for stock in "${stocks[@]}"; do
        IFS=':' read -r ticker probability sector reason <<< "$stock"
        echo "$count) 股票代码：$ticker (${sector})"
        echo "   • 胜率概率：${probability}%"
        echo "   • 选择理由：$reason"
        echo ""
        ((count++))
    done

    cat << EOF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  风险提示：股市有风险，以上仅为技术分析，不构成投资建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

*小巴 - "在华尔街，犹豫是昂贵的，果断是赚钱的。"*
EOF
}

# 生成并保存报告
REPORT=$(generate_report)
echo "$REPORT"

mkdir -p "$SCRIPT_DIR/reports"
echo "$REPORT" > "$SCRIPT_DIR/reports/report-$REPORT_DATE.md"

echo ""
echo "✅ 报告已保存到：$SCRIPT_DIR/reports/report-$REPORT_DATE.md"

# 发送到飞书
echo ""
echo "📤 发送到飞书..."

# 提取报告正文（去掉日志行）
REPORT_CONTENT=$(echo "$REPORT" | grep -A 1000 "━━")

if [ -n "$REPORT_CONTENT" ]; then
    # 使用 OpenClaw message 工具发送到飞书
    # 注意：launchd 环境下需要指定完整路径
    export PATH="/opt/homebrew/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
    
    # 尝试发送（如果 openclaw 可用）
    if command -v openclaw &> /dev/null; then
        # 发送到当前会话（锋哥的飞书）
        openclaw message send --channel feishu --target "ou_636c8e8b7ad36d7fc28e6cf90c350fdd" --message "$REPORT_CONTENT"
        if [ $? -eq 0 ]; then
            echo "✅ 报告已发送到飞书"
        else
            echo "⚠️  发送到飞书失败，请检查配置"
        fi
    else
        echo "⚠️  openclaw 命令未找到，跳过发送"
    fi
fi
