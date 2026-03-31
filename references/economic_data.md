# Economic Data Reference

Query China macroeconomic indicators via akshare.

## When to Use

**Use this tool when you need:**

- GDP growth rates and economic output
- Inflation data (CPI, PPI)
- Manufacturing indicators (PMI)
- Monetary policy data (interest rates, M2, RRR)
- Bond market data (yield curve)

```
User: "中国最新的 GDP 数据是多少"
User: "看看 CPI 和通胀情况"
User: "现在的利率和存款准备金率"
User: "最新的宏观经济数据摘要"
```

## Usage

### Direct Script Usage

```bash
# Single indicator
python3 {baseDir}/tools/economic_data.py gdp
python3 {baseDir}/tools/economic_data.py cpi
python3 {baseDir}/tools/economic_data.py pmi
python3 {baseDir}/tools/economic_data.py rate
python3 {baseDir}/tools/economic_data.py m2
python3 {baseDir}/tools/economic_data.py rrr
python3 {baseDir}/tools/economic_data.py bond

# All indicators summary
python3 {baseDir}/tools/economic_data.py all
```

### Via query.sh (Recommended)

```bash
# Single indicator
{baseDir}/tools/query.sh economic gdp
{baseDir}/tools/query.sh economic cpi
{baseDir}/tools/query.sh economic pmi
{baseDir}/tools/query.sh economic rate
{baseDir}/tools/query.sh economic m2
{baseDir}/tools/query.sh economic rrr
{baseDir}/tools/query.sh economic bond

# All indicators summary
{baseDir}/tools/query.sh economic all
```

## Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `indicator` | string | `gdp`, `cpi`, `pmi`, `rate`, `m2`, `rrr`, `bond`, `all` | Economic indicator to query |

### Supported Indicators

