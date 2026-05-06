#!/usr/bin/env python3
"""
Cai Sen Multi-Stock Analysis - Fallback (No API)
Uses basic technical analysis when OpenRouter API is unavailable
"""

import json
import os
import csv
from datetime import datetime
from typing import Dict, List

STOCKS = [
    {'code': '03690.HK', 'name': 'Meituan (美團)', 'sector': 'Consumer', 'file': '3690_HK.csv'},
    {'code': '00916.HK', 'name': 'Longyuan Power (龍源電力)', 'sector': 'Energy', 'file': '916_HK.csv'},
    {'code': '00020.HK', 'name': 'Sensetime (商湯)', 'sector': 'Technology', 'file': '20_HK.csv'},
    {'code': '02318.HK', 'name': 'Ping An Insurance (平安保險)', 'sector': 'Financials', 'file': '2318_HK.csv'},
    {'code': '00700.HK', 'name': 'Tencent (騰訊)', 'sector': 'Technology', 'file': '0700_HK_2y.csv'},
    {'code': '00345.HK', 'name': 'Vitasoy (維他奶)', 'sector': 'Consumer', 'file': '345_HK.csv'},
    {'code': '^HSI', 'name': 'Hang Seng Index (恆生指數)', 'sector': 'Index', 'file': 'hsi.csv'},
]

DATA_DIR = '/root/.openclaw/workspace/caisen_data'


