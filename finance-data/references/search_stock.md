# Stock/Fund Search Reference

Search for stock or fund codes by name. Supports A-shares, HK stocks, and funds.

## When to Use

**Use this tool FIRST when the user provides a stock/fund NAME instead of a code:**

```
User: "阿里巴巴的股价"     → Search → Get code HK09988 → Query data
User: "腾讯控股怎么样"     → Search → Get code HK00700 → Query data
User: "贵州茅台财务数据"   → Search → Get code 600519 → Query data
User: "易方达中小盘净值"   → Search → Get code 110011 → Query data
```

## Ambiguity Handling

**When search returns multiple results, the tool will ask user to specify:**

```
User: "中航"
  ↓
Search returns 10+ results:
  - 中航光电 (002179)
  - 中航沈飞 (600760)
  - 中航西飞 (000768)
  - 中航产融 (600705)
  - ...
  ↓
Response: "找到 10 只股票，请指定具体名称或代码"
  ↓
User: "中航光电" or "002179"
  ↓
Search returns 1 result → Query data
```

**Strategy:**
- 1 result → Return directly
- 2+ results → Ask user to specify (ambiguous)
- 0 results → Suggest different keyword

## Usage

```bash
# Search for stock by name
python3 {baseDir}/tools/search_stock.py "阿里巴巴"

# Search for fund by name
python3 {baseDir}/tools/search_stock.py "易方达" fund

# Search in specific market
python3 {baseDir}/tools/search_stock.py "腾讯" stock hk

# Search all types
python3 {baseDir}/tools/search_stock.py "茅台" all
```

## Parameters

```bash
search_stock.py <keyword> [type] [market]

Arguments:
  keyword  - Search keyword (stock name, fund name, or code)
  type     - stock (default), fund, all
  market   - all (default), a, hk (only for stocks)
```

## Output Example

```json
{
  "keyword": "阿里巴巴",
  "count": 2,
  "results": [
    {
      "name": "阿里巴巴",
      "symbol": "09988",
      "market": "HK",
      "full_symbol": "HK09988"
    },
    {
      "name": "阿里巴巴健康",
      "symbol": "00241",
      "market": "HK",
      "full_symbol": "HK00241"
    }
  ]
}
```

## Result Fields

- `name`: Stock/fund name (名称)
- `symbol`: Code without prefix (代码)
- `market`: Market type (A, HK, FUND)
- `full_symbol`: Code with prefix (完整代码)
- `type`: Fund type (only for funds)

## Symbol Prefix Rules

| Market | Prefix | Example |
|--------|--------|---------|
| A-share (6xxxxx) | `SH` | `600000` → `SH600000` |
| A-share (0/3xxxxx) | `SZ` | `000001` → `SZ000001` |
| HK stocks | `HK` | `09988` → `HK09988` |
| Funds | (none) | `110011` |

## Common Search Examples

### A-shares
```bash
# Search by name
python3 {baseDir}/tools/search_stock.py "茅台"
python3 {baseDir}/tools/search_stock.py "宁德时代"
python3 {baseDir}/tools/search_stock.py "平安银行"

# Results include:
# - 贵州茅台 (600519)
# - 宁德时代 (300750)
# - 平安银行 (000001)
```

### HK stocks
```bash
# Search by name
python3 {baseDir}/tools/search_stock.py "腾讯"
python3 {baseDir}/tools/search_stock.py "阿里"
python3 {baseDir}/tools/search_stock.py "美团"

# Results include:
# - 腾讯控股 (HK00700)
# - 阿里巴巴 (HK09988)
# - 美团 (HK03690)
```

### Funds
```bash
# Search fund by name
python3 {baseDir}/tools/search_stock.py "易方达" fund
python3 {baseDir}/tools/search_stock.py "中小盘" fund
python3 {baseDir}/tools/search_stock.py "110011" fund

# Results include:
# - 易方达中小盘 (110011)
```

## Workflow for LLM

**When user asks about a stock/fund by NAME:**

```
Step 1: Search for the code
  → query.sh search "阿里巴巴"
  → Get: HK09988

Step 2: Query the data
  → query.sh stock HK09988
  → Get: price, change, volume, etc.

Step 3: Present to user
  → "阿里巴巴 (HK09988) 当前股价为 XXX..."
```

## Troubleshooting

**"No results found"**
- Try different keyword (full name vs abbreviation)
- Stock may not be in the database
- Try searching in specific market: `search_stock.py "XXX" stock hk`

**"akshare not found"**
```bash
pip3 install akshare -U
```

**"Search too slow"**
- Search scans large datasets
- Specify market to narrow search: `search_stock.py "XXX" stock a`

## Related

- `references/stock_query.md` — Query stock prices
- `references/fund_query.md` — Query fund NAV
- `references/financial_report.md` — Query financial data
