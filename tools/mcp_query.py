#!/usr/bin/env python3
"""
MCP Query: A-share real-time data via public MCP server.
Server: http://82.156.17.205/cnstock/mcp
Tools: brief (price), medium (financials), full (all + technical)
"""

import sys
import json
import re
import subprocess

MCP_URL = "http://82.156.17.205/cnstock/mcp"

def normalize_symbol(symbol):
    symbol = str(symbol).strip()
    if symbol.startswith("SH") or symbol.startswith("SZ"):
        return symbol.upper()
    elif symbol.startswith("6"):
        return "SH" + symbol
    elif symbol.startswith("0") or symbol.startswith("3"):
        return "SZ" + symbol
    return None

def call_mcp_tool(tool_name, args):
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": args},
            "id": 1
        }
        
        cmd = [
            "curl", "-s", "-X", "POST", MCP_URL,
            "-H", "Content-Type: application/json",
            "-H", "Accept: application/json, text/event-stream",
            "-d", json.dumps(payload),
            "--connect-timeout", "5",
            "--max-time", "10"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return None
        
        body = result.stdout
        data_match = re.search(r'data:\s*({.+})', body, re.DOTALL)
        if not data_match:
            return None
        
        data = json.loads(data_match.group(1))
        if "error" in data:
            return None
        
        return data.get("result", {})
    except:
        return None

def parse_text_data(text):
    result = {"symbol": "", "name": "", "date": "", "price_data": {}, "financial_data": {}, "raw_text": text}
    try:
        for line in text.split('\n'):
            line = line.strip()
            if "股票代码:" in line:
                result["symbol"] = line.split(":", 1)[1].strip()
            if "股票名称:" in line:
                result["name"] = line.split(":", 1)[1].strip()
            if "数据日期:" in line:
                result["date"] = line.split(":", 1)[1].strip()
            if "市盈率" in line and "静" in line:
                match = re.search(r'市盈率\(静\):\s*([\d.]+)', line)
                if match:
                    result["financial_data"]["pe_ratio"] = float(match.group(1))
            if "市净率:" in line:
                match = re.search(r'市净率:\s*([\d.]+)', line)
                if match:
                    result["financial_data"]["pb_ratio"] = float(match.group(1))
            if "净资产收益率:" in line:
                match = re.search(r'净资产收益率:\s*([\d.]+)', line)
                if match:
                    result["financial_data"]["roe"] = float(match.group(1))
            if line.startswith("- 当日:") and "最高:" in line:
                match = re.search(r'当日:\s*([\d.]+)', line)
                if match:
                    result["price_data"]["price"] = float(match.group(1))
            if "当日:" in line and "%" in line:
                match = re.search(r'当日:\s*([+-]?[\d.]+)%', line)
                if match:
                    result["price_data"]["change_pct"] = float(match.group(1))
    except:
        pass
    return result

def query_mcp(symbol, depth="brief"):
    normalized = normalize_symbol(symbol)
    if not normalized:
        return None
    
    tool_map = {"brief": "brief", "price": "brief", "medium": "medium", "financial": "medium", "full": "full", "all": "full"}
    tool = tool_map.get(depth, "brief")
    result = call_mcp_tool(tool, {"symbol": normalized})
    
    if not result:
        return None
    
    text_content = ""
    if "content" in result and isinstance(result["content"], list):
        for item in result["content"]:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content = item.get("text", "")
                break
    
    if not text_content:
        return None
    
    parsed = parse_text_data(text_content)
    output = {
        "source": "mcp",
        "type": "stock",
        "symbol": parsed["symbol"] or normalized,
        "name": parsed["name"],
        "data": {},
        "update_time": parsed["date"]
    }
    
    for key in ["price", "change_pct"]:
        if key in parsed["price_data"]:
            output["data"][key] = parsed["price_data"][key]
    for key in ["pe_ratio", "pb_ratio", "roe"]:
        if key in parsed["financial_data"]:
            output["data"][key] = parsed["financial_data"][key]
    
    output["data"]["raw"] = parsed["raw_text"]
    return output

def main():
    if len(sys.argv) < 2:
        print("Usage: mcp_query.py <symbol> [depth]", file=sys.stderr)
        sys.exit(1)
    
    result = query_mcp(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "brief")
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "MCP query failed", "symbol": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
