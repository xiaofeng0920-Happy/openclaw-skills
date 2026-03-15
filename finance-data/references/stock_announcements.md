# Stock Announcements Reference

Get company announcements with keyword filtering for important news.

## When to Use

**Use this tool when you need company announcements:**

```
User: "浦发银行最近有什么公告"
User: "腾讯有没有发布财报公告"
User: "看看茅台的重要公告"
```

## Usage

```bash
# A-share, last 3 days
python3 {baseDir}/tools/stock_announcements.py 600000 3

# HK stock, last 7 days, important only
python3 {baseDir}/tools/stock_announcements.py HK00700 7 true

# Default (3 days, all announcements)
python3 {baseDir}/tools/stock_announcements.py 600519
```

## Important Keywords

The tool filters announcements based on these keywords:

### Performance (业绩类)
- 业绩，财报，盈利，亏损，收益，收入，净利润
- 中期，全年，季度

### Assets (资产类)
- 收购，出售，资产，并购，重组，剥离

### Equity (股权类)
- 股权，股份，配股，供股，回购
- 增持，减持，主要股东

### Dividends (分红类)
- 分红，派息，股息，派付

### Operations (经营类)
- 合同，中标，订单，重大
- 诉讼，仲裁，处罚

### Personnel (人事类)
- 董事，高管，辞职，委任
- 主席，CEO, 总裁

### Other (其他)
- 停牌，复牌，澄清，警告
- 风险，评级，目标价

## Output Example

```bash
python3 {baseDir}/tools/stock_announcements.py 600000 3
```

```json
{
  "symbol": "600000",
  "days": 3,
  "count": 5,
  "announcements": [
    {
      "title": "浦发银行 2025 年年度报告",
      "date": "2026-03-01",
      "source": "东方财富",
      "url": "http://...",
      "type": "general",
      "important": true
    },
    {
      "title": "浦发银行董事会决议公告",
      "date": "2026-02-28",
      "source": "东方财富",
      "url": "http://...",
      "type": "general",
      "important": true
    }
  ],
  "note": "Use query.sh news <symbol> for stock news"
}
```

## Use Cases

### Check recent announcements
```bash
# Last 3 days
python3 {baseDir}/tools/stock_announcements.py 600519 3
```

### Check important announcements only
```bash
# Last 7 days, important only
python3 {baseDir}/tools/stock_announcements.py HK00700 7 true
```

### Before earnings season
```bash
# Check for earnings announcements
python3 {baseDir}/tools/stock_announcements.py 600000 30
```

## Data Sources

| Market | Source | Status |
|--------|--------|--------|
| A-shares | 东方财富 (eastmoney) | ✅ |
| HK stocks | 阿思达克 (aastocks) | ⚠️ Basic |

## Performance

| Market | Speed | Coverage |
|--------|-------|----------|
| A-shares | ⚡️ Fast (3-5s) | ✅ Good |
| HK stocks | ⚡️ Fast (3-5s) | ⚠️ Basic |

## Troubleshooting

**"Failed to get announcements"**
- Check symbol format (6-digit for A-shares, HK + 5-digit for HK stocks)
- Market may be closed (weekend/holiday)
- No announcements in the specified period

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/stock_news.md` — Query stock news
- `references/get_stock_info.md` — Get comprehensive stock info
- `references/financial_report.md` — Query financial data
