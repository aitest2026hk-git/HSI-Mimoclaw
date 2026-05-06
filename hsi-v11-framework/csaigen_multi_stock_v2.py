#!/usr/bin/env python3
"""
Multi-Stock 蔡森 (Cai Sen) Analysis v2
Uses local CSV data files + OpenRouter API
Analyzes: 03690, 00916, 00020, 02318, 00700, 00345, HSI
"""

import json
import os
import urllib.request
import ssl
from datetime import datetime
from typing import Dict, List
import csv

# Stock list with local file mappings
STOCKS_TO_ANALYZE = [
    {'code': '03690.HK', 'name': 'Meituan (美團)', 'sector': 'Consumer', 'file': '3690_HK.csv'},
    {'code': '00916.HK', 'name': 'Longyuan Power (龍源電力)', 'sector': 'Energy', 'file': '916_HK.csv'},
    {'code': '00020.HK', 'name': 'Sensetime (商湯)', 'sector': 'Technology', 'file': '20_HK.csv'},
    {'code': '02318.HK', 'name': 'Ping An Insurance (平安保險)', 'sector': 'Financials', 'file': '2318_HK.csv'},
    {'code': '00700.HK', 'name': 'Tencent (騰訊)', 'sector': 'Technology', 'file': '0700_HK_2y.csv'},
    {'code': '00345.HK', 'name': 'Vitasoy (維他奶)', 'sector': 'Consumer', 'file': '345_HK.csv'},
    {'code': '^HSI', 'name': 'Hang Seng Index (恆生指數)', 'sector': 'Index', 'file': 'hsi.csv'},
]

DATA_DIR = '/root/.openclaw/workspace/caisen_data'


def load_config() -> Dict:
    """Load API configuration"""
    config_path = '/root/.openclaw/workspace/caisen_config.json'
    with open(config_path, 'r') as f:
        return json.load(f)


