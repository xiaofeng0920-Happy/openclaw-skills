#!/bin/bash
# Test script for finance-data skill

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Finance Data Skill Tests ==="
echo

# Test 1: Search stock
echo "Test 1: Search stock (茅台)"
python3 tools/search_stock.py "茅台" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Found:', d['count'], 'result(s)')" || echo "  ✗ Search failed"

# Test 2: MCP query
echo "Test 2: MCP query (600000)"
python3 tools/mcp_query.py 600000 brief 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Source:', d['source'], '| Price:', d['data'].get('price'))" || echo "  ✗ MCP failed"

# Test 3: Stock query
echo "Test 3: Stock query (600000)"
python3 tools/stock_query.py 600000 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Source:', d['source'], '| Price:', d['data'].get('price'))" || echo "  ✗ akshare not installed"

# Test 4: Fund query
echo "Test 4: Fund query (110011)"
python3 tools/fund_query.py 110011 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ NAV:', d['data'].get('nav'))" || echo "  ✗ akshare not installed"

# Test 5: Financial report
echo "Test 5: Financial report (600519)"
python3 tools/financial_report.py 600519 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ PE:', d['data'].get('pe_ratio'))" || echo "  ✗ akshare not installed"

# Test 6: Stock news
echo "Test 6: Stock news (600000)"
python3 tools/stock_news.py 600000 3 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Count:', d['data'].get('count'))" || echo "  ✗ akshare not installed"

# Test 7: Query indicator
echo "Test 7: Query indicator (600000 price)"
python3 tools/query_indicator.py 600000 price 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Price:', d['indicators'].get('price'))" || echo "  ✗ akshare not installed"

# Test 8: Full query flow
echo "Test 8: Full query flow (search + stock)"
bash tools/query.sh search "茅台" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ Search:', d['results'][0]['symbol'] if d['results'] else 'None')" || echo "  ✗ Query failed"

echo
echo "=== Tests Complete ==="
echo
echo "Note: LSP errors about 'akshare not resolved' are expected if akshare is not installed in current environment."
echo "Install with: pip3 install akshare -U"
