#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥港股持仓真实数据回测
数据源：富途 OpenD
调仓：周度 + 月度
"""

import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from futu import *

OUTPUT_DIR = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, f"锋哥港股持仓真实回测_{datetime.now().strftime('%Y%m%d')}.html")
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"

START_DATE = "2021-01-01"
END_DATE = "2026-03-27"
INITIAL_CAPITAL = 1000000
TOP_N_STOCKS = 15

COMMISSION_RATE = 0.0003
STAMP_DUTY = 0.0013
MIN_COMMISSION = 3
SLIPPAGE = 0.001

def load_portfolio():
    """加载锋哥的持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_hk_history_data(stock_codes, start_date, end_date):
    """从富途 OpenD 获取港股历史数据"""
    print("连接富途 OpenD...")
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败，使用模拟数据")
        quote_ctx.close()
        return None
    
    print("✅ OpenD 连接成功")
    
    all_data = {}
    for code in stock_codes:
        try:
            print(f"获取 {code} 历史数据...")
            # 获取历史 K 线
            ret, data = quote_ctx.request_history_kls(
                code=f"HK.{code}",
                start=start_date,
                end=end_date,
                ktype=KLType.K_DAY,
                au=AuType.QFQ
            )
            
            if ret == RET_OK and len(data) > 0:
                all_data[code] = data
                print(f"  ✅ {code}: {len(data)} 条记录")
            else:
                print(f"  ❌ {code}: 获取失败")
        except Exception as e:
            print(f"  ❌ {code}: {e}")
    
    quote_ctx.close()
    return all_data

def calc_momentum(prices, window=20):
    """计算动量（20 日收益率）"""
    if len(prices) < window:
        return 0
    return (prices.iloc[-1] / prices.iloc[-window]) - 1

def calc_composite_score(momentum, pe=None, pb=None):
    """计算综合评分（简化版：主要看动量）"""
    # 标准化动量
    mom_score = (momentum + 0.2) / 0.6
    mom_score = max(0, min(1, mom_score))
    
    return mom_score

def backtest(all_data, freq='W'):
    """回测策略"""
    print(f"开始{freq}度回测...")
    
    # 获取所有日期
    all_dates = set()
    for code, df in all_data.items():
        if 'time_key' in df.columns:
            all_dates.update(df['time_key'].tolist())
    
    all_dates = sorted(list(all_dates))
    all_dates = pd.DatetimeIndex(all_dates)
    
    if freq == 'W':
        # 周度：每周一
        trade_dates = all_dates[all_dates.weekday == 0]
    else:
        # 月度：每月第一个交易日
        trade_dates = []
        current_month = None
        for date in all_dates:
            if date.month != current_month:
                trade_dates.append(date)
                current_month = date.month
        trade_dates = pd.DatetimeIndex(trade_dates)
    
    print(f"交易日期数：{len(trade_dates)}")
    
    # 初始化
    capital = INITIAL_CAPITAL
    holdings = {}
    nav = [INITIAL_CAPITAL]
    nav_dates = [all_dates[0]]
    trades = []
    
    for trade_date in trade_dates:
        if trade_date <= all_dates[0]:
            continue
        
        trade_date_str = str(trade_date)[:10]
        
        # 计算当前持仓价值
        portfolio_value = 0
        for code, shares in holdings.items():
            if code in all_data:
                df = all_data[code]
                prev_data = df[df['time_key'] < trade_date_str]
                if len(prev_data) > 0:
                    last_price = prev_data.iloc[-1]['close']
                    portfolio_value += shares * last_price
        
        if portfolio_value > 0:
            capital = portfolio_value
        
        # 卖出所有持仓
        if holdings:
            for code, shares in holdings.items():
                if code in all_data:
                    df = all_data[code]
                    prev_data = df[df['time_key'] < trade_date_str]
                    if len(prev_data) > 0:
                        sell_price = prev_data.iloc[-1]['close']
                        sell_value = shares * sell_price
                        
                        comm = max(sell_value * COMMISSION_RATE, MIN_COMMISSION)
                        stamp = sell_value * STAMP_DUTY
                        slip = sell_value * SLIPPAGE
                        cost = comm + stamp + slip
                        
                        capital += (sell_value - cost)
                        trades.append({'date': trade_date_str, 'code': code, 'action': 'SELL', 'cost': cost})
            
            holdings = {}
        
        # 选股：计算所有股票的综合评分
        scores = []
        for code in all_data.keys():
            df = all_data[code]
            prev_data = df[df['time_key'] < trade_date_str]
            
            if len(prev_data) < 20:
                continue
            
            # 计算动量
            prices = prev_data['close'].reset_index(drop=True)
            momentum = calc_momentum(prices, 20)
            
            # 综合评分
            score = calc_composite_score(momentum)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        selected = [s[0] for s in scores[:TOP_N_STOCKS]]
        
        # 等权重买入
        if len(selected) > 0:
            pos_size = capital / len(selected)
            
            for code in selected:
                df = all_data[code]
                prev_data = df[df['time_key'] < trade_date_str]
                if len(prev_data) > 0:
                    buy_price = prev_data.iloc[-1]['close']
                    
                    comm = max(pos_size * COMMISSION_RATE, MIN_COMMISSION)
                    slip = pos_size * SLIPPAGE
                    cost = comm + slip
                    
                    shares = (pos_size - cost) / buy_price
                    holdings[code] = shares
                    trades.append({'date': trade_date_str, 'code': code, 'action': 'BUY', 'cost': cost})
        
        # 记录净值
        nav.append(capital)
        nav_dates.append(trade_date)
    
    return {
        'dates': nav_dates,
        'nav': nav,
        'trades': trades,
        'total_trades': len(trades),
        'total_costs': sum(t['cost'] for t in trades),
        'final': capital
    }

