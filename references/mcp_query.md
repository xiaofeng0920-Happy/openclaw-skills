# MCP Query Reference

Query A-share real-time data via MCP public server.

## Server Info

- **URL**: `http://82.156.17.205/cnstock/mcp`
- **Protocol**: streamable-http (SSE)
- **Tools**: `brief`, `medium`, `full`
- **Coverage**: A-shares only (沪深主板)
- **Auth**: None required (free)

## Usage

```bash
# Basic data (price + trading)
python3 {baseDir}/tools/mcp_query.py 600000 brief

# Financial data (PE, PB, revenue, profit)
python3 {baseDir}/tools/mcp_query.py 600519 medium

# Full data (all + technical indicators)
python3 {baseDir}/tools/mcp_query.py 600000 full
```

## Symbol Format

- `600000` → auto-converted to `SH600000`
- `000001` → auto-converted to `SZ000001`
- `300750` → auto-converted to `SZ300750`
- `SH600000` → used as-is

## Output Example

```json
{
  "source": "mcp",
  "type": "stock",
  "symbol": "SH600000",
  "name": "浦发银行",
  "data": {
    "price": 9.68,
    "change_pct": -0.41,
    "pe_ratio": 6.71,
    "pb_ratio": 0.43,
    "roe": 5.54
  },
  "update_time": "2026-03-02"
}
```

## Data Fields

### Price Data (brief)
- `price`: Current price
- `change_pct`: Percentage change
- `volume`: Trading volume
- `turnover`: Trading value

### Financial Data (medium)
- `pe_ratio`: P/E ratio
- `pb_ratio`: P/B ratio
- `roe`: Return on equity
- `revenue`: Annual revenue
- `net_profit`: Annual net profit

### Technical Indicators (full)
- KDJ, MACD, RSI, Bollinger Bands
- Moving averages (MA5, MA10, MA30, etc.)

## MCP Protocol Details

### List Available Tools

```bash
curl -X POST "http://82.156.17.205/cnstock/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Call a Tool

```bash
curl -X POST "http://82.156.17.205/cnstock/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc":"2.0",
    "method":"tools/call",
    "params":{"name":"brief","arguments":{"symbol":"SH600000"}},
    "id":1
  }'
```

## Troubleshooting

**"MCP connection failed"**
- Check network connectivity
- Server may be temporarily down
- Falls back to akshare automatically

**"Symbol not found"**
- Ensure A-share format (6xxxxx, 0xxxxx, 3xxxxx)
- MCP only supports A-shares (not HK/US)

**"Timeout"**
- Default timeout: 10 seconds
- Server may be under heavy load
- Retry or use akshare fallback

## Related

- `references/stock_query.md` — Global stocks via akshare
- `references/financial_report.md` — Detailed financial statements