| Indicator | Description | Frequency | API |
|-----------|-------------|-----------|-----|
| `gdp` | 国内生产总值 (Gross Domestic Product) | Quarterly | `macro_china_gdp()` |
| `cpi` | 居民消费价格指数 (Consumer Price Index) | Monthly | `macro_china_cpi()` |
| `pmi` | 采购经理指数 (Purchasing Managers' Index) | Monthly | `macro_china_pmi()` |
| `rate` | 央行利率 (Central Bank Interest Rate) | As announced | `macro_bank_china_interest_rate()` |
| `m2` | 货币供应量 (Money Supply M0/M1/M2) | Monthly | `macro_china_money_supply()` |
| `rrr` | 存款准备金率 (Reserve Requirement Ratio) | As announced | `macro_china_reserve_requirement_ratio()` |
| `bond` | 债券收益率曲线 (Bond Yield Curve) | Daily | `bond_china_yield()` |
| `all` | 全部宏观数据摘要 (All indicators summary) | - | Multiple APIs |

### Unsupported Indicators

If you query an unsupported indicator, you will receive an error:

```bash
{baseDir}/tools/query.sh economic invalid
```

```json
{
  "error": "Unknown indicator",
  "indicator": "invalid",
  "available": ["gdp", "cpi", "pmi", "rate", "m2", "rrr", "bond", "all"]
}
```

## Output Format

Each indicator returns:
- **Latest**: Most recent data point (full details)
- **History**: Previous 10 periods (key fields only)
- **Disclaimer**: Investment disclaimer

## Output Examples

### GDP (国内生产总值)

```bash
{baseDir}/tools/query.sh economic gdp
```

```json
{
  "source": "akshare",
  "type": "economic_data",
  "indicator": "gdp",
  "indicator_name": "国内生产总值",
  "data": {
    "latest": {
      "quarter": "2025 年第 1-4 季度",
      "gdp_total": 1401879.2,
      "gdp_yoy": 5.0,
      "primary_industry": 93346.8,
      "secondary_industry": 499653.0,
      "tertiary_industry": 808879.3
    },
    "history": [
      {
        "quarter": "2025 年第 1-3 季度",
        "gdp_total": 1013967.9,
        "gdp_yoy": 5.2
      }
    ]
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

### CPI (居民消费价格指数)

```bash
{baseDir}/tools/query.sh economic cpi
```

```json
{
  "source": "akshare",
  "type": "economic_data",
  "indicator": "cpi",
  "indicator_name": "居民消费价格指数",
  "data": {
    "latest": {
      "month": "2026 年 01 月份",
      "cpi_index": 100.2,
      "cpi_yoy": 0.2,
      "cpi_mom": 0.2
    },
    "history": [...]
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

### PMI (采购经理指数)

```bash
{baseDir}/tools/query.sh economic pmi
```

```json
{
  "source": "akshare",
  "type": "economic_data",
  "indicator": "pmi",
  "indicator_name": "采购经理指数",
  "data": {
    "latest": {
      "month": "2026 年 01 月份",
      "manufacturing_pmi": 49.3,
      "non_manufacturing_pmi": 49.4
    },
    "history": [...]
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

### All Indicators Summary

```bash
{baseDir}/tools/query.sh economic all
```

```json
{
  "source": "akshare",
  "type": "economic_data",
  "indicator": "all",
  "indicator_name": "宏观经济数据摘要",
  "data": {
    "gdp": {
      "latest_quarter": "2025 年第 1-4 季度",
      "gdp_yoy": 5.0
    },
    "cpi": {
      "latest_month": "2026 年 01 月份",
      "cpi_yoy": 0.2
    },
    "pmi": {
      "latest_month": "2026 年 01 月份",
      "manufacturing_pmi": 49.3,
      "non_manufacturing_pmi": 49.4
    },
    "m2": {
      "latest_month": "2026 年 01 月份",
      "m2_total": 3471860.39,
      "m2_yoy": 9.0
    },
    "rate": {
      "item": "中国央行决议报告",
      "date": "1991-05-01",
      "rate": 8.64
    }
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

## Data Field Descriptions

### GDP
| Field | Type | Description |
|-------|------|-------------|
| `quarter` | string | Quarter (e.g., "2025 年第 1-4 季度") |
| `gdp_total` | float | Total GDP (亿元) |
| `gdp_yoy` | float | Year-over-year growth (%) |
| `primary_industry` | float | Primary industry output (第一产业) |
| `secondary_industry` | float | Secondary industry output (第二产业) |
| `tertiary_industry` | float | Tertiary industry output (第三产业) |

### CPI
| Field | Type | Description |
|-------|------|-------------|
| `month` | string | Month (e.g., "2026 年 01 月份") |
| `cpi_index` | float | CPI index (base=100) |
| `cpi_yoy` | float | Year-over-year change (%) |
| `cpi_mom` | float | Month-over-month change (%) |

### PMI
| Field | Type | Description |
|-------|------|-------------|
| `month` | string | Month |
| `manufacturing_pmi` | float | Manufacturing PMI (>50 = expansion, <50 = contraction) |
| `non_manufacturing_pmi` | float | Non-manufacturing PMI |

### M2 (Money Supply)
| Field | Type | Description |
|-------|------|-------------|
| `month` | string | Month |
| `m2_total` | float | M2 total (亿元) |
| `m2_yoy` | float | Year-over-year change (%) |
| `m1_total` | float | M1 total (亿元) |
| `m1_yoy` | float | M1 year-over-year change (%) |
| `m0_total` | float | M0 (cash in circulation) total (亿元) |

### RRR (Reserve Requirement Ratio)
| Field | Type | Description |
|-------|------|-------------|
| `announce_date` | string | Announcement date |
| `effective_date` | string | Effective date |
| `large_institution_before/after` | float | Large institutions RRR (%) |
| `small_institution_before/after` | float | Small institutions RRR (%) |
| `large/small_institution_change` | float | Change in percentage points |
| `note` | string | Policy notes |

### Bond Yield
| Field | Type | Description |
|-------|------|-------------|
| `curve` | string | Yield curve name |
| `date` | string | Date |
| `yield_3m` to `yield_30y` | float | Yields for different maturities (%) |

## Use Cases

### Check economic growth
```bash
{baseDir}/tools/query.sh economic gdp
```

### Check inflation
```bash
{baseDir}/tools/query.sh economic cpi
```

### Check manufacturing activity
```bash
{baseDir}/tools/query.sh economic pmi
# PMI > 50: Expansion
# PMI < 50: Contraction
```

### Check monetary policy stance
```bash
{baseDir}/tools/query.sh economic rate
{baseDir}/tools/query.sh economic m2
{baseDir}/tools/query.sh economic rrr
```

### Quick overview of all indicators
```bash
{baseDir}/tools/query.sh economic all
```

## Data Sources

| Indicator | API | Status |
|-----------|-----|--------|
| GDP | `macro_china_gdp()` | ✅ |
| CPI | `macro_china_cpi()` | ✅ |
| PMI | `macro_china_pmi()` | ✅ |
| Interest Rate | `macro_bank_china_interest_rate()` | ✅ |
| M2 | `macro_china_money_supply()` | ✅ |
| RRR | `macro_china_reserve_requirement_ratio()` | ✅ |
| Bond Yield | `bond_china_yield()` | ✅ |

## Limitations

- ⚠️ China macro data only (no US/EU data)
- ⚠️ Some indicators may have publication delays
- ⚠️ Historical data depth varies by indicator
- ⚠️ GDP is quarterly, not monthly
- ⚠️ RRR changes are infrequent (policy-driven)
- ⚠️ Bond yield data may be outdated (last update: 2020-02-04)

## Troubleshooting

**"Data query failed"**
- Check network connection
- API may be temporarily unavailable
- Some indicators have limited history

**"Unknown indicator"**
- Available indicators: `gdp`, `cpi`, `pmi`, `rate`, `m2`, `rrr`, `bond`, `all`
- Use `all` to see summary of all indicators

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/market_news.md` — Economic news and policy announcements
- `references/get_stock_info.md` — Stock info and indicators
- `references/financial_report.md` — Company financial reports