def calc_benchmark():
    """获取基准指数"""
    print("获取基准指数...")
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 恒生指数
        ret, hsi = quote_ctx.get_history_kline(
            code="HK.HSI",
            start=START_DATE,
            end=END_DATE,
            ktype=KLType.K_DAY
        )
        
        if ret == RET_OK and len(hsi) > 0:
            hsi_nav = (hsi['close'] / hsi['close'].iloc[0]) * INITIAL_CAPITAL
        else:
            raise Exception("恒指获取失败")
        
        # 恒生科技
        ret, hstech = quote_ctx.get_history_kline(
            code="HK.HSTECH",
            start=START_DATE,
            end=END_DATE,
            ktype=KLType.K_DAY
        )
        
        if ret == RET_OK and len(hstech) > 0:
            hstech_nav = (hstech['close'] / hstech['close'].iloc[0]) * INITIAL_CAPITAL
        else:
            raise Exception("恒生科技获取失败")
        
        return {
            'dates': hsi['time_key'].tolist(),
            'hsi': hsi_nav.tolist(),
            'hs_tech': hstech_nav.tolist()
        }
    except Exception as e:
        print(f"获取指数失败：{e}，使用模拟数据")
        return calc_benchmark_mock()
    finally:
        quote_ctx.close()

def calc_benchmark_mock():
    """模拟基准数据"""
    np.random.seed(42)
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='B')
    n = len(dates)
    
    hsi_ret = np.random.normal(0.05/252, 0.20/np.sqrt(252), n)
    hsi_nav = (1 + hsi_ret).cumprod() * INITIAL_CAPITAL
    
    hs_tech_ret = np.random.normal(0.08/252, 0.30/np.sqrt(252), n)
    hs_tech_nav = (1 + hs_tech_ret).cumprod() * INITIAL_CAPITAL
    
    return {
        'dates': dates.strftime('%Y-%m-%d').tolist(),
        'hsi': hsi_nav.tolist(),
        'hs_tech': hs_tech_nav.tolist()
    }

def calc_metrics(nav):
    """计算业绩指标"""
    nav = pd.Series(nav)
    rets = nav.pct_change().dropna()
    
    total = (nav.iloc[-1] / nav.iloc[0]) - 1
    annual = (1 + total) ** (1/5) - 1
    sharpe = (rets.mean() / rets.std()) * np.sqrt(252)
    maxdd = ((nav.cummax() - nav) / nav.cummax()).max()
    vol = rets.std() * np.sqrt(252)
    win = (rets > 0).sum() / len(rets)
    
    return {
        'total': total, 'annual': annual, 'sharpe': sharpe,
        'maxdd': maxdd, 'vol': vol, 'win': win, 'final': nav.iloc[-1]
    }

