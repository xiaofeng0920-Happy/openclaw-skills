# Stock Query Reference

Query stock prices (A/HK shares) via akshare.

## Usage

```bash
# A-share stock
python3 {baseDir}/tools/stock_query.py 600000

# HK stock
python3 {baseDir}/tools/stock_query.py HK00700
```

## Symbol Format

- **A-shares**: `600000`, `000001`, `300750`
- **HK stocks**: `HK00700`, `HK09988`

## Output Example

```json
{
  "source": "akshare",
  "type": "stock",
  "symbol": "HK00700",
  "name": "腾讯控股",
  "data": {
    "price": 450.20,
    "change": 5.60,
    "change_pct": 1.26,
    "pe_ratio": 18.5,
    "pb_ratio": 3.2,
    "dividend_yield": 0.42
  },
  "update_time": ""
}
```

## Data Fields

- `price`: Current price
- `change`: Price change
- `change_pct`: Percentage change
- `volume`: Trading volume
- `turnover`: Trading value
- `market_cap`: Market capitalization
- `pe_ratio`: P/E ratio (HK stocks)
- `pb_ratio`: P/B ratio (HK stocks)
- `dividend_yield`: Dividend yield (HK stocks)

## Data Sources

- A-shares: 东方财富
- HK stocks: 新浪财经

## Troubleshooting

**"akshare not found"**
```bash
pip3 install akshare -U
```

**"Data not available"**
- Check symbol format
- Some stocks may not be available
- Try MCP for A-shares: `references/mcp_query.md`

**"Query failed"**
- Network issue
- Data source temporarily unavailable
- Retry after a few minutes

## Related

- `references/mcp_query.md` — A-shares via MCP (faster)
- `references/financial_report.md` — Financial statements
