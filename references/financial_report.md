# Financial Report Reference

Query comprehensive financial data for A-shares and HK stocks.

## When to Use

**Use this tool when you need detailed financial metrics:**

```
User: "腾讯的财务数据怎么样"
User: "茅台的 ROE 和毛利率"
User: "看看浦发银行的股息率"
```

## Usage

```bash
# A-share financial data
python3 {baseDir}/tools/financial_report.py 600519

# HK stock comprehensive financials
python3 {baseDir}/tools/financial_report.py HK00700
```

## Available Indicators

### A-shares (A 股)
| Category | Indicators |
|----------|-----------|
| **Valuation** | PE(TTM), PE(静), PB, PS |
| **Market Cap** | 总市值，流通市值 |
| **Price** | 当日收盘价，当日涨跌幅 |

### HK Stocks (港股) - Comprehensive
| Category | Indicators |
|----------|-----------|
| **Valuation** | PE, PB |
| **Per Share** | EPS, BVPS, 每股股息，每股经营现金流 |
| **Dividends** | 股息率，派息比率 |
| **Market Cap** | 总市值 |
| **Income** | 营业总收入，净利润 |
| **Margins** | 销售净利率，毛利率 |
| **Returns** | ROE, ROA, ROIC |
| **Growth** | 营收同比增长，利润同比增长 |
| **Financial Health** | 资产负债率，流动比率 |
| **Cash Flow** | 经营现金流/销售 |

## Output Example

### A-share
```bash
python3 {baseDir}/tools/financial_report.py 600519
```

```json
{
  "source": "akshare",
  "type": "financial",
  "symbol": "600519",
  "data": {
    "pe_ratio": 28.5,
    "pe_static": 27.8,
    "pb_ratio": 7.2,
    "ps_ratio": 12.5,
    "market_cap": 2500000000000,
    "price": 1850.00
  }
}
```

### HK Stock (Comprehensive)
```bash
python3 {baseDir}/tools/financial_report.py HK00700
```

```json
{
  "source": "akshare",
  "type": "financial",
  "symbol": "HK00700",
  "data": {
    "pe_ratio": 20.03,
    "pb_ratio": 3.65,
    "eps": 18.32,
    "bvps": 128.05,
    "dividend_per_share": 4.5,
    "dividend_yield": 0.86,
    "payout_ratio": 17.35,
    "market_cap": 4680667048250,
    "revenue": 557395000000,
    "net_profit": 166582000000,
    "net_profit_margin": 30.63,
    "roe": 15.53,
    "roa": 8.64,
    "revenue_yoy": 8.41,
    "net_profit_yoy": 68.44,
    "gross_margin": 52.90,
    "debt_ratio": 40.83,
    "current_ratio": 1.25
  }
}
```

## Use Cases

### Check valuation
```bash
# PE and PB
python3 {baseDir}/tools/financial_report.py 600519
```

### Check profitability
```bash
# ROE, ROA, margins
python3 {baseDir}/tools/financial_report.py HK00700
```

### Check dividend stocks
```bash
# Dividend yield, payout ratio
python3 {baseDir}/tools/financial_report.py 600000
```

### Check growth
```bash
# Revenue and profit growth
python3 {baseDir}/tools/financial_report.py HK00700
```

## Data Sources

| Market | API | Status |
|--------|-----|--------|
| A-shares | stock_value_em | ✅ |
| HK stocks | stock_hk_financial_indicator_em | ✅ |
| HK stocks | stock_financial_hk_analysis_indicator_em | ✅ |

## Troubleshooting

**"Financial query failed"**
- Check symbol format (6-digit for A-shares, HK + 5-digit for HK stocks)
- Some indicators may not be available for all stocks
- HK stock data may take longer to fetch

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/query_indicator.md` — Query specific indicators
- `references/get_stock_info.md` — Get comprehensive stock info
- `references/stock_query.md` — Query stock prices
