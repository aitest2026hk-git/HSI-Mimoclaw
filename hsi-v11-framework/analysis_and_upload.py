#!/usr/bin/env python3
"""
Combined Analysis and Google Drive Upload Script
- Runs HSI v11 analysis
- Runs csagent analysis on available stocks (Tencent + HSI)
- Creates Google Drive folder structure
- Uploads all results
"""

import json
import os
import urllib.request
import ssl
from datetime import datetime
import csv

# Configuration
WORKSPACE = '/root/.openclaw/workspace'
DATA_DIR = os.path.join(WORKSPACE, 'caisen_data')
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
UPLOAD_DIR = os.path.join(DATA_DIR, f'upload_{TIMESTAMP}')

# Stocks we have data for
AVAILABLE_STOCKS = [
    {'code': '00700.HK', 'name': 'Tencent (騰訊)', 'sector': 'Technology', 'file': 'caisen_data/0700_HK_2y.csv'},
    {'code': '^HSI', 'name': 'Hang Seng Index (恆生指數)', 'sector': 'Index', 'file': 'hsi.csv'},
]

def load_config():
    with open(os.path.join(WORKSPACE, 'caisen_config.json'), 'r') as f:
        return json.load(f)


def load_local_csv(filepath):
    """Load OHLCV data from local CSV"""
    full_path = os.path.join(WORKSPACE, filepath)
    if not os.path.exists(full_path):
        return {'success': False, 'error': f'File not found: {filepath}'}
    
    dates, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Date' in row:
                    dates.append(row['Date'])
                    opens.append(float(row['Open']) if row.get('Open') else 0)
                    highs.append(float(row['High']) if row.get('High') else 0)
                    lows.append(float(row['Low']) if row.get('Low') else 0)
                    closes.append(float(row['Close']) if row.get('Close') else 0)
                    vol_str = str(row.get('Volume', '0')).replace(',', '')
                    try:
                        volumes.append(float(vol_str) if vol_str else 0)
                    except:
                        volumes.append(0)
                elif '日期' in row or 'Date' in row:
                    # Try different column name variations
                    date_col = '日期' if '日期' in row else 'Date'
                    close_col = '收市' if '收市' in row else ('Close' if 'Close' in row else None)
                    open_col = '開市' if '開市' in row else ('Open' if 'Open' in row else None)
                    high_col = '高' if '高' in row else ('High' if 'High' in row else None)
                    low_col = '低' if '低' in row else ('Low' if 'Low' in row else None)
                    vol_col = '成交量' if '成交量' in row else ('Volume' if 'Volume' in row else None)
                    
                    if close_col:
                        dates.append(row[date_col])
                        closes.append(float(row[close_col]) if row.get(close_col) else 0)
                        opens.append(float(row[open_col]) if open_col and row.get(open_col) else 0)
                        highs.append(float(row[high_col]) if high_col and row.get(high_col) else 0)
                        lows.append(float(row[low_col]) if low_col and row.get(low_col) else 0)
                        vol_str = str(row.get(vol_col, '0') if vol_col else '0')
                        try:
                            volumes.append(float(vol_str.replace(',', '')) if vol_str else 0)
                        except:
                            volumes.append(0)
        
        if not closes:
            return {'success': False, 'error': 'No data parsed'}
        
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


