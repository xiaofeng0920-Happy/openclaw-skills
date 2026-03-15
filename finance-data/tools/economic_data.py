#!/usr/bin/env python3
"""
Economic Data: China macroeconomic indicators via akshare.
Supports: GDP, CPI, PMI, Interest Rate, M2, RRR, Bond Yield
Returns: Latest period + 10 historical periods
"""

import sys
import json
from datetime import date, datetime

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

DISCLAIMER = "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"

class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, float) and (o != o):  # NaN check
            return None
        return super().default(o)

def parse_float(value):
    """安全解析浮点数"""
    if value is None or value == '' or value == 'N/A':
        return None
    try:
        f = float(value)
        return None if (f != f) else f  # NaN check
    except (ValueError, TypeError):
        return None

def row_to_dict(row):
    """将 pandas Series 转为字典（避免.get()问题）"""
    return row.to_dict()

def query_gdp():
    """Query GDP data"""
    try:
        data = ak.macro_china_gdp()
        if data is None or len(data) == 0:
            return None
        
        # Latest + 10 history
        latest = row_to_dict(data.iloc[0])
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            r = row_to_dict(row)
            history_list.append({
                "quarter": str(r.get('季度', '')),
                "gdp_total": parse_float(r.get('国内生产总值-绝对值')),
                "gdp_yoy": parse_float(r.get('国内生产总值-同比增长'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "gdp",
            "indicator_name": "国内生产总值",
            "data": {
                "latest": {
                    "quarter": str(latest.get('季度', '')),
                    "gdp_total": parse_float(latest.get('国内生产总值-绝对值')),
                    "gdp_yoy": parse_float(latest.get('国内生产总值-同比增长')),
                    "primary_industry": parse_float(latest.get('第一产业-绝对值')),
                    "secondary_industry": parse_float(latest.get('第二产业-绝对值')),
                    "tertiary_industry": parse_float(latest.get('第三产业-绝对值'))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_cpi():
    """Query CPI data"""
    try:
        data = ak.macro_china_cpi()
        if data is None or len(data) == 0:
            return None
        
        latest = data.iloc[0]
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "month": str(row.get('月份', '')),
                "cpi_yoy": parse_float(row.get('全国-同比增长')),
                "cpi_mom": parse_float(row.get('全国-环比增长'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "cpi",
            "indicator_name": "居民消费价格指数",
            "data": {
                "latest": {
                    "month": str(latest.get('月份', '')),
                    "cpi_index": parse_float(latest.get('全国-当月')),
                    "cpi_yoy": parse_float(latest.get('全国-同比增长')),
                    "cpi_mom": parse_float(latest.get('全国-环比增长'))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_pmi():
    """Query PMI data"""
    try:
        data = ak.macro_china_pmi()
        if data is None or len(data) == 0:
            return None
        
        latest = data.iloc[0]
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "month": str(row.get('月份', '')),
                "manufacturing_pmi": parse_float(row.get('制造业-指数')),
                "non_manufacturing_pmi": parse_float(row.get('非制造业-指数'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "pmi",
            "indicator_name": "采购经理指数",
            "data": {
                "latest": {
                    "month": str(latest.get('月份', '')),
                    "manufacturing_pmi": parse_float(latest.get('制造业-指数')),
                    "non_manufacturing_pmi": parse_float(latest.get('非制造业-指数'))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_interest_rate():
    """Query interest rate data"""
    try:
        data = ak.macro_bank_china_interest_rate()
        if data is None or len(data) == 0:
            return None
        
        latest = data.iloc[0]
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "date": str(row.get('日期', '')),
                "rate": parse_float(row.get('今值'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "rate",
            "indicator_name": "央行利率",
            "data": {
                "latest": {
                    "item": str(latest.get('商品', '')),
                    "date": str(latest.get('日期', '')),
                    "rate": parse_float(latest.get('今值')),
                    "previous": parse_float(latest.get('前值'))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_money_supply():
    """Query money supply (M0, M1, M2) data"""
    try:
        data = ak.macro_china_money_supply()
        if data is None or len(data) == 0:
            return None
        
        latest = data.iloc[0]
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "month": str(row.get('月份', '')),
                "m2_yoy": parse_float(row.get('货币和准货币(M2)-同比增长')),
                "m1_yoy": parse_float(row.get('货币(M1)-同比增长')),
                "m0_yoy": parse_float(row.get('流通中的现金(M0)-同比增长'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "m2",
            "indicator_name": "货币供应量",
            "data": {
                "latest": {
                    "month": str(latest.get('月份', '')),
                    "m2_total": parse_float(latest.get('货币和准货币(M2)-数量(亿元)')),
                    "m2_yoy": parse_float(latest.get('货币和准货币(M2)-同比增长')),
                    "m1_total": parse_float(latest.get('货币(M1)-数量(亿元)')),
                    "m1_yoy": parse_float(latest.get('货币(M1)-同比增长')),
                    "m0_total": parse_float(latest.get('流通中的现金(M0)-数量(亿元)')),
                    "m0_yoy": parse_float(latest.get('流通中的现金(M0)-同比增长'))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_rrr():
    """Query Reserve Requirement Ratio data"""
    try:
        data = ak.macro_china_reserve_requirement_ratio()
        if data is None or len(data) == 0:
            return None
        
        latest = data.iloc[0]
        history = data.iloc[1:11]
        
        history_list = []
        for _, row in history.iterrows():
            history_list.append({
                "announce_date": str(row.get('公布时间', '')),
                "effective_date": str(row.get('生效时间', '')),
                "large_institution_after": parse_float(row.get('大型金融机构-调整后')),
                "small_institution_after": parse_float(row.get('中小金融机构-调整后'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "rrr",
            "indicator_name": "存款准备金率",
            "data": {
                "latest": {
                    "announce_date": str(latest.get('公布时间', '')),
                    "effective_date": str(latest.get('生效时间', '')),
                    "large_institution_before": parse_float(latest.get('大型金融机构-调整前')),
                    "large_institution_after": parse_float(latest.get('大型金融机构-调整后')),
                    "large_institution_change": parse_float(latest.get('大型金融机构-调整幅度')),
                    "small_institution_before": parse_float(latest.get('中小金融机构-调整前')),
                    "small_institution_after": parse_float(latest.get('中小金融机构-调整后')),
                    "small_institution_change": parse_float(latest.get('中小金融机构-调整幅度')),
                    "note": str(latest.get('备注', ''))
                },
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_bond_yield():
    """Query bond yield curve data"""
    try:
        data = ak.bond_china_yield()
        if data is None or len(data) == 0:
            return None
        
        # Filter to most recent date
        latest_date = data.iloc[0]['日期']
        latest_data = data[data['日期'] == latest_date]
        
        if len(latest_data) == 0:
            latest_data = data.iloc[:3]  # Fallback to first 3 rows
        else:
            latest_data = latest_data.iloc[:3]
        
        history_dates = data['日期'].unique()[1:11]
        history_list = []
        for d in history_dates:
            day_data = data[data['日期'] == d]
            if len(day_data) > 0:
                row = day_data.iloc[0]
                history_list.append({
                    "date": str(d),
                    "curve": str(row.get('曲线名称', '')),
                    "yield_1y": parse_float(row.get('1年')),
                    "yield_10y": parse_float(row.get('10年'))
                })
        
        result_list = []
        for _, row in latest_data.iterrows():
            result_list.append({
                "curve": str(row.get('曲线名称', '')),
                "date": str(row.get('日期', '')),
                "yield_3m": parse_float(row.get('3月')),
                "yield_6m": parse_float(row.get('6月')),
                "yield_1y": parse_float(row.get('1年')),
                "yield_3y": parse_float(row.get('3年')),
                "yield_5y": parse_float(row.get('5年')),
                "yield_7y": parse_float(row.get('7年')),
                "yield_10y": parse_float(row.get('10年')),
                "yield_30y": parse_float(row.get('30年'))
            })
        
        return {
            "source": "akshare",
            "type": "economic_data",
            "indicator": "bond",
            "indicator_name": "债券收益率曲线",
            "data": {
                "latest": result_list,
                "history": history_list
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_all_summary():
    """Query summary of all major economic indicators"""
    result = {
        "source": "akshare",
        "type": "economic_data",
        "indicator": "all",
        "indicator_name": "宏观经济数据摘要",
        "data": {},
        "disclaimer": DISCLAIMER
    }
    
    # GDP
    try:
        data = ak.macro_china_gdp()
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            result["data"]["gdp"] = {
                "latest_quarter": str(row.get('季度', '')),
                "gdp_yoy": parse_float(row.get('国内生产总值-同比增长'))
            }
    except:
        pass
    
    # CPI
    try:
        data = ak.macro_china_cpi()
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            result["data"]["cpi"] = {
                "latest_month": str(row.get('月份', '')),
                "cpi_yoy": parse_float(row.get('全国-同比增长'))
            }
    except:
        pass
    
    # PMI
    try:
        data = ak.macro_china_pmi()
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            result["data"]["pmi"] = {
                "latest_month": str(row.get('月份', '')),
                "manufacturing_pmi": parse_float(row.get('制造业-指数')),
                "non_manufacturing_pmi": parse_float(row.get('非制造业-指数'))
            }
    except:
        pass
    
    # M2
    try:
        data = ak.macro_china_money_supply()
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            result["data"]["m2"] = {
                "latest_month": str(row.get('月份', '')),
                "m2_total": parse_float(row.get('货币和准货币(M2)-数量(亿元)')),
                "m2_yoy": parse_float(row.get('货币和准货币(M2)-同比增长'))
            }
    except:
        pass
    
    # Interest Rate
    try:
        data = ak.macro_bank_china_interest_rate()
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            result["data"]["rate"] = {
                "item": str(row.get('商品', '')),
                "date": str(row.get('日期', '')),
                "rate": parse_float(row.get('今值'))
            }
    except:
        pass
    
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: economic_data.py <indicator>", file=sys.stderr)
        print("Indicators: gdp, cpi, pmi, rate, m2, rrr, bond, all", file=sys.stderr)
        sys.exit(1)
    
    indicator = sys.argv[1].lower()
    
    indicator_map = {
        'gdp': query_gdp,
        'cpi': query_cpi,
        'pmi': query_pmi,
        'rate': query_interest_rate,
        'm2': query_money_supply,
        'rrr': query_rrr,
        'bond': query_bond_yield,
        'all': query_all_summary
    }
    
    if indicator not in indicator_map:
        print(json.dumps({
            "error": "Unknown indicator",
            "indicator": indicator,
            "available": list(indicator_map.keys())
        }))
        sys.exit(1)
    
    result = indicator_map[indicator]()
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DateEncoder))
    else:
        print(json.dumps({"error": "Data query failed", "indicator": indicator}))
        sys.exit(1)

if __name__ == "__main__":
    main()
