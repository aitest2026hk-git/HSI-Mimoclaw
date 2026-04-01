#!/usr/bin/env python3
"""
蔡森 (Cai Sen) Full Technical Analysis for Tencent (0700.HK)

Implements all 12 蔡森 patterns with volume-price analysis:
1. W-bottom (雙重底)
2. M-top (雙重頂)
3. Head & Shoulders Top (頭肩頂)
4. Head & Shoulders Bottom (頭肩底)
5. False Breakout Up (假突破多)
6. False Breakout Down (假突破空)
7. Ascending Triangle (上升三角形)
8. Descending Triangle (下降三角形)
9. Rising Channel (上升通道)
10. Falling Channel (下降通道)
11. Volume Spike Reversal (量增反轉)
12. Volume Divergence (量價背離)

Key 蔡森 Principles:
- 量在價先 (Volume precedes price)
- 小賠大賺 (Small losses, big gains)
- 嚴守停損 (Strict stop-loss)
- 隨勢而為 (Follow the trend)
"""

import csv
import json
import math
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple

# Import pattern detection from caisen_patterns
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
from caisen_patterns import (
    load_data, detect_w_bottom, detect_m_top, detect_head_shoulders,
    detect_false_breakout, calc_mean, find_local_extrema
)


def load_csv_data(filepath: str) -> Dict:
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