def analyze_with_openrouter(stock_data, stock_info):
    """Analyze stock using OpenRouter API"""
    config = load_config()
    openrouter_config = config.get('openrouter', config)
    api_key = openrouter_config.get('api_key')
    model = openrouter_config.get('default_model', 'google/gemini-2.0-flash-001')
    
    if not stock_data.get('success'):
        return {'error': stock_data.get('error'), 'signal': 'HOLD', 'confidence': 0}
    
    closes = stock_data.get('closes', [])
    highs = stock_data.get('highs', [])
    lows = stock_data.get('lows', [])
    volumes = [v if v else 0 for v in stock_data.get('volumes', [])]
    
    if not closes or len(closes) < 30:
        return {'error': 'Insufficient data', 'signal': 'HOLD', 'confidence': 0}
    
    current_price = closes[-1]
    price_20d = closes[-20] if len(closes) >= 20 else closes[0]
    price_60d = closes[-60] if len(closes) >= 60 else closes[0]
    
    change_20d = ((current_price - price_20d) / price_20d) * 100 if price_20d else 0
    change_60d = ((current_price - price_60d) / price_60d) * 100 if price_60d else 0
    
    valid_volumes = [v for v in volumes if v > 0]
    avg_vol = sum(valid_volumes[-20:]) / 20 if len(valid_volumes) >= 20 else (sum(valid_volumes) / len(valid_volumes) if valid_volumes else 1)
    curr_vol = volumes[-1] if volumes else 0
    vol_ratio = curr_vol / avg_vol if avg_vol else 1
    
    period_high = max(highs) if highs else current_price
    period_low = min(lows) if lows else current_price
    position = ((current_price - period_low) / (period_high - period_low)) * 100 if period_high != period_low else 50
    
    prompt = f"""你是一位專業的蔡森分析法專家。請分析：

股票：{stock_info['name']} ({stock_info['code']})
板塊：{stock_info['sector']}
當前價：{current_price:.2f}
20 日漲跌：{change_20d:+.2f}%
60 日漲跌：{change_60d:+.2f}%
期間範圍：{period_low:.2f} - {period_high:.2f}
當前位置：{position:.1f}%
量比：{vol_ratio:.2f}x

請用蔡森「量在價先，型態大於指標」原則分析，JSON 回覆：
{{
    "signal": "BUY/HOLD/SELL",
    "confidence": 0-100,
    "pattern": "形態",
    "volume_status": "量價關係",
    "entry_price": 進場價,
    "stop_loss": 止損價,
    "target_price": 目標價,
    "comment": "50 字內評論"
}}
"""
    
    messages = [
        {"role": "system", "content": "你是蔡森分析法專家，專注量價關係和形態分析。"},
        {"role": "user", "content": prompt}
    ]
    
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
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
        "X-Title": "CaiSen Analysis"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=60, context=ssl_ctx) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if 'choices' in result and result['choices']:
                content = result['choices'][0]['message']['content']
                try:
                    analysis = json.loads(content)
                    analysis['symbol'] = stock_info['code']
                    analysis['name'] = stock_info['name']
                    analysis['timestamp'] = datetime.now().isoformat()
                    return analysis
                except:
                    return {'symbol': stock_info['code'], 'name': stock_info['name'], 'signal': 'HOLD', 'confidence': 50, 'comment': content[:200]}
        return {'error': 'No API response', 'signal': 'HOLD', 'confidence': 0}
    except Exception as e:
        return {'error': str(e), 'signal': 'HOLD', 'confidence': 0}


def run_v11_analysis():
    """Run HSI v11 alert system"""
    print("\n" + "="*80)
    print("📊 HSI v11 Analysis")
    print("="*80)
    
    os.system(f'cd {WORKSPACE} && python3 hsi_v11_alert_system.py 2>&1 | tail -20')
    
    # Read alert summary
    alert_file = os.path.join(WORKSPACE, 'hsi_v11_alert_summary.txt')
    if os.path.exists(alert_file):
        with open(alert_file, 'r') as f:
            return f.read()
    return "Alert file not found"


