# Get Stock Info Reference

Get comprehensive stock/fund information (price + key indicators + company profile).

## When to Use

**Use this tool when user asks for general stock information:**

```
User: "贵州茅台现在怎么样？"
User: "看看腾讯控股的信息"
User: "易方达中小盘的净值"
```

**Returns:**
- **A-shares**: price, change_pct, pe_ratio, pb_ratio (from MCP, fast)
- **HK stocks**: price, change_pct, PE, PB, market_cap + **company profile**
- **Funds**: nav, daily_growth

## Usage

```bash
# Get A-share info
python3 {baseDir}/tools/get_stock_info.py 600519

# Get HK stock info (with company profile)
python3 {baseDir}/tools/get_stock_info.py HK00700

# Get fund info
python3 {baseDir}/tools/get_stock_info.py 110011
```

## Data Fields

### A-shares & HK Stocks
| Field | Description | Chinese |
|-------|-------------|---------|
| `price` | Current price | 当前价格 |
| `change_pct` | Percentage change | 涨跌幅 |
| `pe_ratio` | P/E ratio | 市盈率 |
| `pb_ratio` | P/B ratio | 市净率 |
| `market_cap` | Market capitalization | 总市值 |

### HK Stocks - Company Profile
| Field | Description | Chinese |
|-------|-------------|---------|
| `company_name` | Company name | 公司名称 |
| `industry` | Industry sector | 所属行业 |
| `chairman` | Chairman | 董事长 |
| `employees` | Number of employees | 员工人数 |
| `profile` | Company description | 公司介绍 |

### Funds
| Field | Description | Chinese |
|-------|-------------|---------|
| `nav` | Net Asset Value | 单位净值 |
| `daily_growth` | Daily growth rate | 日增长率 |

## Output Examples

### A-share (from MCP)
```bash
python3 {baseDir}/tools/get_stock_info.py 600000
```

```json
{
  "source": "mcp",
  "type": "stock",
  "symbol": "600000",
  "name": "浦发银行",
  "data": {
    "price": 9.76,
    "change_pct": 1.03,
    "pe_ratio": 6.76,
    "pb_ratio": 0.43
  },
  "update_time": "2026-03-02",
  "note": "Use query_indicator.py for specific indicators, stock_news.py for news"
}
```

### HK Stock (with company profile)
```bash
python3 {baseDir}/tools/get_stock_info.py HK00700
```

```json
{
  "source": "akshare",
  "type": "stock",
  "symbol": "HK00700",
  "name": "腾讯控股有限公司",
  "data": {
    "price": 523.5,
    "change_pct": 2.15,
    "pe_ratio": 20.03,
    "pb_ratio": 3.65,
    "market_cap": 4680667048250,
    "company_name": "腾讯控股有限公司",
    "industry": "软件服务",
    "chairman": "马化腾",
    "employees": 115076,
    "profile": "腾讯控股有限公司是一家世界领先的互联网科技公司..."
  },
  "update_time": "",
  "note": "Use query_indicator.py for specific indicators, stock_news.py for news"
}
```

### Fund
```bash
python3 {baseDir}/tools/get_stock_info.py 110011
```

```json
{
  "source": "akshare",
  "type": "fund",
  "symbol": "110011",
  "name": "110011",
  "data": {
    "nav": 8.523,
    "daily_growth": 1.25
  },
  "update_time": "2026-03-02",
  "note": "Use query_indicator.py for specific indicators"
}
```

## Use Cases

### User asks for stock info
```
User: "贵州茅台现在怎么样？"
  ↓
LLM: get_stock_info.py 600519
  ↓
Returns: price, PE, PB, change_pct
  ↓
LLM: "贵州茅台当前股价 XXX，市盈率 XXX..."
```

### User asks for company info
```
User: "腾讯是做什么的？"
  ↓
LLM: get_stock_info.py HK00700
  ↓
Returns: company profile, industry, chairman
  ↓
LLM: "腾讯控股是一家互联网科技公司，董事长马化腾..."
```

### User asks for fund info
```
User: "易方达中小盘净值多少？"
  ↓
LLM: get_stock_info.py 110011
  ↓
Returns: nav, daily_growth
  ↓
LLM: "易方达中小盘当前净值 XXX，日增长 XXX%"
```

## Data Source Priority

### A-shares
1. **MCP Server** (fast, real-time) ← Primary
2. **akshare** (fallback if MCP fails)

### HK stocks
- **akshare.stock_hk_spot()** + **stock_hk_company_profile_em()**

### Funds
- **akshare.fund_open_fund_info_em()**

## Performance

| Market | Data Source | Speed |
|--------|-------------|-------|
| A-shares | MCP | ⚡️ Fast (3-5s) |
| A-shares | akshare (fallback) | ⚡️ Fast (3-5s) |
| HK stocks | akshare | 🐌 Slow (50-60s) |
| Funds | akshare | ⚡️ Fast (3-5s) |

## Troubleshooting

**"Failed to get stock info"**
- Check symbol format (6-digit for A-shares/funds, HK + 5-digit for HK stocks)
- MCP server may be temporarily unavailable
- HK stock queries may take 50-60 seconds

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/search_stock.md` — Search for stock codes by name
- `references/query_indicator.md` — Query specific indicators
- `references/stock_query.md` — Query full stock data
- `references/stock_news.md` — Query stock news
- `references/financial_report.md` — Query detailed financial data
