#!/usr/bin/env python3
"""
Run CaiSen Analysis on Tencent (0700.HK) - V2 with better JSON parsing
"""

import json
import csv
import re
from datetime import datetime
from openrouter_analyzer import call_openrouter

def load_tencent_data(filepath):
    """Load OHLCV data from CSV"""
    data = {'dates': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
    
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

def extract_json(content):
    """Extract JSON from LLM response (handles reasoning text)"""
    # Try to find JSON object
    json_start = content.find('{')
    json_end = content.rfind('}') + 1
    
    if json_start >= 0 and json_end > json_start:
        json_str = content[json_start:json_end]
        try:
            return json.loads(json_str)
        except:
            pass
    
    # Try to find array
    array_start = content.find('[')
    array_end = content.rfind(']') + 1
    
    if array_start >= 0 and array_end > array_start:
        array_str = content[array_start:array_end]
        try:
            return json.loads(array_str)
        except:
            pass
    
    return None

def analyze_tencent():
    """Analyze Tencent with LLM"""
    print("📊 Task 1: Analyzing OHLC Data...")
    print()
    
    # Load data
    data = load_tencent_data('/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv')
    
    # Calculate stats
    n = min(30, len(data['close']))
    current_price = data['close'][-1]
    price_20d_ago = data['close'][-20] if len(data['close']) >= 20 else data['close'][0]
    price_change_pct = ((current_price - price_20d_ago) / price_20d_ago) * 100
    
    high_30d = max(data['high'][-30:])
    low_30d = min(data['low'][-30:])
    
    # Get last 30 days data
    recent_data = []
    for i in range(-n, 0):
        recent_data.append({
            'date': data['dates'][i],
            'open': round(data['open'][i], 2),
            'high': round(data['high'][i], 2),
            'low': round(data['low'][i], 2),
            'close': round(data['close'][i], 2),
            'volume': data['volume'][i]
        })
    
    system_prompt = """You are an expert technical analyst specializing in 蔡森 (Cai Sen)'s volume-price methodology.

蔡森's 12 Key Patterns:
1. W-bottom (雙重底) - Bullish reversal
2. 破底翻 (Spring) - False breakdown then reversal
3. M-top (雙重頂) - Bearish reversal
4. 假突破 (False Breakout) - Breakout fails
5. 頭肩頂 (Head & Shoulders Top) - Bearish
6. 頭肩底 (Head & Shoulders Bottom) - Bullish
7. 收斂三角形頭部 (Descending Triangle)
8. 收斂三角形底部 (Ascending Triangle)
9. 上飄旗形 (Bearish Flag)
10. 下飄旗形 (Bullish Flag)
11. 問題量 (Problem Volume) - Volume-price divergence
12. 時間波 (Time Waves) - Cyclical patterns

Core Principles:
- 量在價先 (Volume precedes price)
- 小賠大賺 (Small losses, big gains)
- 嚴守停損 (Strict stop-loss)
- 隨勢而為 (Follow the trend)"""

    user_prompt = f"""Analyze 0700.HK (Tencent) based on this data:

**Current Price**: HKD {current_price:.2f}
**30-Day Range**: HKD {low_30d:.2f} - HKD {high_30d:.2f}
**20-Day Change**: {price_change_pct:+.1f}%

**Last 10 Trading Days**:
{json.dumps(recent_data[-10:], indent=2)}

Return ONLY valid JSON (no reasoning text, no markdown):

{{
    "trend": {{
        "direction": "uptrend|downtrend|sideways",
        "strength": "strong|moderate|weak",
        "evidence": "brief explanation"
    }},
    "volume": {{
        "trend": "increasing|decreasing|flat",
        "confirming_price": true|false,
        "notes": "brief observation"
    }},
    "patterns": [
        {{"name": "pattern name", "confidence": 0.0-1.0, "evidence": "brief"}}
    ],
    "levels": {{
        "support1": price,
        "support2": price,
        "resistance1": price,
        "resistance2": price
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "reasoning": "brief"
    }},
    "risks": ["risk1", "risk2"]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    print("   Calling OpenRouter API...")
    result = call_openrouter(messages, max_tokens=1500)
    
    if 'error' in result:
        print(f"   ❌ API Error: {result.get('error')}")
        return None
    
    try:
        content = result['choices'][0]['message']['content']
        print(f"   Raw response length: {len(content)} chars")
        
        analysis = extract_json(content)
        
        if analysis:
            analysis['model_used'] = 'nvidia/nemotron-3-nano-30b-a3b:free'
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['data_source'] = '0700_HK_2y.csv'
            print("   ✅ Analysis complete!")
            return analysis
        else:
            print(f"   ⚠️ Could not parse JSON, saving raw response")
            return {'raw_analysis': content, 'timestamp': datetime.now().isoformat()}
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    print("=" * 60)
    print("🎯 CaiSen Tencent Analysis")
    print("=" * 60)
    print()
    
    # Run analysis
    analysis = analyze_tencent()
    
    if analysis:
        # Save analysis
        output_path = '/root/.openclaw/workspace/caisen_data/tencent_analysis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"   💾 Saved to: {output_path}")
        
        # Print summary
        print()
        print("=" * 60)
        print("📊 ANALYSIS SUMMARY")
        print("=" * 60)
        
        if 'signal' in analysis:
            sig = analysis['signal']
            print(f"Signal: {sig.get('direction', 'N/A')} ({sig.get('confidence', 0)*100:.0f}% confidence)")
            print(f"Reasoning: {sig.get('reasoning', 'N/A')}")
        
        if 'trend' in analysis:
            t = analysis['trend']
            print(f"Trend: {t.get('direction', 'N/A')} ({t.get('strength', 'N/A')})")
        
        if 'patterns' in analysis and analysis['patterns']:
            print(f"Patterns detected: {len(analysis['patterns'])}")
            for p in analysis['patterns'][:3]:
                print(f"  • {p.get('name', 'Unknown')} ({p.get('confidence', 0)*100:.0f}%)")
        
        if 'levels' in analysis:
            l = analysis['levels']
            print(f"Support: {l.get('support1', 'N/A')} / {l.get('support2', 'N/A')}")
            print(f"Resistance: {l.get('resistance1', 'N/A')} / {l.get('resistance2', 'N/A')}")
        
        if 'risks' in analysis:
            print(f"Risks: {', '.join(analysis['risks'][:3])}")
    
    print()
    print("📈 Chart already generated: caisen_data/tencent_chart.html")
    print()
    print("=" * 60)
    print("✅ Tasks Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
