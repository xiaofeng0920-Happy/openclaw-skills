#!/bin/bash
# Comprehensive Test Suite for Finance Data Skill
# Tests all features: A-shares, HK stocks, Funds, indicators, news, history, announcements

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/tools"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
SKIP=0

log_pass() { echo -e "${GREEN}✓${NC} $1"; ((PASS++)); }
log_fail() { echo -e "${RED}✗${NC} $1"; ((FAIL++)); }
log_skip() { echo -e "${YELLOW}○${NC} $1"; ((SKIP++)); }
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }

echo "========================================"
echo "Finance Data Skill - Comprehensive Test"
echo "========================================"
echo "Test Date: $(date)"
echo ""

cd "$SCRIPT_DIR"

# ============================================
# Test Group 1: Search Function
# ============================================
echo "=== Test Group 1: Search Function ==="

log_info "Test 1.1: Search A-share (茅台)"
result=$(python3 "$TOOLS_DIR/search_stock.py" "茅台" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d['count']>0 and '600519' in str(d['results']) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share search (茅台→600519)" || log_fail "A-share search"

log_info "Test 1.2: Search HK stock (腾讯)"
result=$(python3 "$TOOLS_DIR/search_stock.py" "腾讯" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d['count']>0 and 'HK00700' in str(d['results']) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock search (腾讯→HK00700)" || log_fail "HK stock search"

log_info "Test 1.3: Search Fund (易方达)"
result=$(python3 "$TOOLS_DIR/search_stock.py" "易方达" fund 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d['count']>0 else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "Fund search (易方达)" || log_fail "Fund search"

echo ""

# ============================================
# Test Group 2: Get Stock Info
# ============================================
echo "=== Test Group 2: Get Stock Info ==="

log_info "Test 2.1: A-share info (600000)"
result=$(python3 "$TOOLS_DIR/get_stock_info.py" 600000 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) and d.get('source')=='mcp' else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share info (MCP source)" || log_fail "A-share info"

log_info "Test 2.2: HK stock info with profile (HK00700)"
result=$(python3 "$TOOLS_DIR/get_stock_info.py" HK00700 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) and 'company_name' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock info + company profile" || log_fail "HK stock info"

log_info "Test 2.3: Fund info (110011)"
result=$(python3 "$TOOLS_DIR/get_stock_info.py" 110011 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'nav' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "Fund info (NAV)" || log_fail "Fund info"

echo ""

# ============================================
# Test Group 3: Stock Price Query
# ============================================
echo "=== Test Group 3: Stock Price Query ==="

log_info "Test 3.1: A-share price (600000)"
result=$(python3 "$TOOLS_DIR/stock_query.py" 600000 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share price" || log_fail "A-share price"

log_info "Test 3.2: HK stock price (HK00700)"
result=$(python3 "$TOOLS_DIR/stock_query.py" HK00700 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock price" || log_fail "HK stock price"

echo ""

# ============================================
# Test Group 4: Financial Report
# ============================================
echo "=== Test Group 4: Financial Report ==="

log_info "Test 4.1: A-share financial (600519)"
result=$(python3 "$TOOLS_DIR/financial_report.py" 600519 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'pe_ratio' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share financial (PE ratio)" || log_fail "A-share financial"

log_info "Test 4.2: HK stock financial (HK00700)"
result=$(python3 "$TOOLS_DIR/financial_report.py" HK00700 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'pe_ratio' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock financial" || log_fail "HK stock financial"

echo ""

# ============================================
# Test Group 5: Fund Query
# ============================================
echo "=== Test Group 5: Fund Query ==="

log_info "Test 5.1: Fund NAV (110011)"
result=$(python3 "$TOOLS_DIR/fund_query.py" 110011 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'nav' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "Fund NAV" || log_fail "Fund NAV"

echo ""

# ============================================
# Test Group 6: Stock News
# ============================================
echo "=== Test Group 6: Stock News ==="

log_info "Test 6.1: A-share news (600000)"
result=$(python3 "$TOOLS_DIR/stock_news.py" 600000 3 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('data',{}).get('count',0)>=0 else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share news" || log_fail "A-share news"

log_info "Test 6.2: HK stock news (HK00700)"
result=$(python3 "$TOOLS_DIR/stock_news.py" HK00700 3 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if d.get('data',{}).get('count',0)>=0 else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock news" || log_fail "HK stock news"

echo ""

# ============================================
# Test Group 7: Query Indicators
# ============================================
echo "=== Test Group 7: Query Indicators ==="

log_info "Test 7.1: A-share indicators (price, PE)"
result=$(python3 "$TOOLS_DIR/query_indicator.py" 600000 price pe_ratio 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('indicators',{}) and 'pe_ratio' in d.get('indicators',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share multiple indicators" || log_fail "A-share indicators"

log_info "Test 7.2: HK stock indicators (price)"
result=$(python3 "$TOOLS_DIR/query_indicator.py" HK00700 price 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'indicators' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock indicators" || log_fail "HK stock indicators"

log_info "Test 7.3: HK stock unsupported indicator (MA5)"
result=$(python3 "$TOOLS_DIR/query_indicator.py" HK00700 ma5 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'error' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK unsupported indicator error handling" || log_fail "HK unsupported indicator"

log_info "Test 7.4: A-share technical indicator (MA5)"
result=$(python3 "$TOOLS_DIR/query_indicator.py" 600000 ma5 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'indicators' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share technical indicator" || log_fail "A-share technical"

echo ""

# ============================================
# Test Group 8: Historical Price
# ============================================
echo "=== Test Group 8: Historical Price ==="

log_info "Test 8.1: A-share history (600000, 10 days)"
result=$(python3 "$TOOLS_DIR/history_price.py" 600000 10 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'statistics' in d and 'period_high' in d.get('statistics',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share historical price" || log_fail "A-share history"

log_info "Test 8.2: A-share history (000001, 10 days)"
result=$(python3 "$TOOLS_DIR/history_price.py" 000001 10 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'data_points' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share history (平安银行)" || log_fail "A-share history 2"

log_info "Test 8.3: HK stock history (HK00700, 10 days)"
result=$(python3 "$TOOLS_DIR/history_price.py" HK00700 10 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'statistics' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "HK stock historical price" || log_fail "HK stock history"

echo ""

# ============================================
# Test Group 9: Company Announcements
# ============================================
echo "=== Test Group 9: Company Announcements ==="

log_info "Test 9.1: A-share announcements (600000)"
result=$(python3 "$TOOLS_DIR/stock_announcements.py" 600000 3 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'announcements' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "A-share announcements" || log_fail "A-share announcements"

echo ""

# ============================================
# Test Group 10: Query.sh Orchestrator
# ============================================
echo "=== Test Group 10: Query.sh Orchestrator ==="

log_info "Test 10.1: query.sh search"
result=$(bash "$TOOLS_DIR/query.sh" search "茅台" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'count' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh search" || log_fail "query.sh search"

log_info "Test 10.2: query.sh info"
result=$(bash "$TOOLS_DIR/query.sh" info 600000 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh info" || log_fail "query.sh info"

log_info "Test 10.3: query.sh stock"
result=$(bash "$TOOLS_DIR/query.sh" stock 600000 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'price' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh stock" || log_fail "query.sh stock"

log_info "Test 10.4: query.sh financial"
result=$(bash "$TOOLS_DIR/query.sh" financial 600519 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'pe_ratio' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh financial" || log_fail "query.sh financial"

log_info "Test 10.5: query.sh news"
result=$(bash "$TOOLS_DIR/query.sh" news 600000 3 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'news' in d.get('data',{}) else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh news" || log_fail "query.sh news"

log_info "Test 10.6: query.sh history"
result=$(bash "$TOOLS_DIR/query.sh" history 600000 10 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('PASS' if 'statistics' in d else 'FAIL')")
[ "$result" == "PASS" ] && log_pass "query.sh history (A-share)" || log_fail "query.sh history"

echo ""

# ============================================
# Summary
# ============================================
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo -e "${YELLOW}Skipped: $SKIP${NC}"
TOTAL=$((PASS + FAIL + SKIP))
echo "Total:  $TOTAL"
echo ""

if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
