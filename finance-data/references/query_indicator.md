# Stock Indicator Query Reference

Query specific stock indicators (price, valuation, financial, technical).

## Market Support

### A-shares (A 股)
**Supports ALL indicators:**
- ✅ Price indicators (价格指标)
- ✅ Valuation indicators (估值指标)
- ✅ Market cap indicators (市值指标)
- ✅ Trading indicators (交易指标)
- ✅ Financial indicators (财务指标)
- ✅ **Technical indicators (技术指标)** - via MCP only

### HK Stocks (港股)
**Supports LIMITED indicators:**
- ✅ Price: `price`, `change`, `change_pct`
- ✅ Valuation: `pe_ratio`, `pb_ratio`, `dividend_yield`
- ✅ Market cap: `market_cap`
- ❌ **Technical indicators NOT supported** (MA, KDJ, MACD, RSI)
- ❌ Financial indicators NOT supported (revenue, profit, ROE, etc.)

## Usage

```bash
# A-share - all indicators supported
python3 {baseDir}/tools/query_indicator.py 600519 price pe_ratio roe ma5

# HK stock - limited indicators
python3 {baseDir}/tools/query_indicator.py HK00700 price pe_ratio market_cap

# HK stock - unsupported indicators will show error
python3 {baseDir}/tools/query_indicator.py HK00700 ma5 kdj_k
# Error: Indicators not supported for this market
```

## Available Indicators

### Price Indicators (价格指标)
| Canonical | Chinese | Aliases | A-share | HK |
|-----------|---------|---------|---------|-----|
| `price` | 当前价格 | 股价，现价 | ✅ | ✅ |
| `change` | 涨跌额 | 涨跌 | ✅ | ✅ |
| `change_pct` | 涨跌幅 | 涨幅，跌幅 | ✅ | ✅ |

### Valuation Indicators (估值指标)
| Canonical | Chinese | A-share | HK |
|-----------|---------|---------|-----|
| `pe_ratio` | 市盈率 | ✅ | ✅ |
| `pb_ratio` | 市净率 | ✅ | ✅ |
| `dividend_yield` | 股息率 | ✅ | ✅ |
| `ps_ratio` | 市销率 | ✅ | ❌ |
| `peg_ratio` | PEG 值 | ✅ | ❌ |

### Market Cap Indicators (市值指标)
| Canonical | Chinese | A-share | HK |
|-----------|---------|---------|-----|
| `market_cap` | 总市值 | ✅ | ✅ |
| `float_market_cap` | 流通市值 | ✅ | ❌ |

### Financial Indicators (财务指标)
| Canonical | Chinese | A-share | HK |
|-----------|---------|---------|-----|
| `roe` | 净资产收益率 | ✅ | ❌ |
| `eps` | 每股收益 | ✅ | ❌ |
| `revenue` | 营业收入 | ✅ | ❌ |
| `net_profit` | 净利润 | ✅ | ❌ |

### Technical Indicators (技术指标) - A-share ONLY
| Canonical | Chinese | A-share | HK |
|-----------|---------|---------|-----|
| `ma5` | 5 日均线 | ✅ | ❌ |
| `kdj_k` | KDJ-K | ✅ | ❌ |
| `macd_dif` | MACD-DIF | ✅ | ❌ |
| `rsi6` | RSI(6) | ✅ | ❌ |

## Error Messages

### Unsupported Indicators for HK Stocks
```bash
python3 tools/query_indicator.py HK00700 ma5 kdj_k
```

```json
{
  "error": "Indicators not supported for this market",
  "symbol": "HK00700",
  "market": "HK",
  "unsupported": ["ma5", "kdj_k"],
  "hk_supported": ["price", "change", "pe_ratio", "pb_ratio", ...],
  "hint": "HK stocks support limited indicators. Technical indicators are A-share only."
}
```

### Invalid Indicator Name
```bash
python3 tools/query_indicator.py 600000 invalid_indicator
```

```json
{
  "error": "Invalid indicators",
  "invalid": ["invalid_indicator"],
  "valid_indicators": ["price", "pe_ratio", ...]
}
```

## Examples

### A-share - All Indicators
```bash
# Price + Valuation
python3 {baseDir}/tools/query_indicator.py 600519 price pe_ratio pb_ratio

# Financial
python3 {baseDir}/tools/query_indicator.py 600519 roe eps revenue

# Technical (A-share only)
python3 {baseDir}/tools/query_indicator.py 600000 ma5 ma20 kdj_k macd_dif

# Mixed
python3 {baseDir}/tools/query_indicator.py 600519 price pe_ratio roe ma5
```

### HK Stock - Limited Indicators
```bash
# Price + Valuation (supported)
python3 {baseDir}/tools/query_indicator.py HK00700 price pe_ratio

# Market cap (supported)
python3 {baseDir}/tools/query_indicator.py HK00700 market_cap

# Technical (NOT supported - will error)
python3 {baseDir}/tools/query_indicator.py HK00700 ma5
# Error: Indicators not supported for this market
```

## Related

- `references/search_stock.md` — Search for stock codes by name
- `references/stock_query.md` — Query full stock data
- `references/mcp_query.md` — A-share real-time data via MCP