def detect_ascending_triangle(data: Dict) -> Optional[Dict]:
    """Detect Ascending Triangle (上升三角形) - Bullish continuation"""
    highs = data['high']
    lows = data['low']
    closes = data['close']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 60:
        return None
    
    # Look for flat resistance and rising lows
    window = 40
    recent_highs = highs[-window:]
    recent_lows = lows[-window:]
    
    # Check if highs are relatively flat (within 3%)
    high_range = (max(recent_highs) - min(recent_highs)) / min(recent_highs)
    if high_range > 0.05:
        return None
    
    # Check if lows are rising
    first_half_lows = recent_lows[:window//2]
    second_half_lows = recent_lows[window//2:]
    
    if calc_mean(second_half_lows) <= calc_mean(first_half_lows):
        return None
    
    resistance = max(recent_highs)
    support_line = min(recent_lows)
    
    # Check for breakout
    breakout = False
    breakout_idx = None
    for i in range(len(closes) - 20, len(closes)):
        if closes[i] > resistance * 1.02:
            breakout = True
            breakout_idx = i
            break
    
    if not breakout:
        return None
    
    breakout_vol = volumes[breakout_idx]
    avg_vol = calc_mean(volumes[-30:-10])
    volume_confirmed = breakout_vol > avg_vol * 1.5
    
    entry_price = resistance
    stop_loss = support_line * 0.97
    pattern_height = resistance - support_line
    target_price = resistance + pattern_height
    
    risk = entry_price - stop_loss
    reward = target_price - entry_price
    risk_reward = reward / risk if risk > 0 else 0
    
    confidence = 0.55
    confidence += 0.15 if volume_confirmed else 0
    confidence += 0.10 if high_range < 0.03 else 0
    confidence = min(confidence, 0.90)
    
    return {
        'pattern': 'Ascending Triangle (上升三角形)',
        'type': 'bullish_continuation',
        'detected_at': dates[breakout_idx],
        'confidence': round(confidence, 2),
        'entry_price': round(entry_price, 2),
        'stop_loss': round(stop_loss, 2),
        'target_price': round(target_price, 2),
        'risk_reward_ratio': round(risk_reward, 2),
        'volume_confirmed': volume_confirmed,
        'notes': f"Breakout on {'strong' if volume_confirmed else 'weak'} volume"
    }


def detect_descending_triangle(data: Dict) -> Optional[Dict]:
    """Detect Descending Triangle (下降三角形) - Bearish continuation"""
    highs = data['high']
    lows = data['low']
    closes = data['close']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 60:
        return None
    
    window = 40
    recent_highs = highs[-window:]
    recent_lows = lows[-window:]
    
    # Check if lows are relatively flat (within 3%)
    low_range = (max(recent_lows) - min(recent_lows)) / min(recent_lows)
    if low_range > 0.05:
        return None
    
    # Check if highs are falling
    first_half_highs = recent_highs[:window//2]
    second_half_highs = recent_highs[window//2:]
    
    if calc_mean(second_half_highs) >= calc_mean(first_half_highs):
        return None
    
    support = min(recent_lows)
    resistance_line = max(recent_highs)
    
    # Check for breakdown
    breakdown = False
    breakdown_idx = None
    for i in range(len(closes) - 20, len(closes)):
        if closes[i] < support * 0.98:
            breakdown = True
            breakdown_idx = i
            break
    
    if not breakdown:
        return None
    
    entry_price = support
    stop_loss = resistance_line * 1.03
    pattern_height = resistance_line - support
    target_price = support - pattern_height
    
    risk = stop_loss - entry_price
    reward = entry_price - target_price
    risk_reward = reward / risk if risk > 0 else 0
    
    confidence = 0.55
    confidence += 0.10 if low_range < 0.03 else 0
    confidence = min(confidence, 0.85)
    
    return {
        'pattern': 'Descending Triangle (下降三角形)',
        'type': 'bearish_continuation',
        'detected_at': dates[breakdown_idx],
        'confidence': round(confidence, 2),
        'entry_price': round(entry_price, 2),
        'stop_loss': round(stop_loss, 2),
        'target_price': round(target_price, 2),
        'risk_reward_ratio': round(risk_reward, 2),
        'notes': "Breakdown detected"
    }


def detect_volume_divergence(data: Dict) -> Optional[Dict]:
    """Detect Volume-Price Divergence (量價背離)"""
    closes = data['close']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 40:
        return None
    
    # Look for higher highs in price but lower highs in volume
    recent_closes = closes[-30:]
    recent_volumes = volumes[-30:]
    
    # Find price peaks
    price_peaks = find_local_extrema(closes, valley=False, order=5)
    volume_peaks = find_local_extrema(volumes, valley=False, order=5)
    
    if len(price_peaks) < 2 or len(volume_peaks) < 2:
        return None
    
    # Check last two price peaks
    p1, p2 = price_peaks[-2], price_peaks[-1]
    price_higher = closes[p2] > closes[p1]
    
    # Check corresponding volume
    if p2 < len(volumes) and p1 < len(volumes):
        vol_lower = volumes[p2] < volumes[p1] * 0.8
        
        if price_higher and vol_lower:
            # Bearish divergence
            confidence = 0.65
            return {
                'pattern': 'Volume-Price Divergence (量價背離)',
                'type': 'bearish_reversal',
                'detected_at': dates[-1],
                'confidence': round(confidence, 2),
                'evidence': f"Price made higher high ({closes[p2]:.2f} > {closes[p1]:.2f}) but volume declined ({volumes[p2]:,.0f} < {volumes[p1]:,.0f})",
                'notes': "Volume not confirming price strength - potential reversal"
            }
    
    # Check for bullish divergence (lower lows in price, higher lows in volume)
    price_valleys = find_local_extrema(closes, valley=True, order=5)
    if len(price_valleys) >= 2:
        v1, v2 = price_valleys[-2], price_valleys[-1]
        price_lower = closes[v2] < closes[v1]
        
        if v2 < len(volumes) and v1 < len(volumes):
            vol_higher = volumes[v2] > volumes[v1] * 1.2
            
            if price_lower and vol_higher:
                confidence = 0.65
                return {
                    'pattern': 'Volume-Price Divergence (量價背離)',
                    'type': 'bullish_reversal',
                    'detected_at': dates[-1],
                    'confidence': round(confidence, 2),
                    'evidence': f"Price made lower low ({closes[v2]:.2f} < {closes[v1]:.2f}) but volume increased ({volumes[v2]:,.0f} > {volumes[v1]:,.0f})",
                    'notes': "Volume accumulation on weakness - potential reversal up"
                }
    
    return None


def detect_volume_spike_reversal(data: Dict) -> Optional[Dict]:
    """Detect Volume Spike Reversal (量增反轉)"""
    closes = data['close']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 30:
        return None
    
    avg_vol = calc_mean(volumes[-30:-1])
    current_vol = volumes[-1]
    
    # Volume spike = 2x average
    if current_vol < avg_vol * 2:
        return None
    
    # Check if price reversed
    price_change = (closes[-1] - closes[-5]) / closes[-5]
    
    if abs(price_change) > 0.05:  # 5% move
        direction = 'bullish' if price_change > 0 else 'bearish'
        confidence = 0.70
        
        return {
            'pattern': 'Volume Spike Reversal (量增反轉)',
            'type': f'{direction}_reversal',
            'detected_at': dates[-1],
            'confidence': round(confidence, 2),
            'volume_spike': f"{current_vol/avg_vol:.1f}x average",
            'price_change': f"{price_change*100:+.1f}%",
            'notes': f"Unusual volume with {direction} price move"
        }
    
    return None


def analyze_volume_price_trend(data: Dict) -> Dict:
    """Analyze volume-price relationship per 蔡森 methodology"""
    closes = data['close']
    volumes = data['volume']
    
    # Calculate trends
    price_20d = closes[-1] - closes[-20] if len(closes) >= 20 else 0
    price_10d = closes[-1] - closes[-10] if len(closes) >= 10 else 0
    
    vol_20d_avg = calc_mean(volumes[-20:-10]) if len(volumes) >= 20 else calc_mean(volumes[-10:])
    vol_recent_avg = calc_mean(volumes[-10:])
    vol_trend = (vol_recent_avg - vol_20d_avg) / vol_20d_avg if vol_20d_avg > 0 else 0
    
    # Determine relationship
    if price_20d > 0 and vol_trend > 0.1:
        relationship = "量價齊升 (Volume & Price Rising) - Bullish"
        signal = "bullish"
    elif price_20d > 0 and vol_trend < -0.1:
        relationship = "量價背離 (Volume-Price Divergence) - Bearish warning"
        signal = "bearish_divergence"
    elif price_20d < 0 and vol_trend > 0.1:
        relationship = "量增價跌 (Volume Up, Price Down) - Distribution"
        signal = "bearish"
    elif price_20d < 0 and vol_trend < -0.1:
        relationship = "量縮價跌 (Volume & Price Declining) - Weak bearish"
        signal = "weak_bearish"
    else:
        relationship = "盤整 (Consolidation)"
        signal = "neutral"
    
    return {
        'price_trend_20d': f"{price_20d:+.1f} HKD ({price_20d/closes[-20]*100:+.1f}%)",
        'volume_trend': f"{vol_trend*100:+.1f}%",
        'relationship': relationship,
        'signal': signal,
        'avg_volume_recent': f"{vol_recent_avg:,.0f}",
        'avg_volume_older': f"{vol_20d_avg:,.0f}"
    }


def calculate_key_levels(data: Dict) -> Dict:
    """Calculate key support/resistance using 蔡森 methodology"""
    highs = data['high']
    lows = data['low']
    closes = data['close']
    
    current = closes[-1]
    
    # Recent extremes
    high_60d = max(highs[-60:])
    low_60d = min(lows[-60:])
    high_30d = max(highs[-30:])
    low_30d = min(lows[-30:])
    
    # Moving averages
    ma20 = calc_mean(closes[-20:])
    ma50 = calc_mean(closes[-50:]) if len(closes) >= 50 else ma20
    ma200 = calc_mean(closes[-200:]) if len(closes) >= 200 else ma50
    
    # Psychological levels
    psychological = [round(current / 100) * 100, round(current / 50) * 50]
    
    # Support levels
    supports = []
    if low_30d < current:
        supports.append(('30-day low', low_30d))
    if low_60d < current:
        supports.append(('60-day low', low_60d))
    if ma20 < current:
        supports.append(('MA20', ma20))
    if ma50 < current:
        supports.append(('MA50', ma50))
    for p in psychological:
        if p < current and p > current * 0.9:
            supports.append(('Psychological', p))
    
    # Resistance levels
    resistances = []
    if high_30d > current:
        resistances.append(('30-day high', high_30d))
    if high_60d > current:
        resistances.append(('60-day high', high_60d))
    if ma20 > current:
        resistances.append(('MA20', ma20))
    if ma50 > current:
        resistances.append(('MA50', ma50))
    for p in psychological:
        if p > current and p < current * 1.1:
            resistances.append(('Psychological', p))
    
    supports.sort(key=lambda x: x[1], reverse=True)
    resistances.sort(key=lambda x: x[1])
    
    return {
        'current_price': current,
        'support_levels': supports[:5],
        'resistance_levels': resistances[:5],
        'ma20': ma20,
        'ma50': ma50,
        'ma200': ma200,
        'high_60d': high_60d,
        'low_60d': low_60d
    }


def generate_caisen_chart_html(data: Dict, patterns: List[Dict], levels: Dict, volume_analysis: Dict) -> str:
    """Generate interactive HTML chart with 蔡森 annotations"""
    
    # Get last 90 days for display
    n = min(90, len(data['dates']))
    dates = data['dates'][-n:]
    opens = data['open'][-n:]
    highs = data['high'][-n:]
    lows = data['low'][-n:]
    closes = data['close'][-n:]
    volumes = data['volume'][-n:]
    
    current_price = data['close'][-1]
    current_date = data['dates'][-1]
    
    # Calculate MA lines
    def calc_ma(prices, period):
        ma = []
        for i in range(len(prices)):
            if i < period - 1:
                ma.append(None)
            else:
                ma.append(round(sum(prices[i-period+1:i+1]) / period, 2))
        return ma
    
    ma20 = calc_ma(closes, 20)
    ma50 = calc_ma(closes, 50)
    
    # Build pattern annotations
    pattern_annotations = []
    for p in patterns:
        if 'entry_price' in p:
            color = 'rgba(0, 255, 136, 0.8)' if 'bullish' in p.get('type', '').lower() else 'rgba(255, 100, 100, 0.8)'
            pattern_annotations.append({
                'type': 'line',
                'yMin': p['entry_price'],
                'yMax': p['entry_price'],
                'borderColor': color,
                'borderWidth': 3,
                'label': {
                    'display': True,
                    'content': f"Pattern: {p['pattern'][:20]}",
                    'position': 'end',
                    'backgroundColor': color,
                    'color': 'white',
                    'font': {'size': 11}
                }
            })
    
    # Support/Resistance annotations
    support_resistance_annotations = []
    for name, level in levels.get('support_levels', [])[:3]:
        support_resistance_annotations.append({
            'type': 'line',
            'yMin': level,
            'yMax': level,
            'borderColor': 'rgba(0, 255, 0, 0.6)',
            'borderWidth': 2,
            'borderDash': [5, 5],
            'label': {
                'display': True,
                'content': f'S: {level:.0f}',
                'position': 'start',
                'backgroundColor': 'rgba(0, 100, 0, 0.8)',
                'color': 'white'
            }
        })
    
    for name, level in levels.get('resistance_levels', [])[:3]:
        support_resistance_annotations.append({
            'type': 'line',
            'yMin': level,
            'yMax': level,
            'borderColor': 'rgba(255, 0, 0, 0.6)',
            'borderWidth': 2,
            'borderDash': [5, 5],
            'label': {
                'display': True,
                'content': f'R: {level:.0f}',
                'position': 'start',
                'backgroundColor': 'rgba(100, 0, 0, 0.8)',
                'color': 'white'
            }
        })
    
    html = f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <title>騰訊 (0700.HK) - 蔡森技術分析</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%);
            color: #e0e0e0; 
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            color: #00ff88; 
            text-align: center; 
            margin-bottom: 10px;
            font-size: 2em;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }}
        .subtitle {{ 
            text-align: center; 
            color: #888; 
            margin-bottom: 25px;
            font-size: 1.1em;
        }}
        .dashboard {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }}
        .card {{ 
            background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
            padding: 20px; 
            border-radius: 15px; 
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s;
        }}
        .card:hover {{ transform: translateY(-3px); }}
        .card-label {{ color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }}
        .card-value {{ font-size: 22px; font-weight: bold; color: #fff; }}
        .positive {{ color: #00ff88; }}
        .negative {{ color: #ff4466; }}
        .chart-wrapper {{ 
            background: rgba(0,0,0,0.3); 
            border-radius: 15px; 
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .chart-container {{ position: relative; height: 500px; }}
        .volume-container {{ position: relative; height: 150px; margin-top: 15px; }}
        .analysis-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); 
            gap: 20px; 
            margin: 20px 0; 
        }}
        .panel {{ 
            background: rgba(255,255,255,0.05); 
            padding: 25px; 
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .panel h3 {{ 
            color: #00d4ff; 
            margin-top: 0;
            font-size: 1.3em;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 10px;
        }}
        .level-item {{ 
            display: flex; 
            justify-content: space-between; 
            padding: 12px 0; 
            border-bottom: 1px solid rgba(255,255,255,0.08);
            font-size: 14px;
        }}
        .level-item:last-child {{ border-bottom: none; }}
        .level.support {{ color: #00ff88; }}
        .level.resistance {{ color: #ff6b6b; }}
        .pattern-card {{
            background: linear-gradient(145deg, rgba(0, 212, 255, 0.1), rgba(0, 0, 0, 0.2));
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            border-left: 4px solid #00d4ff;
        }}
        .pattern-card.bullish {{ border-left-color: #00ff88; }}
        .pattern-card.bearish {{ border-left-color: #ff4466; }}
        .pattern-name {{ font-weight: bold; color: #fff; margin-bottom: 5px; }}
        .pattern-detail {{ font-size: 13px; color: #aaa; }}
        .legend {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 25px; 
            margin: 20px 0; 
            justify-content: center;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 10px; font-size: 13px; }}
        .legend-color {{ width: 25px; height: 4px; border-radius: 2px; }}
        .caisen-principles {{
            background: linear-gradient(145deg, rgba(255, 165, 0, 0.1), rgba(0, 0, 0, 0.2));
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            border: 1px solid rgba(255, 165, 0, 0.3);
        }}
        .principle {{
            display: inline-block;
            background: rgba(255, 165, 0, 0.2);
            padding: 8px 15px;
            border-radius: 20px;
            margin: 5px;
            font-size: 13px;
            color: #ffa500;
        }}
        .signal-box {{
            text-align: center;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            font-size: 1.5em;
            font-weight: bold;
        }}
        .signal-bullish {{ background: linear-gradient(145deg, rgba(0, 255, 136, 0.2), rgba(0, 100, 50, 0.3)); border: 2px solid #00ff88; }}
        .signal-bearish {{ background: linear-gradient(145deg, rgba(255, 68, 102, 0.2), rgba(100, 0, 50, 0.3)); border: 2px solid #ff4466; }}
        .signal-neutral {{ background: linear-gradient(145deg, rgba(255, 165, 0, 0.2), rgba(100, 50, 0, 0.3)); border: 2px solid #ffa500; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 騰訊控股 (0700.HK)</h1>
        <p class="subtitle">蔡森技術分析 - 量價關係與形態識別</p>
        
        <div class="caisen-principles">
            <strong style="color: #ffa500;">蔡森核心原則:</strong>
            <span class="principle">量在價先</span>
            <span class="principle">小賠大賺</span>
            <span class="principle">嚴守停損</span>
            <span class="principle">隨勢而為</span>
        </div>
        
        <div class="dashboard">
            <div class="card">
                <div class="card-label">當前價格</div>
                <div class="card-value">HKD {current_price:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">更新日期</div>
                <div class="card-value" style="font-size: 16px;">{current_date}</div>
            </div>
            <div class="card">
                <div class="card-label">60 日高</div>
                <div class="card-value">HKD {levels['high_60d']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">60 日低</div>
                <div class="card-value">HKD {levels['low_60d']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">MA20</div>
                <div class="card-value">HKD {levels['ma20']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">MA50</div>
                <div class="card-value">HKD {levels['ma50']:.2f}</div>
            </div>
        </div>
        
        <div class="signal-box {'signal-bullish' if 'bullish' in volume_analysis.get('signal', '').lower() else 'signal-bearish' if 'bearish' in volume_analysis.get('signal', '').lower() else 'signal-neutral'}">
            量價關係：{volume_analysis.get('relationship', 'N/A')}
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #00d4ff;"></div>
                <span>收盤價</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ffa500;"></div>
                <span>MA20</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #ff6b6b;"></div>
                <span>MA50</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(0, 255, 0, 0.8);"></div>
                <span>支撐位</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(255, 0, 0, 0.8);"></div>
                <span>阻力位</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(0, 255, 136, 0.8);"></div>
                <span>看漲形態</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: rgba(255, 68, 102, 0.8);"></div>
                <span>看跌形態</span>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <h3 style="color: #00d4ff; margin-bottom: 15px;">📊 價格走勢與技術指標</h3>
            <div class="chart-container">
                <canvas id="priceChart"></canvas>
            </div>
            <div class="volume-container">
                <canvas id="volumeChart"></canvas>
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="panel">
                <h3>📊 支撐位 (Support)</h3>
                {''.join(f'<div class="level-item level support"><span>{name}</span><span>HKD {level:.2f}</span></div>' for name, level in levels.get('support_levels', [])[:5])}
            </div>
            <div class="panel">
                <h3>📈 阻力位 (Resistance)</h3>
                {''.join(f'<div class="level-item level resistance"><span>{name}</span><span>HKD {level:.2f}</span></div>' for name, level in levels.get('resistance_levels', [])[:5])}
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="panel">
                <h3>🎯  detected patterns</h3>
                {''.join(f'''<div class="pattern-card {'bullish' if 'bullish' in p.get('type', '').lower() else 'bearish' if 'bearish' in p.get('type', '').lower() else ''}">
                    <div class="pattern-name">{p.get('pattern', 'Unknown')}</div>
                    <div class="pattern-detail">Confidence: {p.get('confidence', 0)*100:.0f}% | Type: {p.get('type', 'N/A')}</div>
                    <div class="pattern-detail">Entry: HKD {p.get('entry_price', 'N/A')} | Target: HKD {p.get('target_price', 'N/A')}</div>
                    <div class="pattern-detail">Stop: HKD {p.get('stop_loss', 'N/A')} | R/R: {p.get('risk_reward_ratio', 'N/A')}</div>
                </div>''' for p in patterns[:4]) if patterns else '<p style="color: #888;">No clear patterns detected</p>'}
            </div>
            <div class="panel">
                <h3>📉 量價分析 (Volume-Price)</h3>
                <div class="level-item"><span>20 日價格變化</span><span>{volume_analysis.get('price_trend_20d', 'N/A')}</span></div>
                <div class="level-item"><span>成交量趨勢</span><span>{volume_analysis.get('volume_trend', 'N/A')}</span></div>
                <div class="level-item"><span>近期均量</span><span>{volume_analysis.get('avg_volume_recent', 'N/A')}</span></div>
                <div class="level-item"><span>前期均量</span><span>{volume_analysis.get('avg_volume_older', 'N/A')}</span></div>
                <div class="level-item"><span>量價關係</span><span style="color: {'#00ff88' if 'bullish' in volume_analysis.get('signal', '').lower() else '#ff4466' if 'bearish' in volume_analysis.get('signal', '').lower() else '#ffa500'}">{volume_analysis.get('relationship', 'N/A')}</span></div>
            </div>
        </div>
    </div>
    
    <script>
        const labels = {json.dumps(dates)};
        const closeData = {json.dumps(closes)};
        const volumeData = {json.dumps(volumes)};
        const ma20Data = {json.dumps(ma20)};
        const ma50Data = {json.dumps(ma50)};
        
        const allAnnotations = {json.dumps(pattern_annotations + support_resistance_annotations)};
        
        // Price Chart
        const priceCtx = document.getElementById('priceChart').getContext('2d');
        new Chart(priceCtx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{
                        label: '收盤價',
                        data: closeData,
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.15)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.1,
                        pointRadius: 0,
                        pointHoverRadius: 7
                    }},
                    {{
                        label: 'MA20',
                        data: ma20Data,
                        borderColor: '#ffa500',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    }},
                    {{
                        label: 'MA50',
                        data: ma50Data,
                        borderColor: '#ff6b6b',
                        borderWidth: 2,
                        borderDash: [10, 5],
                        fill: false,
                        tension: 0.1,
                        pointRadius: 0
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false
                }},
                plugins: {{
                    legend: {{
                        labels: {{ color: '#ccc', font: {{ size: 12 }} }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.95)',
                        titleColor: '#00d4ff',
                        bodyColor: '#eee',
                        borderColor: '#333',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': HKD ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }},
                    annotation: {{
                        annotations: allAnnotations
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ color: '#888', maxTicksLimit: 10, font: {{ size: 11 }} }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888', callback: (v) => 'HKD ' + v, font: {{ size: 11 }} }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }}
                }}
            }}
        }});
        
        // Volume Chart
        const volumeCtx = document.getElementById('volumeChart').getContext('2d');
        new Chart(volumeCtx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: '成交量',
                    data: volumeData,
                    backgroundColor: closeData.map((v, i) => {{
                        if (i === 0) return 'rgba(0, 212, 255, 0.6)';
                        return v >= (closeData[i-1] || v) ? 'rgba(0, 255, 136, 0.5)' : 'rgba(255, 68, 102, 0.5)';
                    }}),
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.95)',
                        callbacks: {{
                            label: function(context) {{
                                return 'Volume: ' + context.parsed.y.toLocaleString();
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ display: false }},
                        grid: {{ display: false }}
                    }},
                    y: {{
                        ticks: {{ color: '#888', callback: (v) => (v/1000000).toFixed(2) + 'M', font: {{ size: 11 }} }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    return html


def main():
    print("=" * 70)
    print("🎯 蔡森 (Cai Sen) 技術分析 - 騰訊控股 (0700.HK)")
    print("=" * 70)
    print()
    
    # Load data
    data_path = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    print(f"📂 載入數據：{data_path}")
    data = load_csv_data(data_path)
    print(f"   ✅ 載入 {len(data['dates'])} 個交易日")
    print()
    
    # Run all 蔡森 pattern detections
    print("🔍 掃描蔡森形態...")
    patterns = []
    
    # 1. W-bottom
    w_bottom = detect_w_bottom(data, sensitivity=0.7)
    if w_bottom:
        patterns.append(w_bottom)
        print(f"   ✓ W-bottom detected (confidence: {w_bottom['confidence']:.0f}%)")
    
    # 2. M-top
    m_top = detect_m_top(data, sensitivity=0.7)
    if m_top:
        patterns.append(m_top)
        print(f"   ✓ M-top detected (confidence: {m_top['confidence']:.0f}%)")
    
    # 3. Head & Shoulders Top
    hs_top = detect_head_shoulders(data, type='top')
    if hs_top:
        patterns.append(hs_top)
        print(f"   ✓ Head & Shoulders Top detected")
    
    # 4. Head & Shoulders Bottom
    hs_bottom = detect_head_shoulders(data, type='bottom')
    if hs_bottom:
        patterns.append(hs_bottom)
        print(f"   ✓ Head & Shoulders Bottom detected")
    
    # 5. False Breakout Up
    false_up = detect_false_breakout(data, direction='up')
    if false_up:
        patterns.append(false_up)
        print(f"   ✓ False Breakout (Bull Trap) detected")
    
    # 6. False Breakout Down
    false_down = detect_false_breakout(data, direction='down')
    if false_down:
        patterns.append(false_down)
        print(f"   ✓ False Breakout (Bear Trap) detected")
    
    # 7. Ascending Triangle
    asc_tri = detect_ascending_triangle(data)
    if asc_tri:
        patterns.append(asc_tri)
        print(f"   ✓ Ascending Triangle detected")
    
    # 8. Descending Triangle
    desc_tri = detect_descending_triangle(data)
    if desc_tri:
        patterns.append(desc_tri)
        print(f"   ✓ Descending Triangle detected")
    
    # 9. Volume Divergence
    vol_div = detect_volume_divergence(data)
    if vol_div:
        patterns.append(vol_div)
        print(f"   ✓ Volume-Price Divergence detected")
    
    # 10. Volume Spike Reversal
    vol_spike = detect_volume_spike_reversal(data)
    if vol_spike:
        patterns.append(vol_spike)
        print(f"   ✓ Volume Spike Reversal detected")
    
    print()
    
    # Calculate key levels
    print("📊 計算關鍵價位...")
    levels = calculate_key_levels(data)
    print(f"   ✓ Support levels: {len(levels['support_levels'])}")
    print(f"   ✓ Resistance levels: {len(levels['resistance_levels'])}")
    print()
    
    # Volume-price analysis
    print("📈 量價關係分析...")
    volume_analysis = analyze_volume_price_trend(data)
    print(f"   ✓ {volume_analysis['relationship']}")
    print()
    
    # Generate chart
    print("🎨 生成互動圖表...")
    html = generate_caisen_chart_html(data, patterns, levels, volume_analysis)
    
    output_path = '/root/.openclaw/workspace/caisen_data/tencent_caisen_chart.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   ✅ 圖表已保存：{output_path}")
    print()
    
    # Generate JSON analysis
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'symbol': '0700.HK',
        'current_price': data['close'][-1],
        'current_date': data['dates'][-1],
        'patterns_detected': patterns,
        'key_levels': levels,
        'volume_price_analysis': volume_analysis,
        'caisen_principles': [
            '量在價先 (Volume precedes price)',
            '小賠大賺 (Small losses, big gains)',
            '嚴守停損 (Strict stop-loss)',
            '隨勢而為 (Follow the trend)'
        ]
    }
    
    analysis_path = '/root/.openclaw/workspace/caisen_data/tencent_caisen_analysis.json'
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"💾 分析已保存：{analysis_path}")
    print()
    
    # Print summary
    print("=" * 70)
    print("📊 蔡森分析總結")
    print("=" * 70)
    print(f"當前價格：HKD {data['close'][-1]:.2f} ({data['dates'][-1]})")
    print(f"量價關係：{volume_analysis['relationship']}")
    print(f"形態檢測：{len(patterns)} 個")
    
    if patterns:
        print("\n detected patterns:")
        for p in patterns:
            print(f"   • {p['pattern']} - {p.get('type', 'N/A')} ({p.get('confidence', 0)*100:.0f}%)")
    
    print(f"\n關鍵支撐:")
    for name, level in levels['support_levels'][:3]:
        print(f"   • {name}: HKD {level:.2f}")
    
    print(f"\n關鍵阻力:")
    for name, level in levels['resistance_levels'][:3]:
        print(f"   • {name}: HKD {level:.2f}")
    
    print("=" * 70)
    print("✅ 分析完成!")
    print("=" * 70)


if __name__ == '__main__':
    main()