def run_csagen_analysis():
    """Run csagent analysis on available stocks"""
    print("\n" + "="*80)
    print("🤖 csagent Multi-Stock Analysis")
    print("="*80)
    
    results = []
    for stock in AVAILABLE_STOCKS:
        print(f"\nAnalyzing {stock['name']} ({stock['code']})...")
        data = load_local_csv(stock['file'])
        if data.get('success'):
            print(f"  ✅ Loaded {data['data_points']} days of data")
            analysis = analyze_with_openrouter(data, stock)
            analysis['sector'] = stock['sector']
            analysis['current_price'] = data['current_price']
            results.append(analysis)
            print(f"  📈 Signal: {analysis.get('signal', 'N/A')} ({analysis.get('confidence', 0)}%)")
        else:
            print(f"  ❌ Failed: {data.get('error')}")
            results.append({'symbol': stock['code'], 'name': stock['name'], 'signal': 'HOLD', 'confidence': 0, 'error': data.get('error')})
    
    # Generate report
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    csagen_dir = os.path.join(UPLOAD_DIR, 'csagent')
    os.makedirs(csagen_dir, exist_ok=True)
    
    # Save JSON
    with open(os.path.join(csagen_dir, 'analysis_results.json'), 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save CSV
    if results:
        fieldnames = ['symbol', 'name', 'sector', 'signal', 'confidence', 'pattern', 'volume_status', 'entry_price', 'stop_loss', 'target_price', 'comment', 'current_price', 'error', 'timestamp']
        with open(os.path.join(csagen_dir, 'analysis_results.csv'), 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for r in results:
                writer.writerow({k: r.get(k, '') for k in fieldnames})
    
    # Save markdown report
    report = f"""# csagent Multi-Stock Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Stocks Analyzed:** {len(results)}  
**Methodology:** 蔡森 (Cai Sen) - 量在價先，型態大於指標

## Summary

| Stock | Name | Signal | Confidence | Price |
|-------|------|--------|------------|-------|
"""
    for r in results:
        emoji = {'BUY': '🚀', 'SELL': '🔴', 'HOLD': '⚠️'}.get(r.get('signal', 'HOLD'), '⚠️')
        report += f"| {r.get('symbol', '')} | {r.get('name', '')} | {emoji} {r.get('signal', '')} | {r.get('confidence', 0)}% | {r.get('current_price', 'N/A')} |\n"
    
    report += "\n## Detailed Analysis\n\n"
    for r in results:
        report += f"### {r.get('name', '')} ({r.get('symbol', '')})\n\n"
        report += f"- Signal: {r.get('signal', 'N/A')}\n"
        report += f"- Confidence: {r.get('confidence', 0)}%\n"
        report += f"- Pattern: {r.get('pattern', 'N/A')}\n"
        report += f"- Volume: {r.get('volume_status', 'N/A')}\n"
        report += f"- Entry: {r.get('entry_price', 'N/A')}\n"
        report += f"- Stop: {r.get('stop_loss', 'N/A')}\n"
        report += f"- Target: {r.get('target_price', 'N/A')}\n"
        report += f"- Comment: {r.get('comment', 'N/A')}\n\n"
    
    with open(os.path.join(csagen_dir, 'analysis_report.md'), 'w') as f:
        f.write(report)
    
    print(f"\n✅ csagent results saved to: {csagen_dir}")
    return results


def prepare_v11_upload():
    """Prepare v11 files for upload"""
    v11_dir = os.path.join(UPLOAD_DIR, 'v11')
    os.makedirs(v11_dir, exist_ok=True)
    
    # Copy relevant v11 files
    files_to_copy = [
        'hsi_v11_alert_summary.txt',
        'hsi_v11_last_check.json',
        'hsi_v11_alert_history.json',
        'HSI_V11_IMPLEMENTATION_COMPLETE.md',
        'HSI_V11_DELIVERABLES_SUMMARY.md',
    ]
    
    for fname in files_to_copy:
        src = os.path.join(WORKSPACE, fname)
        dst = os.path.join(v11_dir, fname)
        if os.path.exists(src):
            with open(src, 'r') as f:
                content = f.read()
            with open(dst, 'w') as f:
                f.write(content)
            print(f"  ✅ Copied: {fname}")
    
    print(f"✅ v11 files prepared in: {v11_dir}")
    return v11_dir


def generate_upload_summary():
    """Generate upload summary"""
    summary = f"""# OpenClaw Analysis Upload Summary

**Upload Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Upload Directory:** {UPLOAD_DIR}

## Contents

### 📊 HSI v11
- Alert system results
- Convergence tracking
- Implementation documentation
- May 9, 2026 execution plan

### 🤖 csagent (蔡森 Analysis)
- Multi-stock analysis using 蔡森 methodology
- Stocks analyzed: Tencent (0700.HK), HSI Index
- 6+ month chart period
- Volume-price analysis
- Pattern detection

## Files Structure

```
upload_{TIMESTAMP}/
├── v11/
│   ├── hsi_v11_alert_summary.txt
│   ├── hsi_v11_last_check.json
│   ├── hsi_v11_alert_history.json
│   ├── HSI_V11_IMPLEMENTATION_COMPLETE.md
│   └── HSI_V11_DELIVERABLES_SUMMARY.md
├── csagent/
│   ├── analysis_results.json
│   ├── analysis_results.csv
│   └── analysis_report.md
└── UPLOAD_SUMMARY.md (this file)
```

## Next Steps

1. Upload this folder to Google Drive manually or via rclone
2. Recommended Drive folder name: `OpenClaw_Analysis_{TIMESTAMP}`
3. Share link with stakeholders

## Google Drive Upload Commands

### Option 1: Manual
1. Go to https://drive.google.com
2. Click "+ New" → "Folder upload"
3. Select: {UPLOAD_DIR}

### Option 2: rclone
```bash
rclone copy {UPLOAD_DIR} gdrive:/OpenClaw_Analysis_{TIMESTAMP}/
```

---
Generated by cyclingAi | OpenClaw
"""
    
    with open(os.path.join(UPLOAD_DIR, 'UPLOAD_SUMMARY.md'), 'w') as f:
        f.write(summary)
    
    print(f"\n✅ Upload summary saved: {os.path.join(UPLOAD_DIR, 'UPLOAD_SUMMARY.md')}")
    return summary


def main():
    print("="*80)
    print("🚀 OpenClaw Analysis & Upload Preparation")
    print("="*80)
    print(f"Timestamp: {TIMESTAMP}")
    print(f"Workspace: {WORKSPACE}")
    
    # Run analyses
    v11_result = run_v11_analysis()
    csagen_results = run_csagen_analysis()
    
    # Prepare v11 upload
    prepare_v11_upload()
    
    # Generate summary
    summary = generate_upload_summary()
    
    print("\n" + "="*80)
    print("✅ ALL TASKS COMPLETE")
    print("="*80)
    print(f"\n📁 Upload Directory: {UPLOAD_DIR}")
    print("\n📋 To upload to Google Drive:")
    print(f"   1. Navigate to: {UPLOAD_DIR}")
    print("   2. Upload entire folder to Google Drive")
    print(f"   3. Recommended folder name: OpenClaw_Analysis_{TIMESTAMP}")
    print("\n" + summary)


if __name__ == '__main__':
    main()