def load_csv(filepath: str) -> Dict:
    """Load OHLCV data from CSV"""
    full_path = os.path.join(DATA_DIR, filepath)
    
    if not os.path.exists(full_path):
        return {'success': False, 'error': f'File not found: {filepath}'}
    
    dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Date' in row:
                    dates.append(row['Date'])
                    closes.append(float(row['Close']) if row.get('Close') else 0)
                    opens.append(float(row['Open']) if row.get('Open') else 0)
                    highs.append(float(row['High']) if row.get('High') else 0)
                    lows.append(float(row['Low']) if row.get('Low') else 0)
                    volumes.append(float(row.get('Volume', 0)) if row.get('Volume') else 0)
                elif '日期' in row:
                    dates.append(row.get('日期', ''))
                    closes.append(float(row.get('收市', 0)) if row.get('收市') else 0)
                    opens.append(float(row.get('開市', 0)) if row.get('開市') else 0)
                    highs.append(float(row.get('高', 0)) if row.get('高') else 0)
                    lows.append(float(row.get('低', 0)) if row.get('低') else 0)
                    vol_str = str(row.get('成交量', '0'))
                    # Handle B/M/K suffix
                    vol_str = vol_str.replace(',', '').upper()
                    if 'B' in vol_str:
                        vol = float(vol_str.replace('B', '')) * 1_000_000_000
                    elif 'M' in vol_str:
                        vol = float(vol_str.replace('M', '')) * 1_000_000
                    elif 'K' in vol_str:
                        vol = float(vol_str.replace('K', '')) * 1_000
                    else:
                        vol = float(vol_str) if vol_str else 0
                    volumes.append(vol)
        
        if not closes:
            return {'success': False, 'error': 'No data parsed'}
        
        max_days = min(240, len(closes))
        return {
            'success': True,
            'dates': dates[-max_days:],
            'closes': closes[-max_days:],
            'opens': opens[-max_days:],
            'highs': highs[-max_days:],
            'lows': lows[-max_days:],
            'volumes': volumes[-max_days:],
            'current_price': closes[-1],
            'data_points': max_days
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def analyze_stock(data: Dict, stock_info: Dict) -> Dict:
    """Basic technical analysis using Cai Sen principles"""
    if not data.get('success'):
        return {
            'symbol': stock_info['code'],
            'name': stock_info['name'],
            'sector': stock_info['sector'],
            'signal': 'HOLD',
            'confidence': 0,
            'error': data.get('error', 'Unknown')
        }
    
    closes = data['closes']
    highs = data['highs']
    lows = data['lows']
    volumes = data['volumes']
    current_price = data['current_price']
    
    # Calculate metrics
    price_20d_ago = closes[-20] if len(closes) >= 20 else closes[0]
    price_60d_ago = closes[-60] if len(closes) >= 60 else closes[0]
    
    change_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100 if price_20d_ago else 0
    change_60d = ((current_price - price_60d_ago) / price_60d_ago) * 100 if price_60d_ago else 0
    
    # Volume analysis
    valid_volumes = [v for v in volumes if v and v > 0]
    avg_vol_20d = sum(valid_volumes[-20:]) / 20 if len(valid_volumes) >= 20 else (sum(valid_volumes) / len(valid_volumes) if valid_volumes else 1)
    current_vol = volumes[-1] if volumes else 0
    vol_ratio = current_vol / avg_vol_20d if avg_vol_20d else 1
    
    # Price position in range
    period_high = max(highs) if highs else current_price
    period_low = min(lows) if lows else current_price
    position = ((current_price - period_low) / (period_high - period_low)) * 100 if period_high != period_low else 50
    
    # Moving averages
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else current_price
    ma60 = sum(closes[-60:]) / 60 if len(closes) >= 60 else current_price
    
    # Cai Sen pattern detection (simplified)
    pattern = "Consolidation"
    volume_status = "Normal"
    signal = "HOLD"
    confidence = 50
    comment = ""
    
    # Trend detection
    if current_price > ma20 and current_price > ma60:
        trend = "Uptrend"
        if change_20d > 10:
            pattern = "Strong Uptrend"
            volume_status = "Volume confirming" if vol_ratio > 1 else "Low volume rally"
        elif change_20d > 0:
            pattern = "Gradual Rise"
    elif current_price < ma20 and current_price < ma60:
        trend = "Downtrend"
        if change_20d < -10:
            pattern = "Sharp Decline"
        else:
            pattern = "Weakness"
    else:
        trend = "Sideways"
        pattern = "Consolidation"
    
    # Volume analysis
    if vol_ratio > 1.5:
        volume_status = "High Volume"
    elif vol_ratio < 0.7:
        volume_status = "Low Volume"
    
    # Signal generation (Cai Sen principles)
    if trend == "Uptrend" and vol_ratio > 1 and position < 70:
        signal = "BUY"
        confidence = min(75, 50 + int(change_20d))
        comment = f"量價齊揚，上升趨勢中"
    elif trend == "Downtrend" and vol_ratio > 1.2:
        signal = "SELL"
        confidence = min(70, 50 + int(abs(change_20d)))
        comment = f"放量下跌，注意風險"
    elif position < 20 and vol_ratio > 1.5:
        signal = "BUY"
        confidence = 60
        pattern = "破底翻 (Spring)"
        comment = "低位放量，可能反彈"
    elif position > 80 and vol_ratio > 1.5:
        signal = "SELL"
        confidence = 60
        pattern = "假突破 (False Breakout)"
        comment = "高位放量，小心回調"
    else:
        signal = "HOLD"
        confidence = 50
        comment = "觀望為宜"
    
    # Entry/Stop/Target
    entry_price = current_price
    stop_loss = current_price * 0.92 if signal == "BUY" else (current_price * 1.08 if signal == "SELL" else None)
    target_price = current_price * 1.15 if signal == "BUY" else (current_price * 0.85 if signal == "SELL" else None)
    
    return {
        'symbol': stock_info['code'],
        'name': stock_info['name'],
        'sector': stock_info['sector'],
        'signal': signal,
        'confidence': confidence,
        'pattern': pattern,
        'volume_status': volume_status,
        'entry_price': round(entry_price, 2),
        'stop_loss': round(stop_loss, 2) if stop_loss else None,
        'target_price': round(target_price, 2) if target_price else None,
        'comment': comment,
        'current_price': round(current_price, 2),
        'trend': trend,
        'change_20d': round(change_20d, 2),
        'change_60d': round(change_60d, 2),
        'vol_ratio': round(vol_ratio, 2),
        'position_pct': round(position, 1),
        'data_points': data['data_points']
    }


def generate_reports(results: List[Dict], output_dir: str):
    """Generate reports"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Markdown report
    report = f"""# 蔡森多股票分析報告 | Cai Sen Multi-Stock Analysis

**生成時間 Generated:** {timestamp}  
**分析方法 Methodology:** 蔡森分析法 (量在價先，型態大於指標) - Fallback Mode  
**數據周期 Data Period:** 6+ months (240 days)  
**API Status:** OpenRouter unavailable, using technical analysis fallback

---

## 📊 信號總結 | Signal Summary

| 股票 | 名稱 | 信號 | 信心度 | 形態 | 量價 | 現價 | 20 日漲跌 |
|------|------|------|--------|------|------|------|----------|
"""
    
    for r in results:
        emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(r.get('signal', 'HOLD'), '⚠️')
        report += f"| {r.get('symbol', 'N/A')} | {r.get('name', 'N/A')} | {emoji} {r.get('signal', 'N/A')} | {r.get('confidence', 0)}% | {r.get('pattern', 'N/A')} | {r.get('volume_status', 'N/A')} | {r.get('current_price', 'N/A')} | {r.get('change_20d', 0):+.1f}% |\n"
    
    report += f"""
---

## 📈 詳細分析 | Detailed Analysis

"""
    
    for r in results:
        report += f"""### {r.get('name', 'Unknown')} ({r.get('symbol', 'N/A')})

| 項目 | 數值 |
|------|------|
| **信號 Signal** | {r.get('signal', 'N/A')} |
| **信心度 Confidence** | {r.get('confidence', 0)}% |
| **形態 Pattern** | {r.get('pattern', 'N/A')} |
| **量價關係 Volume** | {r.get('volume_status', 'N/A')} |
| **趨勢 Trend** | {r.get('trend', 'N/A')} |
| **現價 Current Price** | {r.get('current_price', 'N/A')} |
| **20 日漲跌 20d Change** | {r.get('change_20d', 0):+.2f}% |
| **60 日漲跌 60d Change** | {r.get('change_60d', 0):+.2f}% |
| **進場價 Entry** | {r.get('entry_price', 'N/A')} |
| **止損 Stop Loss** | {r.get('stop_loss', 'N/A')} |
| **目標價 Target** | {r.get('target_price', 'N/A')} |
| **評論 Comment** | {r.get('comment', 'N/A')} |

"""
    
    # Summary stats
    buy_count = sum(1 for r in results if r.get('signal') == 'BUY')
    sell_count = sum(1 for r in results if r.get('signal') == 'SELL')
    hold_count = sum(1 for r in results if r.get('signal') == 'HOLD')
    
    report += f"""---

## 📋 總結 | Summary

- **🚀 BUY:** {buy_count} stocks
- **⚠️ HOLD:** {hold_count} stocks  
- **🔴 SELL:** {sell_count} stocks

**Note:** Analysis based on technical indicators (MA, volume, price position). 
For full Cai Sen pattern analysis with LLM interpretation, API access required.

---
*Generated by cyclingAi (csagent fallback)*
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
        fieldnames = ['symbol', 'name', 'sector', 'signal', 'confidence', 'pattern', 'volume_status',
                      'entry_price', 'stop_loss', 'target_price', 'comment', 'current_price',
                      'trend', 'change_20d', 'change_60d', 'vol_ratio', 'position_pct']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
    
    return report_path


def main():
    print("=" * 80)
    print("蔡森多股票分析 v2 (Fallback Mode) | Cai Sen Multi-Stock Analysis")
    print("=" * 80)
    print(f"開始時間 Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析股票 Stocks: {len(STOCKS)}")
    print(f"模式：Technical Analysis Fallback (No API)")
    print()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = f'/root/.openclaw/workspace/caisen_data/multi_stock_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    
    for i, stock in enumerate(STOCKS, 1):
        print(f"[{i}/{len(STOCKS)}] 分析 Analyzing: {stock['name']} ({stock['code']})...")
        
        data = load_csv(stock['file'])
        
        if not data.get('success'):
            print(f"  ❌ 數據載入失敗: {data.get('error', 'Unknown')}")
            results.append({
                'symbol': stock['code'],
                'name': stock['name'],
                'sector': stock['sector'],
                'signal': 'HOLD',
                'confidence': 0,
                'error': data.get('error', 'Data load failed')
            })
            continue
        
        print(f"  ✅ 數據載入成功 Loaded {data['data_points']} days")
        
        analysis = analyze_stock(data, stock)
        results.append(analysis)
        
        emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(analysis.get('signal', 'HOLD'), '⚠️')
        print(f"  ✅ {emoji} {analysis['signal']} ({analysis['confidence']}%) - {analysis['pattern']}")
        print()
    
    print("📝 生成報告 Generating reports...")
    report_path = generate_reports(results, output_dir)
    print(f"  ✅ 報告已保存: {report_path}")
    print(f"  ✅ JSON: {output_dir}/csagen_analysis_results.json")
    print(f"  ✅ CSV: {output_dir}/csagen_analysis_results.csv")
    print()
    
    buy_count = sum(1 for r in results if r.get('signal') == 'BUY')
    sell_count = sum(1 for r in results if r.get('signal') == 'SELL')
    hold_count = sum(1 for r in results if r.get('signal') == 'HOLD')
    
    print("=" * 80)
    print("分析完成 | Analysis Complete")
    print("=" * 80)
    print(f"🚀 BUY: {buy_count} | ⚠️ HOLD: {hold_count} | 🔴 SELL: {sell_count}")
    print(f"輸出目錄 Output: {output_dir}")
    
    return output_dir, results


if __name__ == '__main__':
    main()
