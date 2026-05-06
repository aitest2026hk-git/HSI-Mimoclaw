#!/usr/bin/env python3
"""
Multi-Stock 蔡森 (Cai Sen) Analysis with OpenRouter Integration
Analyzes multiple stocks with 6+ month chart period
Uploads results to Google Drive
"""

import json
import os
import urllib.request
import ssl
from datetime import datetime, timedelta
from typing import Dict, List
import csv

# Stock list for analysis
STOCKS_TO_ANALYZE = [
    {'code': '03690.HK', 'name': 'Meituan (美團)', 'sector': 'Consumer'},
    {'code': '00916.HK', 'name': 'Longyuan Power (龍源電力)', 'sector': 'Energy'},
    {'code': '00020.HK', 'name': 'Sensetime (商湯)', 'sector': 'Technology'},
    {'code': '02318.HK', 'name': 'Ping An Insurance (平安保險)', 'sector': 'Financials'},
    {'code': '00700.HK', 'name': 'Tencent (騰訊)', 'sector': 'Technology'},
    {'code': '00345.HK', 'name': 'Vitasoy (維他奶)', 'sector': 'Consumer'},
    {'code': '^HSI', 'name': 'Hang Seng Index (恆生指數)', 'sector': 'Index'},
]

def load_config() -> Dict:
    """Load API configuration"""
    config_path = '/root/.openclaw/workspace/caisen_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def fetch_stooq_data(symbol: str, period_months: int = 8) -> Dict:
    """
    Fetch OHLCV data from Stooq (better coverage for HK stocks)
    Period: 8 months minimum (6+ months requirement)
    """
    # Stooq URL for HK stocks
    # Format: https://stooq.com/q/d/l/?s=0700.HK&d1=YYYYMMDD&d2=YYYYMMDD&i=d
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_months * 30)
    
    # Clean symbol for Stooq (remove ^ for indices)
    stooq_symbol = symbol.replace('^', '')
    
    url = f"https://stooq.com/q/d/l/?s={stooq_symbol}&d1={start_date.strftime('%Y%m%d')}&d2={end_date.strftime('%Y%m%d')}&i=d"
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'},
            method='GET'
        )
        
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            csv_data = response.read().decode('utf-8')
            lines = csv_data.strip().split('\n')
            
            if len(lines) < 2:
                return {'success': False, 'error': 'No data returned'}
            
            # Parse CSV (Date,Open,High,Low,Close,Volume)
            dates = []
            opens = []
            highs = []
            lows = []
            closes = []
            volumes = []
            
            for line in lines[1:]:  # Skip header
                parts = line.split(',')
                if len(parts) >= 6:
                    dates.append(parts[0])
                    try:
                        opens.append(float(parts[1]) if parts[1] else 0)
                        highs.append(float(parts[2]) if parts[2] else 0)
                        lows.append(float(parts[3]) if parts[3] else 0)
                        closes.append(float(parts[4]) if parts[4] else 0)
                        volumes.append(float(parts[5]) if parts[5] else 0)
                    except (ValueError, IndexError):
                        continue
            
            if not closes:
                return {'success': False, 'error': 'No valid data parsed'}
            
            return {
                'symbol': symbol,
                'dates': dates,
                'opens': opens,
                'highs': highs,
                'lows': lows,
                'closes': closes,
                'volumes': volumes,
                'current_price': closes[-1] if closes else 0,
                'success': True,
                'data_points': len(closes)
            }
                
    except Exception as e:
        return {'success': False, 'error': str(e)}


def fetch_yahoo_data(symbol: str, period_months: int = 8) -> Dict:
    """
    Fetch OHLCV data from Yahoo Finance (fallback)
    Period: 8 months minimum (6+ months requirement)
    """
    # Try Stooq first for HK stocks
    result = fetch_stooq_data(symbol, period_months)
    if result.get('success'):
        return result
    
    # Fallback to Yahoo
    config = load_config()
    data_sources = config.get('data_sources', {})
    yahoo_base = data_sources.get('yahoo_finance', 'https://query1.finance.yahoo.com/v8/finance/chart/')
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_months * 30)
    
    url = f"{yahoo_base}{symbol}?period1={int(start_date.timestamp())}&period2={int(end_date.timestamp())}&interval=1d&includePrePost=false"
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}, method='GET')
        
        with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                quote = result.get('quote', {})
                meta = result.get('meta', {})
                
                return {
                    'symbol': symbol,
                    'timestamps': result.get('timestamp', []),
                    'indicators': result.get('indicators', {}),
                    'meta': meta,
                    'current_price': quote.get('regularMarketPrice', meta.get('regularMarketPrice', 0)),
                    'success': True
                }
            else:
                return {'success': False, 'error': 'No data returned'}
                
    except Exception as e:
        return {'success': False, 'error': str(e)}


