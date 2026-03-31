# Stock News Reference

Query stock news and announcements via akshare.

## When to Use

**Use this tool when you need recent news about a specific stock:**

```
User: "浦发银行最近有什么新闻？"
User: "看看茅台的最新消息"
```

## Usage

```bash
# Query news (default 10 items)
python3 {baseDir}/tools/stock_news.py 600000

# Query specific number of news
python3 {baseDir}/tools/stock_news.py 600519 5
```

## Symbol Format

- **A-shares**: `600000`, `000001`, `300750`
- Note: Only supports A-shares

## Output Example

```bash
python3 {baseDir}/tools/stock_news.py 600000 3
```

```json
{
  "source": "akshare",
  "type": "news",
  "symbol": "600000",
  "name": "600000",
  "data": {
    "news": [
      {
        "title": "浦发银行发布 2025 年年报",
        "source": "东方财富",
        "date": "2026-03-02",
        "url": "https://..."
      }
    ],
    "count": 3
  },
  "update_time": ""
}
```

## Data Fields

- `title`: News title (新闻标题)
- `source`: News source (文章来源)
- `date`: Publish date (发布时间)
- `url`: News link (新闻链接)

## Limitations

- ⚠️ Only supports A-shares
- ⚠️ News API may be unstable
- ⚠️ Some news may not have full content

## Troubleshooting

**"News query failed"**
- Check symbol format (6-digit A-share code)
- News API may be temporarily unavailable
- Retry after a few minutes

**"akshare not found"**
```bash
pip3 install akshare -U
```

## Related

- `references/search_stock.md` — Search for stock codes by name
- `references/stock_query.md` — Query stock prices
- `references/financial_report.md` — Query financial data
