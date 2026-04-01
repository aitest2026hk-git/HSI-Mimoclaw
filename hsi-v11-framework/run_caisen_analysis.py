#!/usr/bin/env python3
"""
Run CaiSen Analysis on Tencent (0700.HK)
Task 1: Analyze OHLC data
Task 3: Generate chart and analyze with vision
"""

import json
import csv
import urllib.request
import ssl
from datetime import datetime
from openrouter_analyzer import call_openrouter

def load_tencent_data(filepath):
    """Load OHLCV data from CSV"""
    data = {
        'dates': [],
        'open': [],
        'high': [],
        'low': [],
        'close': [],
        'volume': []
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data['dates'].append(row['Date'])
            data['open'].append(float(row['Open']))
            data['high'].append(float(row['High']))
            data['low'].append(float(row['Low']))
            data['close'].append(float(row['Close']))
            data['volume'].append(int(row['Volume']))
    
    return data

def analyze_tencent_ohlc(data):
    """Analyze Tencent OHLC data using LLM"""
    print("📊 Task 1: Analyzing OHLC Data...")
    print()
    
    # Calculate summary statistics
    n = min(60, len(data['close']))
    current_price = data['close'][-1]
    price_20d_ago = data['close'][-20] if len(data['close']) >= 20 else data['close'][0]
    price_change_pct = ((current_price - price_20d_ago) / price_20d_ago) * 100
    
    avg_vol_recent = sum(data['volume'][-10:]) / 10
    avg_vol_older = sum(data['volume'][-30:-10]) / 20 if len(data['volume']) >= 30 else avg_vol_recent
    vol_change_pct = ((avg_vol_recent - avg_vol_older) / avg_vol_older) * 100 if avg_vol_older > 0 else 0
    
    high_60d = max(data['high'][-60:])
    low_60d = min(data['low'][-60:])
    
    # Get recent data
    recent_data = []
    for i in range(-n, 0):
        recent_data.append({
            'date': data['dates'][i],
            'open': data['open'][i],
            'high': data['high'][i],
            'low': data['low'][i],
            'close': data['close'][i],
            'volume': data['volume'][i]
        })
    
    system_prompt = """You are an expert technical analyst specializing in 蔡森 (Cai Sen)'s volume-price methodology.

Key Principles:
- 量在價先 (Volume precedes price)
- 小賠大賺 (Small losses, big gains)
- 嚴守停損 (Strict stop-loss)
- 隨勢而為 (Follow the trend)

Focus on volume-price relationships and the 12 蔡森 patterns."""

    user_prompt = f"""Analyze 0700.HK (Tencent) based on the following OHLCV data summary:

**Current Price**: HKD {current_price:.2f}
**60-Day Range**: HKD {low_60d:.2f} - HKD {high_60d:.2f}
**20-Day Change**: {price_change_pct:+.1f}%
**Volume Trend**: {vol_change_pct:+.1f}% (recent vs older)

**Recent Data (last 10 days)**:
{json.dumps(recent_data[-10:], indent=2)}

**Full Recent Data (last 60 days)**:
{json.dumps(recent_data, indent=2)}

Provide analysis in JSON format:

{{
    "trend_analysis": {{
        "direction": "uptrend|downtrend|sideways",
        "strength": "strong|moderate|weak",
        "evidence": "Explanation"
    }},
    "volume_analysis": {{
        "trend": "increasing|decreasing|flat",
        "confirming_price": true|false,
        "divergence_detected": true|false,
        "notes": "Volume observations"
    }},
    "patterns_detected": [
        {{
            "name": "Pattern name from 蔡森's 12 patterns",
            "confidence": 0.0-1.0,
            "evidence": "Why you think this pattern exists"
        }}
    ],
    "key_levels": {{
        "immediate_support": price,
        "strong_support": price,
        "immediate_resistance": price,
        "strong_resistance": price
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "reasoning": "Why this signal"
    }},
    "caisen_principles": ["Which principles apply"],
    "risk_factors": ["Key risks to consider"]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("   Calling OpenRouter API...")
    result = call_openrouter(messages, max_tokens=2000)
    
    if 'error' in result:
        print(f"   ❌ API Error: {result.get('error')}")
        return None
    
    try:
        content = result['choices'][0]['message']['content']
        
        # Extract JSON
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            analysis = json.loads(json_str)
            analysis['model_used'] = 'nvidia/nemotron-3-nano-30b-a3b:free'
            analysis['timestamp'] = datetime.now().isoformat()
            
            print("   ✅ Analysis complete!")
            return analysis
        else:
            print(f"   ❌ Could not parse JSON from response")
            return {'raw_analysis': content}
    
    except Exception as e:
        print(f"   ❌ Error parsing response: {e}")
        return None

def generate_chart_html(data, output_path):
    """Generate a simple HTML chart using Plotly-like visualization"""
    print()
    print("📈 Task 3: Generating Chart...")
    
    # Create simple HTML chart with Chart.js
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Tencent (0700.HK) - 蔡森 Analysis Chart</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: #eee; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #00d4ff; }}
        .chart-container {{ position: relative; height: 600px; margin: 20px 0; }}
        .info {{ background: #16213e; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 Tencent Holdings (0700.HK)</h1>
        <div class="info">
            <p><strong>Data Range:</strong> {data['dates'][0]} to {data['dates'][-1]}</p>
            <p><strong>Current Price:</strong> HKD {data['close'][-1]:.2f}</p>
            <p><strong>60-Day High:</strong> HKD {max(data['high'][-60:]):.2f}</p>
            <p><strong>60-Day Low:</strong> HKD {min(data['low'][-60:]):.2f}</p>
        </div>
        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('priceChart').getContext('2d');
        
        const priceData = {json.dumps(data['close'][-90:])};
        const volumeData = {json.dumps(data['volume'][-90:])};
        const labels = {json.dumps(data['dates'][-90:])};
        
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [{{
                    label: 'Close Price (HKD)',
                    data: priceData,
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ labels: {{ color: '#eee' }} }},
                    title: {{
                        display: true,
                        text: 'Tencent (0700.HK) - Last 90 Days',
                        color: '#00d4ff',
                        font: {{ size: 16 }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#aaa', maxTicksLimit: 10 }},
                        grid: {{ color: '#333' }}
                    }},
                    y: {{
                        ticks: {{ color: '#aaa' }},
                        grid: {{ color: '#333' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ Chart saved to: {output_path}")
    return output_path

def main():
    print("=" * 60)
    print("🎯 CaiSen Tencent Analysis")
    print("=" * 60)
    print()
    
    # Load data
    data_path = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    print(f"📂 Loading data from: {data_path}")
    
    try:
        data = load_tencent_data(data_path)
        print(f"   ✅ Loaded {len(data['close'])} trading days")
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")
        return
    
    # Task 1: Analyze OHLC data
    analysis = analyze_tencent_ohlc(data)
    
    if analysis:
        # Save analysis
        output_path = '/root/.openclaw/workspace/caisen_data/tencent_analysis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"   💾 Analysis saved to: {output_path}")
        
        # Print summary
        print()
        print("=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        if 'signal' in analysis:
            signal = analysis['signal']
            direction = signal.get('direction', 'N/A')
            confidence = signal.get('confidence', 0) * 100
            print(f"Signal: {direction} ({confidence:.0f}% confidence)")
        
        if 'trend_analysis' in analysis:
            trend = analysis['trend_analysis']
            print(f"Trend: {trend.get('direction', 'N/A')} ({trend.get('strength', 'N/A')})")
        
        if 'patterns_detected' in analysis and analysis['patterns_detected']:
            print(f"Patterns: {len(analysis['patterns_detected'])} detected")
            for p in analysis['patterns_detected'][:3]:
                print(f"  - {p.get('name', 'Unknown')} ({p.get('confidence', 0)*100:.0f}%)")
        
        if 'key_levels' in analysis:
            levels = analysis['key_levels']
            print(f"Support: {levels.get('immediate_support', 'N/A')} / {levels.get('strong_support', 'N/A')}")
            print(f"Resistance: {levels.get('immediate_resistance', 'N/A')} / {levels.get('strong_resistance', 'N/A')}")
    
    # Task 3: Generate chart
    chart_path = '/root/.openclaw/workspace/caisen_data/tencent_chart.html'
    generate_chart_html(data, chart_path)
    
    print()
    print("=" * 60)
    print("✅ Tasks Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