def analyze_with_openrouter(stock_data: Dict, stock_info: Dict) -> Dict:
    """
    Send analysis to OpenRouter LLM for 蔡森 methodology interpretation
    """
    config = load_config()
    openrouter_config = config.get('openrouter', config)
    api_key = openrouter_config.get('api_key')
    model = openrouter_config.get('default_model', 'google/gemini-2.0-flash-001')
    
    # Prepare OHLCV data summary
    if not stock_data.get('success'):
        return {'error': stock_data.get('error', 'Unknown error'), 'signal': 'HOLD', 'confidence': 0}
    
    # Handle both Stooq and Yahoo formats
    if 'closes' in stock_data:
        # Stooq format
        closes = stock_data.get('closes', [])
        highs = stock_data.get('highs', [])
        lows = stock_data.get('lows', [])
        volumes = stock_data.get('volumes', [])
    else:
        # Yahoo format
        indicators = stock_data.get('indicators', {})
        quote = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
        closes = quote.get('close', [])
        highs = quote.get('high', [])
        lows = quote.get('low', [])
        volumes = quote.get('volume', [])
    
    # Filter out None values from volumes
    volumes = [v if v is not None else 0 for v in volumes] if volumes else []
    
    if not closes or len(closes) < 30:
        return {'error': 'Insufficient data', 'signal': 'HOLD', 'confidence': 0}
    
    # Calculate basic metrics
    current_price = closes[-1]
    price_20d_ago = closes[-20] if len(closes) >= 20 else closes[0]
    price_60d_ago = closes[-60] if len(closes) >= 60 else closes[0]
    
    change_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100 if price_20d_ago else 0
    change_60d = ((current_price - price_60d_ago) / price_60d_ago) * 100 if price_60d_ago else 0
    
    # Volume analysis
    valid_volumes = [v for v in volumes if v and v > 0]
    if len(valid_volumes) >= 20:
        avg_volume_20d = sum(valid_volumes[-20:]) / 20
    elif valid_volumes:
        avg_volume_20d = sum(valid_volumes) / len(valid_volumes)
    else:
        avg_volume_20d = 1
    
    current_volume = volumes[-1] if volumes and volumes[-1] else 0
    volume_ratio = current_volume / avg_volume_20d if avg_volume_20d else 1
    
    # High/Low range
    period_high = max(highs) if highs else current_price
    period_low = min(lows) if lows else current_price
    position_in_range = ((current_price - period_low) / (period_high - period_low)) * 100 if period_high != period_low else 50
    
    # Prepare prompt for 蔡森 analysis
    prompt = f"""你是一位專業的蔡森分析法專家。請根據以下數據進行分析：

股票：{stock_info['name']} ({stock_info['code']})
板塊：{stock_info['sector']}

【價格數據】
- 當前價格：{current_price:.2f}
- 20 日漲跌幅：{change_20d:+.2f}%
- 60 日漲跌幅：{change_60d:+.2f}%
- 期間最高：{period_high:.2f}
- 期間最低：{period_low:.2f}
- 當前位置：{position_in_range:.1f}% (0%=最低，100%=最高)

【成交量分析】
- 當前成交量：{current_volume:,.0f}
- 20 日平均成交量：{avg_volume_20d:,.0f}
- 量比：{volume_ratio:.2f}x

【蔡森分析法要求】
請根據蔡森的「量在價先，型態大於指標」原則，分析：
1. 當前形態（破底翻、假突破、突破點等）
2. 量價關係（量價齊揚、量價背離等）
3. 進場點、止損點、目標價
4. 信號（BUY/HOLD/SELL）及信心度（0-100%）
5. 簡短評論（50 字以內）

請用 JSON 格式回覆：
{{
    "signal": "BUY/HOLD/SELL",
    "confidence": 0-100,
    "pattern": "形態名稱",
    "volume_status": "量價關係",
    "entry_price": 進場價,
    "stop_loss": 止損價,
    "target_price": 目標價,
    "comment": "簡短評論"
}}
"""
    
    messages = [
        {"role": "system", "content": "你是一位專業的蔡森分析法專家，專注於量價關係和形態分析。"},
        {"role": "user", "content": prompt}
    ]
    
    # Call OpenRouter API
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    url = f"{openrouter_config.get('base_url', 'https://openrouter.ai/api/v1')}/chat/completions"
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 500,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/caisen-trading",
        "X-Title": "CaiSen Multi-Stock Analysis"
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                try:
                    analysis = json.loads(content)
                    analysis['symbol'] = stock_info['code']
                    analysis['name'] = stock_info['name']
                    analysis['timestamp'] = datetime.now().isoformat()
                    return analysis
                except json.JSONDecodeError:
                    return {
                        'symbol': stock_info['code'],
                        'name': stock_info['name'],
                        'signal': 'HOLD',
                        'confidence': 50,
                        'comment': content[:200] if content else 'Analysis failed',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                return {'error': 'No response from API', 'signal': 'HOLD', 'confidence': 0}
                
    except Exception as e:
        return {'error': str(e), 'signal': 'HOLD', 'confidence': 0}


def generate_summary_report(results: List[Dict], output_dir: str) -> str:
    """Generate a summary report in markdown format"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    report = f"""# 蔡森多股票分析報告 | Cai Sen Multi-Stock Analysis

**生成時間 Generated:** {timestamp}  
**分析股票數量 Stocks Analyzed:** {len(results)}  
**分析方法 Methodology:** 蔡森分析法 (量在價先，型態大於指標)

---

## 📊 信號總結 | Signal Summary

| 股票 | 名稱 | 信號 | 信心度 | 形態 | 量價關係 |
|------|------|------|--------|------|----------|
"""
    
    for r in results:
        signal_emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(r.get('signal', 'HOLD'), '⚠️')
        report += f"| {r.get('symbol', 'N/A')} | {r.get('name', 'N/A')} | {signal_emoji} {r.get('signal', 'N/A')} | {r.get('confidence', 0)}% | {r.get('pattern', 'N/A')} | {r.get('volume_status', 'N/A')} |\n"
    
    report += f"""
---

## 📈 詳細分析 | Detailed Analysis

"""
    
    for r in results:
        report += f"""### {r.get('name', 'Unknown')} ({r.get('symbol', 'N/A')})

- **信號 Signal:** {r.get('signal', 'N/A')}
- **信心度 Confidence:** {r.get('confidence', 0)}%
- **形態 Pattern:** {r.get('pattern', 'N/A')}
- **量價關係 Volume:** {r.get('volume_status', 'N/A')}
- **進場價 Entry:** {r.get('entry_price', 'N/A')}
- **止損 Stop Loss:** {r.get('stop_loss', 'N/A')}
- **目標價 Target:** {r.get('target_price', 'N/A')}
- **評論 Comment:** {r.get('comment', 'N/A')}

---

"""
    
    # Save report
    report_path = os.path.join(output_dir, 'csagen_analysis_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save JSON results
    json_path = os.path.join(output_dir, 'csagen_analysis_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    csv_path = os.path.join(output_dir, 'csagen_analysis_results.csv')
    if results:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    return report_path


def main():
    """Main execution"""
    print("=" * 80)
    print("蔡森多股票分析 | Cai Sen Multi-Stock Analysis")
    print("=" * 80)
    print(f"開始時間 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析股票 Stocks: {len(STOCKS_TO_ANALYZE)}")
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'/root/.openclaw/workspace/caisen_data/multi_stock_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for i, stock in enumerate(STOCKS_TO_ANALYZE, 1):
        print(f"[{i}/{len(STOCKS_TO_ANALYZE)}] 分析 Analyzing: {stock['name']} ({stock['code']})...")
        
        # Fetch data (8 months for 6+ month requirement)
        print(f"  📥 獲取數據 Fetching data (8 months)...")
        stock_data = fetch_stooq_data(stock['code'], period_months=8)
        
        if not stock_data.get('success'):
            print(f"  ❌ 數據獲取失敗 Data fetch failed: {stock_data.get('error', 'Unknown')}")
            results.append({
                'symbol': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'signal': 'HOLD',
                'confidence': 0,
                'error': stock_data.get('error', 'Data fetch failed')
            })
            continue
        
        # Analyze with OpenRouter
        print(f"  🤖 OpenRouter 分析中 Analyzing...")
        analysis = analyze_with_openrouter(stock_data, stock)
        analysis['sector'] = stock['sector']
        
        # Add current price info
        analysis['current_price'] = stock_data.get('current_price', 0)
        
        results.append(analysis)
        
        signal_emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(analysis.get('signal', 'HOLD'), '⚠️')
        print(f"  ✅ 完成 Done: {signal_emoji} {analysis.get('signal', 'N/A')} ({analysis.get('confidence', 0)}%)")
        print()
    
    # Generate reports
    print("📝 生成報告 Generating reports...")
    report_path = generate_summary_report(results, output_dir)
    print(f"  ✅ 報告已保存 Report saved: {report_path}")
    print(f"  ✅ JSON: {output_dir}/csagen_analysis_results.json")
    print(f"  ✅ CSV: {output_dir}/csagen_analysis_results.csv")
    print()
    
    # Summary
    buy_count = sum(1 for r in results if r.get('signal') == 'BUY')
    sell_count = sum(1 for r in results if r.get('signal') == 'SELL')
    hold_count = sum(1 for r in results if r.get('signal') == 'HOLD')
    
    print("=" * 80)
    print("分析完成 | Analysis Complete")
    print("=" * 80)
    print(f"總計 Total: {len(results)} 股票")
    print(f"🚀 BUY: {buy_count} | ⚠️ HOLD: {hold_count} | 🔴 SELL: {sell_count}")
    print(f"輸出目錄 Output: {output_dir}")
    print()
    
    return output_dir


if __name__ == '__main__':
    main()