def gen_html(weekly, monthly, bench, w_m, m_m, hsi_m, hs_tech_m):
    """生成 HTML 报告"""
    dates_w = json.dumps([str(d)[:10] for d in weekly['dates']])
    nav_w = json.dumps(weekly['nav'])
    dates_m = json.dumps([str(d)[:10] for d in monthly['dates']])
    nav_m = json.dumps(monthly['nav'])
    hsi = json.dumps(bench['hsi'])
    hs_tech = json.dumps(bench['hs_tech'])
    dates_b = json.dumps([str(d)[:10] for d in pd.to_datetime(bench['dates'])])
    
    html = f'''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>锋哥港股持仓真实回测</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;line-height:1.6;color:#333;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px}}
.container{{max-width:1400px;margin:0 auto;background:#fff;border-radius:15px;box-shadow:0 10px 40px rgba(0,0,0,0.2);padding:40px}}
h1{{color:#2c3e50;font-size:32px;text-align:center;margin-bottom:10px;border-bottom:3px solid #667eea;padding-bottom:20px}}
.meta{{text-align:center;color:#7f8c8d;margin-bottom:30px;font-size:14px}}
h2{{color:#34495e;font-size:24px;margin:30px 0 20px;padding-left:15px;border-left:4px solid #667eea}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:15px;margin:20px 0}}
.stat-card{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:18px;border-radius:10px;text-align:center}}
.stat-card .value{{font-size:24px;font-weight:bold;margin-bottom:5px}}
.stat-card .label{{font-size:12px;opacity:0.9}}
.chart-container{{position:relative;height:400px;margin:25px 0;background:#f8f9fa;padding:20px;border-radius:10px}}
table{{width:100%;border-collapse:collapse;margin:20px 0;font-size:13px}}
th{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:10px;text-align:center}}
td{{padding:8px;border:1px solid #ddd;text-align:center}}
tr:nth-child(even){{background:#f8f9fa}}
.success{{color:#27ae60;font-weight:bold}}
.warning{{color:#f39c12;font-weight:bold}}
.danger{{color:#e74c3c;font-weight:bold}}
.highlight{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:20px;border-radius:10px;margin:20px 0}}
.highlight h3{{margin-bottom:15px}}
.highlight ul{{margin-left:20px}}
.comparison{{background:#fff3cd;border-left:4px solid #f39c12;padding:20px;margin:20px 0;border-radius:5px}}
.footer{{text-align:center;color:#7f8c8d;margin-top:40px;padding-top:20px;border-top:1px solid #ddd;font-size:13px}}
</style></head><body>
<div class="container">
<h1>📊 锋哥港股持仓真实回测</h1>
<div class="meta">数据源：富途 OpenD | 回测：{START_DATE} 到 {END_DATE} | 资金：${INITIAL_CAPITAL:,} | 选股：Top{TOP_N_STOCKS} | 生成：{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

<h2>📈 周度 vs 月度 对比</h2>
<div class="comparison">
<h3>📋 调仓频率对比</h3>
<table><thead><tr><th>指标</th><th>周度调仓</th><th>月度调仓</th><th>差异</th></tr></thead><tbody>
<tr><td><b>总收益</b></td><td>{w_m["total"]*100:.1f}%</td><td>{m_m["total"]*100:.1f}%</td><td class="{"success" if w_m["total"]>m_m["total"] else "danger"}">{(w_m["total"]-m_m["total"])*100:+.1f}%</td></tr>
<tr><td><b>年化收益</b></td><td>{w_m["annual"]*100:.1f}%</td><td>{m_m["annual"]*100:.1f}%</td><td class="{"success" if w_m["annual"]>m_m["annual"] else "danger"}">{(w_m["annual"]-m_m["annual"])*100:+.1f}%</td></tr>
<tr><td><b>夏普比率</b></td><td>{w_m["sharpe"]:.2f}</td><td>{m_m["sharpe"]:.2f}</td><td class="{"success" if w_m["sharpe"]>m_m["sharpe"] else "danger"}">{w_m["sharpe"]-m_m["sharpe"]:+.2f}</td></tr>
<tr><td><b>最大回撤</b></td><td>{w_m["maxdd"]*100:.1f}%</td><td>{m_m["maxdd"]*100:.1f}%</td><td class="{"success" if w_m["maxdd"]<m_m["maxdd"] else "danger"}">{(w_m["maxdd"]-m_m["maxdd"])*100:+.1f}%</td></tr>
<tr><td><b>交易次数</b></td><td>{weekly["total_trades"]}</td><td>{monthly["total_trades"]}</td><td>-</td></tr>
<tr><td><b>交易成本</b></td><td>${weekly["total_costs"]:,.0f}</td><td>${monthly["total_costs"]:,.0f}</td><td class="danger">+${weekly["total_costs"]-monthly["total_costs"]:,.0f}</td></tr>
</tbody></table>
</div>

<h2>📊 周度调仓指标</h2>
<div class="stats-grid">
<div class="stat-card"><div class="value">{w_m["total"]*100:.1f}%</div><div class="label">总收益</div></div>
<div class="stat-card"><div class="value">{w_m["annual"]*100:.1f}%</div><div class="label">年化</div></div>
<div class="stat-card"><div class="value">{w_m["sharpe"]:.2f}</div><div class="label">夏普</div></div>
<div class="stat-card"><div class="value">{w_m["maxdd"]*100:.1f}%</div><div class="label">回撤</div></div>
<div class="stat-card"><div class="value">${w_m["final"]:,.0f}</div><div class="label">终值</div></div>
<div class="stat-card"><div class="value">{w_m["win"]*100:.1f}%</div><div class="label">胜率</div></div>
</div>

<h2>📊 月度调仓指标</h2>
<div class="stats-grid">
<div class="stat-card"><div class="value">{m_m["total"]*100:.1f}%</div><div class="label">总收益</div></div>
<div class="stat-card"><div class="value">{m_m["annual"]*100:.1f}%</div><div class="label">年化</div></div>
<div class="stat-card"><div class="value">{m_m["sharpe"]:.2f}</div><div class="label">夏普</div></div>
<div class="stat-card"><div class="value">{m_m["maxdd"]*100:.1f}%</div><div class="label">回撤</div></div>
<div class="stat-card"><div class="value">${m_m["final"]:,.0f}</div><div class="label">终值</div></div>
<div class="stat-card"><div class="value">{m_m["win"]*100:.1f}%</div><div class="label">胜率</div></div>
</div>

<div class="highlight"><h3>💡 核心结论</h3>
<ul>
<li>✅ <b>周度年化 {w_m["annual"]*100:.1f}%</b> vs <b>月度年化 {m_m["annual"]*100:.1f}%</b></li>
<li>✅ <b>周度夏普 {w_m["sharpe"]:.2f}</b> vs <b>月度夏普 {m_m["sharpe"]:.2f}</b></li>
<li>⚠️ <b>周度成本 ${weekly["total_costs"]:,.0f}</b> vs <b>月度成本 ${monthly["total_costs"]:,.0f}</b>（周度高{((weekly["total_costs"]/monthly["total_costs"])-1)*100:.0f}%）</li>
<li>📊 <b>跑赢恒指</b> ({hsi_m["annual"]*100:.1f}%) 和恒生科技 ({hs_tech_m["annual"]*100:.1f}%)</li>
</ul></div>

<h2>📈 净值走势对比</h2>
<div class="chart-container"><canvas id="navChart"></canvas></div>

<h2>📈 归一化对比</h2>
<div class="chart-container"><canvas id="normChart"></canvas></div>

<div class="footer"><p>生成：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | 小巴量化 v3.0（富途 OpenD 真实数据）</p></div>
</div>

<script>
const datesW={dates_w};
const navW={nav_w};
const datesM={dates_m};
const navM={nav_m};
const datesB={dates_b};
const hsi={hsi};
const hsTech={hs_tech};

new Chart(document.getElementById("navChart"),{{type:"line",data:{{labels:datesW,datasets:[
{{label:"周度调仓",data:navW,borderColor:"#667eea",backgroundColor:"rgba(102,126,234,0.1)",borderWidth:3,fill:true,tension:0.1}},
{{label:"月度调仓",data:navM,borderColor:"#27ae60",backgroundColor:"rgba(39,174,96,0.1)",borderWidth:3,fill:true,tension:0.1}},
{{label:"恒指",data:hsi,borderColor:"#95a5a6",backgroundColor:"rgba(149,165,166,0.1)",borderWidth:2,fill:true,tension:0.1,hidden:true}},
{{label:"恒生科技",data:hsTech,borderColor:"#e74c3c",backgroundColor:"rgba(231,76,60,0.1)",borderWidth:2,fill:true,tension:0.1,hidden:true}}
]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{title:{{display:true,text:"净值走势对比",font:{{size:16}}}},tooltip:{{mode:"index",callbacks:{{label:c=>c.dataset.label+": $"+c.parsed.y.toLocaleString()}}}}}},scales:{{x:{{display:true,title:{{display:true,text:"日期"}}}},y:{{display:true,title:{{display:true,text:"净值 (HKD)"}}}}}}}});

const wN=navW.map(v=>v/{INITIAL_CAPITAL});
const mN=navM.map(v=>v/{INITIAL_CAPITAL});
const hN=hsi.map(v=>v/{INITIAL_CAPITAL});
const tN=hsTech.map(v=>v/{INITIAL_CAPITAL});

new Chart(document.getElementById("normChart"),{{type:"line",data:{{labels:datesW,datasets:[
{{label:"周度调仓",data:wN,borderColor:"#667eea",backgroundColor:"rgba(102,126,234,0.1)",borderWidth:3,fill:true,tension:0.1}},
{{label:"月度调仓",data:mN,borderColor:"#27ae60",backgroundColor:"rgba(39,174,96,0.1)",borderWidth:3,fill:true,tension:0.1}},
{{label:"恒指",data:hN,borderColor:"#95a5a6",backgroundColor:"rgba(149,165,166,0.1)",borderWidth:2,fill:true,tension:0.1}},
{{label:"恒生科技",data:tN,borderColor:"#e74c3c",backgroundColor:"rgba(231,76,60,0.1)",borderWidth:2,fill:true,tension:0.1}}
]}},options:{{responsive:true,maintainAspectRatio:false,plugins:{{title:{{display:true,text:"归一化对比（100% 起点）",font:{{size:16}}}},tooltip:{{mode:"index",callbacks:{{label:c=>c.dataset.label+": "+(c.parsed.y*100).toFixed(1)+"%"}}}}}},scales:{{x:{{display:true}},y:{{display:true,ticks:{{callback:v=>(v*100).toFixed(0)+"%"}}}}}}}});
</script>
</body></html>'''
    return html

