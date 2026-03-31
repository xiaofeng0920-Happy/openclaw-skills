#!/usr/bin/env bash
# Finance Data Query Orchestrator

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TYPE="${1:-}"
SYMBOL="${2:-}"
EXTRA="${3:-}"

usage() {
  cat <<USAGE
Usage: $0 <type> <symbol> [extra]

Types:
  search         - Search stock/fund by name
  info           - Get stock info (price + key indicators)
  stock          - Stock price (A/HK)
  financial      - Financial report
  fund           - Fund NAV
  news           - Stock news (A/HK)
  indicator      - Query specific indicators
  history        - Historical price data
  announcements  - Company announcements
  market-news    - Market news summary (economic & policy) ⭐ NEW
  economic       - Macroeconomic data (GDP, CPI, PMI, etc.) ⭐ NEW

Examples:
  $0 search 茅台
  $0 info 600000
  $0 stock 600000
  $0 financial 600519
  $0 fund 110011
  $0 news 600000 5
  $0 indicator 600000 price pe
  $0 history 600000 30
  $0 announcements 600000 3
  $0 market-news                    # Economic news (20 items)
  $0 market-news --policy           # Policy news (CCTV)
  $0 market-news 30                 # Economic news (30 items)
  $0 economic gdp                   # GDP data
  $0 economic cpi                   # CPI data
  $0 economic all                   # All macro data summary
USAGE
  exit 1
}

[[ -z "$TYPE" ]] && usage

case "$TYPE" in
  search)
    search_type="${EXTRA:-all}"
    market="${4:-all}"
    python3 "$SCRIPT_DIR/search_stock.py" "$SYMBOL" "$search_type" "$market"
    ;;
  
  info)
    python3 "$SCRIPT_DIR/get_stock_info.py" "$SYMBOL"
    ;;
  
  stock)
    if [[ "$SYMBOL" =~ ^(6|0|3)[0-9]{5}$ ]]; then
      result=$(python3 "$SCRIPT_DIR/mcp_query.py" "$SYMBOL" brief 2>/dev/null) || result=""
      if [[ -n "$result" && "$result" != *"error"* ]]; then
        echo "$result"
        exit 0
      fi
    fi
    python3 "$SCRIPT_DIR/stock_query.py" "$SYMBOL"
    ;;
  
  financial)
    python3 "$SCRIPT_DIR/financial_report.py" "$SYMBOL"
    ;;
  
  fund)
    python3 "$SCRIPT_DIR/fund_query.py" "$SYMBOL"
    ;;
  
  news)
    limit="${EXTRA:-10}"
    python3 "$SCRIPT_DIR/stock_news.py" "$SYMBOL" "$limit"
    ;;
  
  indicator)
    shift 2
    python3 "$SCRIPT_DIR/query_indicator.py" "$SYMBOL" "$@"
    ;;
  
  history)
    days="${EXTRA:-30}"
    python3 "$SCRIPT_DIR/history_price.py" "$SYMBOL" "$days"
    ;;
  
  announcements)
    days="${EXTRA:-3}"
    important="${4:-false}"
    python3 "$SCRIPT_DIR/stock_announcements.py" "$SYMBOL" "$days" "$important"
    ;;
  
  market-news)
    # Handle market-news command
    # Usage: market-news [--policy] [limit]
    if [[ "$SYMBOL" == "--policy" ]]; then
      mode="--policy"
      limit="${EXTRA:-20}"
    elif [[ "$SYMBOL" =~ ^[0-9]+$ ]]; then
      mode=""
      limit="$SYMBOL"
    else
      mode=""
      limit="${SYMBOL:-20}"
    fi
    if [[ "$mode" == "--policy" ]]; then
      python3 "$SCRIPT_DIR/market_news.py" --policy --limit "$limit"
    else
      python3 "$SCRIPT_DIR/market_news.py" --limit "$limit"
    fi
    ;;
  
  economic)
    # Handle economic data command
    # Usage: economic <indicator>
    # Indicators: gdp, cpi, pmi, rate, m2, rrr, bond, all
    indicator="${SYMBOL:-all}"
    python3 "$SCRIPT_DIR/economic_data.py" "$indicator"
    ;;
  
  *)
    echo "Unknown type: $TYPE" >&2
    usage
    ;;
esac
