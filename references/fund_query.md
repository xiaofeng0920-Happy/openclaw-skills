# Fund Query Reference

Query fund NAV and performance data via akshare.

## Usage

```bash
# Fund NAV
python3 {baseDir}/tools/fund_query.py 110011

# Get detailed info
python3 {baseDir}/tools/fund_query.py 000001
```

## Symbol Format

- **Open-end funds**: `110011`, `000001`, `161725`
- **ETF**: `510300`, `159915`

## Output Example

```json
{
  "source": "akshare",
  "type": "fund",
  "symbol": "110011",
  "name": "易方达中小盘混合",
  "data": {
    "nav": 8.523,
    "accumulated_nav": 9.123,
    "daily_growth": 1.25,
    "fund_type": "股票型",
    "fund_manager": "张坤",
    "company": "易方达基金"
  },
  "update_time": "2026-03-02"
}
```

## Data Fields

- `nav`: Net asset value (单位净值)
- `accumulated_nav`: Accumulated NAV (累计净值)
- `daily_growth`: Daily growth rate (日增长率)
- `fund_type`: Fund type (基金类型)
- `fund_manager`: Fund manager (基金经理)
- `company`: Fund company (基金公司)

## Fund Types

- 股票型 (Equity)
- 混合型 (Hybrid)
- 债券型 (Bond)
- 货币型 (Money Market)
- QDII (Overseas Investment)

## Troubleshooting

**"Fund not found"**
- Check fund code (6 digits)
- Some funds may not be available
- Fund may be delisted

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/stock_query.md` — Stock prices
