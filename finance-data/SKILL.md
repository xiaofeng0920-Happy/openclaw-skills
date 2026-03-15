---
name: finance-data
description: |
  Query A/HK stock prices, financial indicators, market news, and China macroeconomic data (GDP, CPI, PMI, etc.).
  
  **Triggers when user mentions:**
  - Market news: "市场消息", "市场动态", "财经新闻", "最新新闻", "有什么值得关注", "市场热点", "投资热点", "市场机会", "市场怎么看", "股市如何"
  - Stock queries: "股价", "股票价格", "查询股票", "股票代码", "股票怎么样"
  - Economic data: "GDP", "CPI", "PMI", "经济数据", "利率", "存款准备金率", "货币供应", "M2", "债券收益率"
  - Financial reports: "财报", "财务数据", "PE", "PB", "ROE", "估值", "股息率"
  - Market analysis: "市场分析", "行情", "走势", "大盘", "指数"
  
  Uses MCP (A-shares) and akshare (A/HK/funds/macro). Data delayed 15min. NOT investment advice.
homepage: https://github.com/elsejj/mcp-cn-a-stock
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["curl", "python3"] },
        "install":
          [
            {
              "id": "akshare",
              "kind": "pip",
              "package": "akshare",
              "label": "Install akshare: pip3 install akshare -U",
            },
          ],
      },
  }
---

# Finance Data Skill

Query Chinese and Hong Kong financial market data with comprehensive tools.

## Feature to Reference Mapping

| Feature | Reference Document |
|---------|-------------------|
| Search stock/fund codes | `references/search_stock.md` |
| Get stock info (price + indicators) | `references/get_stock_info.md` |
| Query specific indicators (PE, PB, ROE) | `references/query_indicator.md` |
| A-share real-time data | `references/mcp_query.md` |
| A/HK stock prices | `references/stock_query.md` |
| Fund NAV | `references/fund_query.md` |
| Financial reports | `references/financial_report.md` |
| Stock news | `references/stock_news.md` |
| Historical prices | `references/history_price.md` |
| Company announcements | `references/stock_announcements.md` |
| **Market news (real-time)** | `references/market_news.md` |
| **Macroeconomic data (GDP, CPI, etc.)** | `references/economic_data.md` |

## References

- `references/search_stock.md` — **Search stock/fund codes by name**
- `references/get_stock_info.md` — **Get comprehensive info (price + indicators + profile)**
- `references/query_indicator.md` — **Query specific indicators (PE, PB, ROE, etc.)**
- `references/mcp_query.md` — A-share real-time data via MCP
- `references/stock_query.md` — A/HK stock prices
- `references/fund_query.md` — Fund NAV
- `references/financial_report.md` — **Comprehensive financial statements**
- `references/stock_news.md` — Stock news
- `references/history_price.md` — **Historical price data**
- `references/stock_announcements.md` — **Company announcements**
- `references/market_news.md` — **Market news summary (real-time from Caixin)** ⭐
- `references/economic_data.md` — **Macroeconomic data (GDP, CPI, PMI, etc.)** ⭐

## Quick Start

### Step 1: Search for Code (if user provides NAME)

```bash
# Search A-share stock
{baseDir}/tools/query.sh search "茅台"
# Returns: 600519

# Search HK stock
{baseDir}/tools/query.sh search "腾讯"
# Returns: HK00700

# Search fund
{baseDir}/tools/query.sh search "易方达" fund
# Returns: 110011
```

### Step 2: Query Data

```bash
# Get comprehensive info (recommended)
{baseDir}/tools/query.sh info 600000
{baseDir}/tools/query.sh info HK00700

# Stock price
{baseDir}/tools/query.sh stock 600000
{baseDir}/tools/query.sh stock HK00700

# Fund NAV
{baseDir}/tools/query.sh fund 110011

# Financial report (comprehensive)
{baseDir}/tools/query.sh financial 600519
{baseDir}/tools/query.sh financial HK00700

# Stock news
{baseDir}/tools/query.sh news 600000 5

# Historical price
{baseDir}/tools/query.sh history 600000 30

# Company announcements
{baseDir}/tools/query.sh announcements 600000 3

# Market news (real-time) ⭐
{baseDir}/tools/query.sh market-news
{baseDir}/tools/query.sh market-news 30

# Market news (policy) ⭐
{baseDir}/tools/query.sh market-news --policy

# Economic data ⭐
{baseDir}/tools/query.sh economic gdp
{baseDir}/tools/query.sh economic cpi
{baseDir}/tools/query.sh economic pmi
{baseDir}/tools/query.sh economic all
```

## Available Tools