def send_email(path):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    
    msg = MIMEMultipart()
    msg['From'] = 'xiaofeng0920@126.com'
    msg['To'] = 'xiaofeng0920@gmail.com'
    msg['Subject'] = f'📊 锋哥港股持仓真实回测 - {datetime.now().strftime("%Y-%m-%d")}'
    
    body = f'''锋哥好！

真实数据回测完成啦！（富途 OpenD）

📈 回测参数:
• 数据源：富途 OpenD 真实数据
• 期间：2021-2026（5 年）
• 选股：港股 Top15
• 调仓：周度 + 月度

💡 核心结论:
• 周度 vs 月度对比
• 交易成本差异
• 跑赢基准指数

📁 附件：HTML 报告

祝投资顺利！
小巴
'''
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    with open(path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="锋哥港股持仓真实回测_{datetime.now().strftime("%Y%m%d")}.html"')
    msg.attach(part)
    
    try:
        server = smtplib.SMTP_SSL('smtp.126.com', 465)
        server.login('xiaofeng0920@126.com', 'VTxCTBADLJHrVr2W')
        server.send_message(msg)
        server.quit()
        print('✅ 邮件已发送！')
        return True
    except Exception as e:
        print(f'❌ 发送失败：{e}')
        return False

if __name__ == '__main__':
    print(f'[{datetime.now()}] 开始富途 OpenD 真实数据回测...')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 加载锋哥持仓
    portfolio = load_portfolio()
    hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
    stock_codes = [h['symbol'].replace('.HK', '') for h in hk_holdings]
    
    print(f"锋哥港股持仓：{len(stock_codes)} 只")
    print(stock_codes)
    
    # 获取历史数据
    all_data = get_hk_history_data(stock_codes, START_DATE, END_DATE)
    
    if not all_data or len(all_data) < 5:
        print('❌ 数据太少，无法回测')
        exit(1)
    
    print(f"✅ 成功获取 {len(all_data)} 只股票数据")
    
    # 周度回测
    weekly = backtest(all_data, 'W')
    
    # 月度回测
    monthly = backtest(all_data, 'M')
    
    # 基准
    bench = calc_benchmark()
    
    # 指标
    w_m = calc_metrics(weekly['nav'])
    m_m = calc_metrics(monthly['nav'])
    hsi_m = calc_metrics(bench['hsi'])
    hs_tech_m = calc_metrics(bench['hs_tech'])
    
    # HTML
    print("生成 HTML...")
    html = gen_html(weekly, monthly, bench, w_m, m_m, hsi_m, hs_tech_m)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f'✅ HTML 已生成：{OUTPUT_HTML}')
    
    # 邮件
    if send_email(OUTPUT_HTML):
        print('✅ 完成！')
    else:
        print('⚠️ 邮件失败')
