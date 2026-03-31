# History Price Reference

Get historical stock price data and statistical analysis.

## When to Use

**Use this tool when you need historical price data:**

```
User: "腾讯控股最近一个月的走势"
User: "看看茅台的历史价格"
User: "过去 30 天的最高价和最低价"
```

## Usage

```bash
# A-share, last 30 days
python3 {baseDir}/tools/history_price.py 600000 30

# HK stock, last 90 days
python3 {baseDir}/tools/history_price.py HK00700 90

# Default (30 days)
python3 {baseDir}/tools/history_price.py 600519
```

## Data Fields

### Statistics
| Field | Description | Chinese |
|-------|-------------|---------|
| `period_high` | Highest price in period | 期间最高价 |
| `period_low` | Lowest price in period | 期间最低价 |
| `period_avg` | Average closing price | 平均收盘价 |
| `price_change` | Price change | 价格变化 |
| `price_change_pct` | Price change % | 价格变化百分比 |
| `volatility` | Volatility (std dev) | 波动率 |
| `avg_daily_change` | Average daily change % | 平均日涨跌幅 |
| `total_volume` | Total trading volume | 总成交量 |
| `avg_volume` | Average daily volume | 平均成交量 |

### Latest Data
| Field | Description | Chinese |
|-------|-------------|---------|
| `date` | Latest trading date | 最新交易日 |
| `open` | Opening price | 开盘价 |
| `high` | High price | 最高价 |
| `low` | Low price | 最低价 |
| `close` | Closing price | 收盘价 |
| `volume` | Trading volume | 成交量 |

## Output Example

```bash
python3 {baseDir}/tools/history_price.py 600000 30
```

```json
{
  "symbol": "600000",
  "days": 30,
  "data_points": 30,
  "statistics": {
    "period_high": 10.50,
    "period_low": 9.20,
    "period_avg": 9.85,
    "price_change": 0.48,
    "price_change_pct": 5.21,
    "volatility": 1.85,
    "avg_daily_change": 1.42,
    "total_volume": 500000000,
    "avg_volume": 16666666
  },
  "latest_data": {
    "date": "2026-03-02",
    "open": 9.68,
    "high": 9.85,
    "low": 9.60,
    "close": 9.76,
    "volume": 15000000
  }
}
```

## Use Cases

### Check price trend
```bash
# Last 30 days
python3 {baseDir}/tools/history_price.py 600519 30
```

### Check volatility
```bash
# Last 90 days for more data
python3 {baseDir}/tools/history_price.py HK00700 90
```

### Compare with current price
```bash
# Get history
python3 {baseDir}/tools/history_price.py 600000 30

# Compare period_avg with current price
# If current > period_avg, stock is trending up
```

## Performance

| Market | Speed | Data Points |
|--------|-------|-------------|
| A-shares | ⚡️ Fast (3-5s) | Up to 5000+ |
| HK stocks | 🐌 Slow (50-60s) | Up to 5000+ |

## Troubleshooting

**"Failed to get history data"**
- Check symbol format (6-digit for A-shares, HK + 5-digit for HK stocks)
- HK stock queries may take 50-60 seconds
- Market may be closed (weekend/holiday)

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/stock_query.md` — Query current stock price
- `references/query_indicator.md` — Query specific indicators
- `references/get_stock_info.md` — Get comprehensive stock info