| Tool | Function | Data Source | Reference |
|------|----------|-------------|-----------|
| `search_stock.py` | Search codes by name | akshare | `references/search_stock.md` |
| `get_stock_info.py` | **Get comprehensive info** | MCP + akshare | `references/get_stock_info.md` |
| `query_indicator.py` | Query specific indicators | MCP + akshare | `references/query_indicator.md` |
| `mcp_query.py` | A-share real-time | MCP server | `references/mcp_query.md` |
| `stock_query.py` | A/HK stock prices | akshare | `references/stock_query.md` |
| `fund_query.py` | Fund NAV | akshare | `references/fund_query.md` |
| `financial_report.py` | **Comprehensive financials** | akshare | `references/financial_report.md` |
| `stock_news.py` | Stock news | akshare | `references/stock_news.md` |
| `history_price.py` | **Historical prices** | akshare | `references/history_price.md` |
| `stock_announcements.py` | **Company announcements** | akshare | `references/stock_announcements.md` |
| `market_news.py` | **Market news (real-time)** | Caixin/CCTV | `references/market_news.md` |
| `economic_data.py` | **Macroeconomic indicators** | akshare | `references/economic_data.md` |

## Symbol Format

### A-shares
- **Stock codes**: `600000`, `000001`, `300750` (6 digits)
- **Fund codes**: `110011`, `161725` (6 digits)

### HK stocks
- **Stock codes**: `HK00700`, `HK09988` (HK + 5 digits)

### Search by Name
```bash
# If unsure about code, search by name first
{baseDir}/tools/query.sh search "股票或基金名称"
```

## Examples

### Get Stock Info (Recommended)
**"贵州茅台现在怎么样？"**
```bash
{baseDir}/tools/query.sh info 600519
# Returns: price, PE, PB, change_pct
```

**"腾讯控股的公司信息"**
```bash
{baseDir}/tools/query.sh info HK00700
# Returns: price, PE, PB + company profile, industry, chairman
```

### Search by Name
**"腾讯控股的股价"**
```bash
# Step 1: Search for code
{baseDir}/tools/query.sh search "腾讯"
# Returns: HK00700

# Step 2: Query price
{baseDir}/tools/query.sh stock HK00700
```

### Query Financial Data
**"腾讯的财务数据"**
```bash
{baseDir}/tools/query.sh financial HK00700
# Returns: PE, PB, EPS, BVPS, dividend yield, ROE, ROA, revenue, profit, etc.
```

### Query Market News
**"最近市场有什么值得关注的"**
```bash
{baseDir}/tools/query.sh market-news
# Returns: Latest market news from Caixin
```

**"看看今天的财经新闻"**
```bash
{baseDir}/tools/query.sh market-news 10
# Returns: 10 latest news items
```

### Query Economic Data
**"中国最新的 GDP 数据"**
```bash
{baseDir}/tools/query.sh economic gdp
# Returns: GDP data with history
```

**"看看 CPI 和通胀情况"**
```bash
{baseDir}/tools/query.sh economic cpi
# Returns: CPI data with history
```

**"最新的宏观经济数据摘要"**
```bash
{baseDir}/tools/query.sh economic all
# Returns: Summary of GDP, CPI, PMI, M2, interest rates
```

## Market Support

### A-shares
- ✅ All indicators supported
- ✅ Technical indicators (MA, KDJ, MACD, RSI)
- ✅ Financial indicators (ROE, EPS, revenue)
- ✅ Fast MCP data source

### HK Stocks
- ✅ Price, PE, PB, market cap
- ✅ **Comprehensive financials** (EPS, BVPS, dividend yield, ROE, ROA, etc.)
- ✅ **Company profile** (industry, chairman, employees, description)
- ✅ **Historical prices** with statistics
- ✅ **Company announcements**
- ⚠️ Slower queries (50-60 seconds)

### Funds
- ✅ NAV, daily growth

## Data Sources

### MCP Server (A-shares only)
**Strengths:**
- ✅ Fast and free
- ✅ Real-time data
- ✅ Technical indicators

**Limitations:**
- ❌ A-shares only

### akshare (A/HK stocks, Funds, Macro)
**Strengths:**
- ✅ Comprehensive data
- ✅ HK stock support (financials, profile, history, announcements)
- ✅ Fund data
- ✅ Macroeconomic data (GDP, CPI, PMI, etc.)
- ✅ Market news (Caixin, CCTV)

**Limitations:**
- ❌ Slower for HK stocks (50-60s)
- ❌ May have rate limits

## Setup

```bash
# Install akshare
pip3 install akshare -U

# Verify installation
python3 -c "import akshare; print('akshare OK')"

# Test
python3 {baseDir}/tools/get_stock_info.py 600000
```

## Notes

- ⚠️ Data delayed by 15 minutes
- ⚠️ A/HK stocks only (no US stocks)
- ⚠️ HK stock queries may be slower (50-60s)
- ⚠️ This skill provides data only, NOT investment advice
- ⚠️ Market news is from Caixin (财新) - professional financial media

## Troubleshooting

**"akshare not found"**
```bash
pip3 install akshare -U
```

**"Indicators not supported"**
- HK stocks support limited indicators only
- Technical indicators (MA, KDJ, MACD) are A-share only

**"Data not available"**
- Check symbol format
- HK stock queries may take 50-60 seconds
- See specific reference for supported symbols

**"News query failed"**
- Check network connection
- API may be temporarily unavailable
- Retry after a few minutes
