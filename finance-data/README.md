# Finance Data Skill

Comprehensive financial data query skill for OpenClaw supporting A-shares, HK stocks, and funds.

## Features

- **A-shares** (沪深股票): Real-time prices, comprehensive financials, news, announcements
- **HK stocks** (港股): Prices, comprehensive financials, company profile, news, announcements, history
- **Funds** (基金): NAV, daily growth
- **Financial Reports** (财报): PE, PB, EPS, BVPS, ROE, ROA, dividends, growth rates
- **Stock News** (资讯): A/HK stock news
- **Company Announcements** (公告): Important company announcements
- **Historical Prices** (历史价格): Price history with statistics
- **Market News** (市场动态): Economic news, policy interpretation ⭐ NEW
- **Economic Data** (宏观经济): GDP, CPI, PMI, interest rates, M2, etc. ⭐ NEW

## Directory Structure

```
finance-data/
├── SKILL.md                    # Main skill definition
├── README.md                   # This file
├── tools/
│   ├── query.sh                # Unified entry point
│   ├── search_stock.py         # Search codes by name
│   ├── get_stock_info.py       # Comprehensive info ⭐
│   ├── query_indicator.py      # Query specific indicators
│   ├── mcp_query.py            # MCP server (A-shares)
│   ├── stock_query.py          # Stock prices
│   ├── fund_query.py           # Funds
│   ├── financial_report.py     # Comprehensive financials ⭐
│   ├── stock_news.py           # Stock news (A/HK)
│   ├── history_price.py        # Historical prices ⭐ NEW
│   ├── stock_announcements.py  # Announcements ⭐ NEW
│   ├── market_news.py          # Market news ⭐ NEW
│   └── economic_data.py        # Economic data ⭐ NEW
└── references/
    ├── search_stock.md
    ├── get_stock_info.md
    ├── query_indicator.md
    ├── mcp_query.md
    ├── stock_query.md
    ├── fund_query.md
    ├── financial_report.md
    ├── stock_news.md
    ├── history_price.md        ⭐ NEW
    ├── stock_announcements.md  ⭐ NEW
    ├── market_news.md          ⭐ NEW
    └── economic_data.md        ⭐ NEW
```

## Installation

```bash
# Required: akshare
pip3 install akshare -U

# Verify installation
python3 -c "import akshare; print('akshare OK')"
```

## Quick Start

```bash
# Search stock by name
./tools/query.sh search "茅台"

# Get comprehensive info
./tools/query.sh info 600000

# Query stock price
./tools/query.sh stock 600000

# Query financial data
./tools/query.sh financial 600519

# Query fund NAV
./tools/query.sh fund 110011

# Query stock news
./tools/query.sh news 600000 5

# Query historical prices
./tools/query.sh history 600000 30

# Query announcements
./tools/query.sh announcements 600000 3

# Market news (NEW)
./tools/query.sh market-news
./tools/query.sh market-news --policy

# Economic data (NEW)
./tools/query.sh economic gdp
./tools/query.sh economic cpi
./tools/query.sh economic all
```

## Testing

```bash
# Run comprehensive tests
bash test.sh

# Test individual scripts
python3 tools/get_stock_info.py 600000
python3 tools/financial_report.py HK00700
python3 tools/history_price.py 600000 30
```

## Symbol Format

- **A-shares**: `600000`, `000001`, `300750`
- **HK stocks**: `HK00700`, `HK09988`
- **Funds**: `110011`, `161725`

## Data Sources

| Source | Coverage | Speed | Status |
|--------|----------|-------|--------|
| MCP | A-shares | Fast | ✅ |
| akshare | A/HK stocks, Funds | Medium | ✅ |

## Notes

- ⚠️ Data delayed by 15 minutes
- ⚠️ A/HK stocks only (no US stocks)
- ⚠️ This skill provides data only, NOT investment advice

## Troubleshooting

**"akshare not found"**
```bash
pip3 install akshare -U
```

**"Data not available"**
- Check symbol format (6-digit code)
- See specific reference for supported symbols

## References

For detailed usage of each tool, see the corresponding reference document in `references/` directory.