def load_local_csv(filepath: str) -> Dict:
    """Load OHLCV data from local CSV file"""
    full_path = os.path.join(DATA_DIR, filepath)
    
    if not os.path.exists(full_path):
        return {'success': False, 'error': f'File not found: {filepath}'}
    
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle different CSV formats
                if 'Date' in row:
                    dates.append(row['Date'])
                    opens.append(float(row['Open']) if row.get('Open') else 0)
                    highs.append(float(row['High']) if row.get('High') else 0)
                    lows.append(float(row['Low']) if row.get('Low') else 0)
                    closes.append(float(row['Close']) if row.get('Close') else 0)
                    vol_str = row.get('Volume', '0')
                    # Handle volume with B/M/K suffix
                    vol_str = str(vol_str).replace(',', '').replace('B', '000000000').replace('M', '000000').replace('K', '000')
                    try:
                        volumes.append(float(vol_str) if vol_str else 0)
                    except:
                        volumes.append(0)
                elif '日期' in row or 'Date' in str(row):
                    # Chinese format: 日期，收市，開市，高，低，成交量
                    dates.append(row.get('日期', row.get('Date', '')))
                    closes.append(float(row.get('收市', row.get('Close', 0))) if row.get('收市') or row.get('Close') else 0)
                    opens.append(float(row.get('開市', row.get('Open', 0))) if row.get('開市') or row.get('Open') else 0)
                    highs.append(float(row.get('高', row.get('High', 0))) if row.get('高') or row.get('High') else 0)
                    lows.append(float(row.get('低', row.get('Low', 0))) if row.get('低') or row.get('Low') else 0)
                    vol_str = row.get('成交量', row.get('Volume', '0'))
                    volumes.append(float(vol_str) if vol_str else 0)
        
        if not closes:
            return {'success': False, 'error': 'No data parsed'}
        
        # Filter to last 8 months (~240 trading days)
        max_days = min(240, len(closes))
        
        return {
            'success': True,
            'dates': dates[-max_days:],
            'opens': opens[-max_days:],
            'highs': highs[-max_days:],
            'lows': lows[-max_days:],
            'closes': closes[-max_days:],
            'volumes': volumes[-max_days:],
            'current_price': closes[-1],
            'data_points': max_days
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def analyze_with_openrouter(stock_data: Dict, stock_info: Dict) -> Dict:
    """Send analysis to OpenRouter LLM for 蔡森 methodology interpretation"""
    config = load_config()
    openrouter_config = config.get('openrouter', config)
    api_key = openrouter_config.get('api_key')
    model = openrouter_config.get('default_model', 'google/gemini-2.0-flash-001')
    
    if not stock_data.get('success'):
        return {'error': stock_data.get('error', 'Unknown error'), 'signal': 'HOLD', 'confidence': 0}
    
    closes = stock_data.get('closes', [])
    highs = stock_data.get('highs', [])
    lows = stock_data.get('lows', [])
    volumes = stock_data.get('volumes', [])
    
    # Filter None volumes
    volumes = [v if v is not None else 0 for v in volumes]
    
    if not closes or len(closes) < 30:
        return {'error': 'Insufficient data', 'signal': 'HOLD', 'confidence': 0}
    
    # Calculate metrics
    current_price = closes[-1]
    price_20d_ago = closes[-20] if len(closes) >= 20 else closes[0]
    price_60d_ago = closes[-60] if len(closes) >= 60 else closes[0]
    
    change_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100 if price_20d_ago else 0
    change_60d = ((current_price - price_60d_ago) / price_60d_ago) * 100 if price_60d_ago else 0
    
    # Volume analysis
    valid_volumes = [v for v in volumes if v and v > 0]
    avg_volume_20d = sum(valid_volumes[-20:]) / 20 if len(valid_volumes) >= 20 else (sum(valid_volumes) / len(valid_volumes) if valid_volumes else 1)
    current_volume = volumes[-1] if volumes else 0
    volume_ratio = current_volume / avg_volume_20d if avg_volume_20d else 1
    
    # High/Low range
    period_high = max(highs) if highs else current_price
    period_low = min(lows) if lows else current_price
    position_in_range = ((current_price - period_low) / (period_high - period_low)) * 100 if period_high != period_low else 50
    
    # Prepare prompt
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
請根據「量在價先，型態大於指標」原則，分析：
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
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        
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


def generate_reports(results: List[Dict], output_dir: str) -> str:
    """Generate summary reports"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Markdown report
    report = f"""# 蔡森多股票分析報告 | Cai Sen Multi-Stock Analysis

**生成時間 Generated:** {timestamp}  
**分析股票數量 Stocks Analyzed:** {len(results)}  
**分析方法 Methodology:** 蔡森分析法 (量在價先，型態大於指標)  
**數據周期 Data Period:** 6+ months

---

## 📊 信號總結 | Signal Summary

| 股票 | 名稱 | 信號 | 信心度 | 形態 | 量價關係 | 當前價 |
|------|------|------|--------|------|----------|--------|
"""
    
    for r in results:
        signal_emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(r.get('signal', 'HOLD'), '⚠️')
        price = r.get('current_price', 'N/A')
        report += f"| {r.get('symbol', 'N/A')} | {r.get('name', 'N/A')} | {signal_emoji} {r.get('signal', 'N/A')} | {r.get('confidence', 0)}% | {r.get('pattern', 'N/A')} | {r.get('volume_status', 'N/A')} | {price} |\n"
    
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
    
    # Save reports
    report_path = os.path.join(output_dir, 'csagen_analysis_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    json_path = os.path.join(output_dir, 'csagen_analysis_results.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    csv_path = os.path.join(output_dir, 'csagen_analysis_results.csv')
    if results:
        # Use consistent fieldnames
        fieldnames = ['symbol', 'name', 'sector', 'signal', 'confidence', 'pattern', 'volume_status', 
                      'entry_price', 'stop_loss', 'target_price', 'comment', 'current_price', 'error']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
    
    return report_path


def main():
    """Main execution"""
    print("=" * 80)
    print("蔡森多股票分析 v2 | Cai Sen Multi-Stock Analysis v2")
    print("=" * 80)
    print(f"開始時間 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析股票 Stocks: {len(STOCKS_TO_ANALYZE)}")
    print(f"數據源：Local CSV files")
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'/root/.openclaw/workspace/caisen_data/multi_stock_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    success_count = 0
    
    for i, stock in enumerate(STOCKS_TO_ANALYZE, 1):
        print(f"[{i}/{len(STOCKS_TO_ANALYZE)}] 分析 Analyzing: {stock['name']} ({stock['code']})...")
        
        # Load local data
        print(f"  📥 讀取本地數據 Loading local data...")
        stock_data = load_local_csv(stock['file'])
        
        if not stock_data.get('success'):
            print(f"  ❌ 數據載入失敗 Data load failed: {stock_data.get('error', 'Unknown')}")
            results.append({
                'symbol': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'signal': 'HOLD',
                'confidence': 0,
                'error': stock_data.get('error', 'Data load failed')
            })
            continue
        
        print(f"  ✅ 數據載入成功 Loaded {stock_data['data_points']} days")
        
        # Analyze with OpenRouter
        print(f"  🤖 OpenRouter 分析中 Analyzing...")
        analysis = analyze_with_openrouter(stock_data, stock)
        analysis['sector'] = stock['sector']
        analysis['current_price'] = stock_data.get('current_price', 0)
        analysis['data_points'] = stock_data.get('data_points', 0)
        
        results.append(analysis)
        success_count += 1
        
        signal_emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(analysis.get('signal', 'HOLD'), '⚠️')
        print(f"  ✅ 完成 Done: {signal_emoji} {analysis.get('signal', 'N/A')} ({analysis.get('confidence', 0)}%)")
        print()
    
    # Generate reports
    print("📝 生成報告 Generating reports...")
    report_path = generate_reports(results, output_dir)
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
    print(f"成功 Successful: {success_count}/{len(STOCKS_TO_ANALYZE)}")
    print(f"🚀 BUY: {buy_count} | ⚠️ HOLD: {hold_count} | 🔴 SELL: {sell_count}")
    print(f"輸出目錄 Output: {output_dir}")
    print()
    
    return output_dir, results


if __name__ == '__main__':
    main()
