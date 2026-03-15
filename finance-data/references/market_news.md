# Market News Reference

Query real-time market news from Caixin (财新) and policy news from CCTV.

## When to Use

**Use this tool when you need:**

- Latest market dynamics and trends
- Real-time financial news
- Policy announcements and interpretations
- Stock market analysis

```
User: "最近有什么市场消息"
User: "看看今天的财经新闻"
User: "有什么最新的政策动态"
```

## Usage

### Direct Script Usage

```bash
# Market news from Caixin (default 20 items)
python3 {baseDir}/tools/market_news.py

# Market news with custom limit
python3 {baseDir}/tools/market_news.py --limit 30

# Policy news from CCTV
python3 {baseDir}/tools/market_news.py --policy

# Policy news with custom limit
python3 {baseDir}/tools/market_news.py --policy --limit 15
```

### Via query.sh (Recommended)

```bash
# Market news (default 20 items)
{baseDir}/tools/query.sh market-news

# Market news (custom limit)
{baseDir}/tools/query.sh market-news 30

# Policy news (CCTV)
{baseDir}/tools/query.sh market-news --policy

# Policy news (custom limit)
{baseDir}/tools/query.sh market-news --policy 15
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--policy` | flag | - | Query policy news from CCTV (default: market news from Caixin) |
| `--limit` | int | 20 | Number of news items to return (1-100) |

## Data Fields

### Market News (Caixin)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `tag` | string | News category/tag | 市场动态/权益周观察 |
| `title` | string | News title (first 100 chars) | A 股三大指数早盘探底回升 |
| `summary` | string | Full news summary | 资源周期行业及小盘股领涨... |
| `url` | string | Full news URL | https://database.caixin.com/... |
| `date` | string | Publication date | 2026-03-03 |

### Policy News (CCTV)

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Publication date |
| `title` | string | News title |
| `content` | string | News content (first 500 chars) |

## Output Example

### Market News (Caixin)

```bash
{baseDir}/tools/query.sh market-news 3
```

```json
{
  "source": "stock_news_main_cx",
  "source_name": "财新网",
  "type": "market_news",
  "mode": "market",
  "data": {
    "news": [
      {
        "tag": "市场动态",
        "title": "伊朗战事重新引发了金融市场对通胀的担忧...",
        "summary": "伊朗战事重新引发了金融市场对通胀的担忧，全球债券刚刚取得了自疫情爆发以来最好的年度开局...",
        "url": "https://database.caixin.com/2026-03-03/102418973.html",
        "date": "2026-03-03"
      },
      {
        "tag": "权益周观察",
        "title": "资源周期行业及小盘股领涨，科技成长亦较活跃...",
        "summary": "资源周期行业及小盘股领涨，科技成长亦较活跃，但随着板块轮动和分化加剧周尾回调...",
        "url": "https://database.caixin.com/2026-03-03/102418901.html",
        "date": "2026-03-03"
      }
    ],
    "count": 2
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

### Policy News (CCTV)

```bash
{baseDir}/tools/query.sh market-news --policy 1
```

```json
{
  "source": "news_cctv",
  "source_name": "央视新闻",
  "type": "market_news",
  "mode": "policy",
  "data": {
    "news": [
      {
        "date": "20240424",
        "title": "习近平在重庆考察时强调 进一步全面深化改革开放",
        "content": "中共中央总书记、国家主席、中央军委主席习近平近日在重庆考察时强调..."
      }
    ],
    "count": 1
  },
  "disclaimer": "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
}
```

## Data Sources

| Source | API | Coverage | Update Frequency |
|--------|-----|----------|------------------|
| Caixin (财新) | `stock_news_main_cx()` | Market dynamics, financial news | Real-time |
| CCTV (央视) | `news_cctv()` | Policy news, government announcements | Daily |

## News Categories (Caixin)

| Category | Description |
|----------|-------------|
| 市场动态 | Market dynamics and trends |
| 权益周观察 | Weekly equity market analysis |
| 今日热点 | Today's hot topics |
| 宏观 | Macroeconomic news |
| 金融 | Financial sector news |
| 公司 | Company news |

## Use Cases

### Check today's market news
```bash
{baseDir}/tools/query.sh market-news 10
```

### Check policy announcements
```bash
{baseDir}/tools/query.sh market-news --policy
```

### Get latest 5 market updates
```bash
{baseDir}/tools/query.sh market-news 5
```

## Limitations

- ⚠️ Caixin news requires network access
- ⚠️ Some articles may require subscription for full content
- ⚠️ Policy news (CCTV) may have slower updates
- ⚠️ CCTV news content is truncated to 500 characters
- ⚠️ News URLs may expire or require login

## Troubleshooting

**"News query failed"**
- Check network connection
- API may be temporarily unavailable
- Retry after a few minutes

**"akshare not found"**
```bash
pip3 install akshare -U
```

**"No news available"**
- API may be experiencing issues
- Try policy news instead: `--policy`

## Related

- `references/economic_data.md` — Macroeconomic data (GDP, CPI, PMI, etc.)
- `references/stock_news.md` — Stock-specific news
- `references/stock_announcements.md` — Company announcements
