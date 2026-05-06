#!/usr/bin/env python3
"""
蔡森 (Cai Sen) Current Technical Analysis for Tencent (0700.HK)

Focus: Recent 90-day analysis with current patterns and volume-price relationship
"""

import csv
import json
import math
from datetime import datetime
from typing import Dict, List, Optional

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


def calc_mean(values: List[float]) -> float:
    """Calculate mean"""
    return sum(values) / len(values) if values else 0


def find_local_extrema(prices: List[float], valley: bool, order: int = 5) -> List[int]:
    """Find local peaks or valleys"""
    indices = []
    for i in range(order, len(prices) - order):
        if valley:
            is_extremum = all(prices[i] <= prices[i-j] for j in range(1, order+1))
            is_extremum = is_extremum and all(prices[i] <= prices[i+j] for j in range(1, order+1))
        else:
            is_extremum = all(prices[i] >= prices[i-j] for j in range(1, order+1))
            is_extremum = is_extremum and all(prices[i] >= prices[i+j] for j in range(1, order+1))
        if is_extremum:
            indices.append(i)
    return indices


def analyze_recent_patterns(data: Dict, window: int = 90) -> List[Dict]:
    """Analyze patterns in recent data only"""
    patterns = []
    
    # Slice recent data
    dates = data['dates'][-window:]
    opens = data['open'][-window:]
    highs = data['high'][-window:]
    lows = data['low'][-window:]
    closes = data['close'][-window:]
    volumes = data['volume'][-window:]
    
    current_price = closes[-1]
    
    # 1. Check for Descending Triangle (下降三角形) - Bearish
    # Look for flat support and declining highs
    if len(highs) >= 40:
        first_half_highs = highs[:20]
        second_half_highs = highs[20:40]
        
        if calc_mean(second_half_highs) < calc_mean(first_half_highs) * 0.97:
            # Highs are declining
            recent_lows = lows[-25:]
            low_range = (max(recent_lows) - min(recent_lows)) / min(recent_lows)
            
            if low_range < 0.05:  # Flat support
                support = min(recent_lows)
                
                # Check if recently broke down
                if closes[-1] < support * 1.02 and closes[-1] > support * 0.97:
                    patterns.append({
                        'pattern': 'Descending Triangle (下降三角形)',
                        'type': 'bearish',
                        'status': 'Active - Testing Support',
                        'confidence': 0.70,
                        'key_level': support,
                        'notes': f"Support at HKD {support:.2f} being tested. Breakdown = bearish continuation."
                    })
    
    # 2. Check for potential W-bottom forming (雙重底)
    valleys = find_local_extrema(lows, valley=True, order=8)
    if len(valleys) >= 2:
        v1, v2 = valleys[-2], valleys[-1]
        low1, low2 = lows[v1], lows[v2]
        
        # Check if two lows are similar (within 5%)
        diff_pct = abs(low1 - low2) / min(low1, low2)
        if diff_pct < 0.05:
            neckline_idx = v1 + max(range(v1, v2+1), key=lambda x: highs[x])
            neckline = highs[neckline_idx]
            
            # Check volume on second bottom
            vol1 = volumes[v1]
            vol2 = volumes[v2]
            volume_declining = vol2 < vol1
            
            patterns.append({
                'pattern': 'Potential W-Bottom (潛在雙重底)',
                'type': 'bullish',
                'status': 'Forming',
                'confidence': 0.55 if volume_declining else 0.45,
                'first_bottom': f"HKD {low1:.2f} ({dates[v1]})",
                'second_bottom': f"HKD {low2:.2f} ({dates[v2]})",
                'neckline': f"HKD {neckline:.2f}",
                'volume_trend': 'Declining (good)' if volume_declining else 'Not declining',
                'notes': f"Watch for breakout above {neckline:.0f} with volume for bullish confirmation."
            })
    
    # 3. Check for M-top (雙重頂) - already happened in Jan 2026
    peaks = find_local_extrema(highs, valley=False, order=8)
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        high1, high2 = highs[p1], highs[p2]
        
        diff_pct = abs(high1 - high2) / max(high1, high2)
        if diff_pct < 0.08:
            # Check if second peak is lower (bearish)
            second_lower = high2 < high1
            
            # Volume check
            vol1 = volumes[p1]
            vol2 = volumes[p2]
            vol_divergence = vol2 < vol1 * 0.8
            
            patterns.append({
                'pattern': 'M-Top Formation (雙重頂形態)',
                'type': 'bearish',
                'status': 'Completed',
                'confidence': 0.75 if second_lower and vol_divergence else 0.60,
                'first_peak': f"HKD {high1:.2f} ({dates[p1]})",
                'second_peak': f"HKD {high2:.2f} ({dates[p2]})",
                'volume_divergence': 'Yes - Bearish' if vol_divergence else 'No',
                'notes': f"Second peak {'lower' if second_lower else 'higher'}. Price has declined from peaks."
            })
    
    # 4. Volume analysis patterns
    avg_vol_30 = calc_mean(volumes[-30:-10])
    recent_vol = calc_mean(volumes[-10:])
    vol_change = (recent_vol - avg_vol_30) / avg_vol_30
    
    # Check for volume spike on down days
    for i in range(max(0, len(closes)-15), len(closes)-1):
        if closes[i] < closes[i-1] * 0.97:  # Down day >3%
            if volumes[i] > avg_vol_30 * 2:  # Volume spike
                patterns.append({
                    'pattern': 'Volume Spike on Decline (下跌放量)',
                    'type': 'bearish',
                    'status': 'Recent',
                    'date': dates[i],
                    'confidence': 0.75,
                    'volume_ratio': f"{volumes[i]/avg_vol_30:.1f}x average",
                    'price_change': f"{(closes[i]-closes[i-1])/closes[i-1]*100:.1f}%",
                    'notes': "Heavy selling volume - distribution pattern"
                })
                break
    
    # 5. Check for consolidation/range pattern
    recent_range_high = max(highs[-20:])
    recent_range_low = min(lows[-20:])
    range_pct = (recent_range_high - recent_range_low) / recent_range_low
    
    if range_pct < 0.08:  # Less than 8% range
        patterns.append({
            'pattern': 'Consolidation (盤整)',
            'type': 'neutral',
            'status': 'Active',
            'confidence': 0.65,
            'range_high': f"HKD {recent_range_high:.2f}",
            'range_low': f"HKD {recent_range_low:.2f}",
            'range_pct': f"{range_pct*100:.1f}%",
            'notes': f"Price consolidating in {range_pct*100:.0f}% range. Watch for breakout direction."
        })
    
    return patterns


def analyze_volume_price_relationship(data: Dict) -> Dict:
    """Detailed volume-price analysis per 蔡森 methodology"""
    closes = data['close']
    volumes = data['volume']
    
    # Multiple timeframes
    analysis = {}
    
    # 10-day
    price_10d = closes[-1] - closes[-10]
    vol_10d_avg = calc_mean(volumes[-10:])
    vol_prev_10d = calc_mean(volumes[-20:-10])
    
    # 20-day
    price_20d = closes[-1] - closes[-20]
    vol_20d_avg = calc_mean(volumes[-20:])
    vol_prev_20d = calc_mean(volumes[-40:-20]) if len(volumes) > 40 else vol_20d_avg
    
    # Determine relationship
    def get_relationship(price_change, vol_change):
        if price_change > 0 and vol_change > 0.1:
            return "量價齊升 (Volume & Price Rising)", "bullish"
        elif price_change > 0 and vol_change < -0.1:
            return "量價背離 (Divergence - Price up, Volume down)", "bearish_warning"
        elif price_change < 0 and vol_change > 0.1:
            return "量增價跌 (Volume Up, Price Down - Distribution)", "bearish"
        elif price_change < 0 and vol_change < -0.1:
            return "量縮價跌 (Volume & Price Declining)", "weak_bearish"
        else:
            return "盤整 (Consolidation)", "neutral"
    
    vol_change_10d = (vol_10d_avg - vol_prev_10d) / vol_prev_10d if vol_prev_10d > 0 else 0
    vol_change_20d = (vol_20d_avg - vol_prev_20d) / vol_prev_20d if vol_prev_20d > 0 else 0
    
    rel_10d, signal_10d = get_relationship(price_10d, vol_change_10d)
    rel_20d, signal_20d = get_relationship(price_20d, vol_change_20d)
    
    # Overall assessment
    if signal_10d == "bearish" or signal_20d == "bearish":
        overall_signal = "bearish"
    elif signal_10d == "bearish_warning" or signal_20d == "bearish_warning":
        overall_signal = "caution"
    elif signal_10d == "bullish" or signal_20d == "bullish":
        overall_signal = "bullish"
    else:
        overall_signal = "neutral"
    
    return {
        'short_term': {
            'price_change_10d': f"{price_10d:+.1f} HKD ({price_10d/closes[-10]*100:+.1f}%)",
            'volume_change': f"{vol_change_10d*100:+.1f}%",
            'relationship': rel_10d,
            'signal': signal_10d
        },
        'medium_term': {
            'price_change_20d': f"{price_20d:+.1f} HKD ({price_20d/closes[-20]*100:+.1f}%)",
            'volume_change': f"{vol_change_20d*100:+.1f}%",
            'relationship': rel_20d,
            'signal': signal_20d
        },
        'overall': {
            'signal': overall_signal,
            'avg_volume_current': f"{vol_10d_avg:,.0f}",
            'avg_volume_previous': f"{vol_prev_10d:,.0f}"
        }
    }


def calculate_key_levels(data: Dict) -> Dict:
    """Calculate key support/resistance levels"""
    highs = data['high']
    lows = data['low']
    closes = data['close']
    
    current = closes[-1]
    
    # Recent extremes
    high_90d = max(highs[-90:])
    low_90d = min(lows[-90:])
    high_30d = max(highs[-30:])
    low_30d = min(lows[-30:])
    high_10d = max(highs[-10:])
    low_10d = min(lows[-10:])
    
    # Moving averages
    ma5 = calc_mean(closes[-5:])
    ma10 = calc_mean(closes[-10:])
    ma20 = calc_mean(closes[-20:])
    ma50 = calc_mean(closes[-50:]) if len(closes) >= 50 else ma20
    ma200 = calc_mean(closes[-200:]) if len(closes) >= 200 else ma50
    
    # Gap analysis
    gaps = []
    for i in range(1, min(90, len(closes))):
        # Gap up: today's low > yesterday's high
        if lows[-i] > highs[-i-1] * 1.02:
            gaps.append(('Gap Up', lows[-i], highs[-i-1]))
        # Gap down: today's high < yesterday's low
        elif highs[-i] < lows[-i-1] * 0.98:
            gaps.append(('Gap Down', highs[-i], lows[-i-1]))
    
    # Support levels (below current price)
    supports = []
    if low_10d < current:
        supports.append(('10-day low', low_10d, 'Near-term'))
    if low_30d < current:
        supports.append(('30-day low', low_30d, 'Short-term'))
    if low_90d < current:
        supports.append(('90-day low', low_90d, 'Medium-term'))
    if ma20 < current:
        supports.append(('MA20', ma20, 'Dynamic'))
    if ma50 < current:
        supports.append(('MA50', ma50, 'Dynamic'))
    if ma200 < current:
        supports.append(('MA200', ma200, 'Long-term'))
    
    # Psychological levels
    for level in [500, 520, 550, 600]:
        if level < current and level > current * 0.9:
            supports.append((f'Psychological {level}', level, 'Psychological'))
    
    # Resistance levels (above current price)
    resistances = []
    if high_10d > current:
        resistances.append(('10-day high', high_10d, 'Near-term'))
    if high_30d > current:
        resistances.append(('30-day high', high_30d, 'Short-term'))
    if high_90d > current:
        resistances.append(('90-day high', high_90d, 'Medium-term'))
    if ma20 > current:
        resistances.append(('MA20', ma20, 'Dynamic'))
    if ma50 > current:
        resistances.append(('MA50', ma50, 'Dynamic'))
    
    for level in [520, 550, 600, 650]:
        if level > current and level < current * 1.15:
            resistances.append((f'Psychological {level}', level, 'Psychological'))
    
    supports.sort(key=lambda x: x[1], reverse=True)
    resistances.sort(key=lambda x: x[1])
    
    return {
        'current_price': current,
        'current_date': data['dates'][-1],
        'support_levels': supports[:6],
        'resistance_levels': resistances[:6],
        'moving_averages': {
            'MA5': ma5,
            'MA10': ma10,
            'MA20': ma20,
            'MA50': ma50,
            'MA200': ma200
        },
        'extremes': {
            'high_90d': high_90d,
            'low_90d': low_90d,
            'high_30d': high_30d,
            'low_30d': low_30d
        }
    }


def generate_caisen_html_report(data: Dict, patterns: List[Dict], levels: Dict, vp_analysis: Dict) -> str:
    """Generate comprehensive HTML report with working chart"""
    
    # Get last 90 days
    n = min(90, len(data['dates']))
    dates = data['dates'][-n:]
    opens = data['open'][-n:]
    highs = data['high'][-n:]
    lows = data['low'][-n:]
    closes = data['close'][-n:]
    volumes = data['volume'][-n:]
    
    current_price = data['close'][-1]
    current_date = data['dates'][-1]
    
    # Calculate MAs
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
    
    # Support/resistance as horizontal line datasets (no annotation plugin needed)
    support_level = levels['support_levels'][0][1] if levels['support_levels'] else 510
    resistance_level = levels['resistance_levels'][0][1] if levels['resistance_levels'] else 550
    
    html = f'''<!DOCTYPE html>
<html lang="zh-HK">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>騰訊 (0700.HK) - 蔡森技術分析報告</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js"></script>
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
            font-size: 2.2em;
            text-shadow: 0 0 20px rgba(0, 255, 136, 0.3);
        }}
        .subtitle {{ 
            text-align: center; 
            color: #888; 
            margin-bottom: 25px;
            font-size: 1.2em;
        }}
        .dashboard {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); 
            gap: 15px; 
            margin: 20px 0; 
        }}
        .card {{ 
            background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
            padding: 18px; 
            border-radius: 12px; 
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }}
        .card-label {{ color: #888; font-size: 11px; text-transform: uppercase; margin-bottom: 8px; }}
        .card-value {{ font-size: 20px; font-weight: bold; color: #fff; }}
        .positive {{ color: #00ff88; }}
        .negative {{ color: #ff4466; }}
        .chart-section {{ 
            background: rgba(0,0,0,0.3); 
            border-radius: 15px; 
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        .price-chart {{ position: relative; height: 450px; margin-bottom: 20px; }}
        .volume-chart {{ position: relative; height: 120px; }}
        .analysis-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); 
            gap: 20px; 
            margin: 20px 0; 
        }}
        .panel {{ 
            background: rgba(255,255,255,0.05); 
            padding: 22px; 
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .panel h3 {{ 
            color: #00d4ff; 
            margin-top: 0;
            font-size: 1.25em;
            border-bottom: 2px solid rgba(0, 212, 255, 0.3);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        .level-item {{ 
            display: flex; 
            justify-content: space-between; 
            padding: 10px 0; 
            border-bottom: 1px solid rgba(255,255,255,0.06);
            font-size: 14px;
        }}
        .level-item:last-child {{ border-bottom: none; }}
        .level.support {{ color: #00ff88; }}
        .level.resistance {{ color: #ff6b6b; }}
        .pattern-card {{
            background: linear-gradient(145deg, rgba(0, 212, 255, 0.08), rgba(0, 0, 0, 0.15));
            padding: 15px;
            border-radius: 10px;
            margin: 12px 0;
            border-left: 4px solid #00d4ff;
        }}
        .pattern-card.bullish {{ border-left-color: #00ff88; background: linear-gradient(145deg, rgba(0, 255, 136, 0.08), rgba(0, 0, 0, 0.15)); }}
        .pattern-card.bearish {{ border-left-color: #ff4466; background: linear-gradient(145deg, rgba(255, 68, 102, 0.08), rgba(0, 0, 0, 0.15)); }}
        .pattern-name {{ font-weight: bold; color: #fff; margin-bottom: 6px; font-size: 14px; }}
        .pattern-detail {{ font-size: 12px; color: #aaa; line-height: 1.6; }}
        .legend {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 20px; 
            margin: 20px 0; 
            justify-content: center;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; font-size: 12px; }}
        .legend-color {{ width: 22px; height: 4px; border-radius: 2px; }}
        .principles {{
            background: linear-gradient(145deg, rgba(255, 165, 0, 0.08), rgba(0, 0, 0, 0.15));
            padding: 18px;
            border-radius: 12px;
            margin: 20px 0;
            border: 1px solid rgba(255, 165, 0, 0.25);
            text-align: center;
        }}
        .principle {{
            display: inline-block;
            background: rgba(255, 165, 0, 0.15);
            padding: 8px 14px;
            border-radius: 20px;
            margin: 5px;
            font-size: 13px;
            color: #ffa500;
        }}
        .signal-box {{
            text-align: center;
            padding: 18px;
            border-radius: 12px;
            margin: 20px 0;
            font-size: 1.3em;
            font-weight: bold;
        }}
        .signal-bullish {{ background: linear-gradient(145deg, rgba(0, 255, 136, 0.15), rgba(0, 100, 50, 0.25)); border: 2px solid #00ff88; }}
        .signal-bearish {{ background: linear-gradient(145deg, rgba(255, 68, 102, 0.15), rgba(100, 0, 50, 0.25)); border: 2px solid #ff4466; }}
        .signal-caution {{ background: linear-gradient(145deg, rgba(255, 165, 0, 0.15), rgba(100, 50, 0, 0.25)); border: 2px solid #ffa500; }}
        .signal-neutral {{ background: linear-gradient(145deg, rgba(100, 100, 100, 0.15), rgba(50, 50, 50, 0.25)); border: 2px solid #888; }}
        .ma-status {{ font-size: 13px; padding: 6px 0; }}
        .ma-above {{ color: #00ff88; }}
        .ma-below {{ color: #ff4466; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 騰訊控股 (0700.HK)</h1>
        <p class="subtitle">蔡森技術分析報告 | 量價關係與形態識別</p>
        
        <div class="principles">
            <strong style="color: #ffa500;">蔡森核心原則:</strong><br>
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
                <div class="card-value" style="font-size: 14px;">{current_date}</div>
            </div>
            <div class="card">
                <div class="card-label">90 日高</div>
                <div class="card-value">HKD {levels['extremes']['high_90d']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">90 日低</div>
                <div class="card-value">HKD {levels['extremes']['low_90d']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">MA20</div>
                <div class="card-value">HKD {levels['moving_averages']['MA20']:.2f}</div>
            </div>
            <div class="card">
                <div class="card-label">MA50</div>
                <div class="card-value">HKD {levels['moving_averages']['MA50']:.2f}</div>
            </div>
        </div>
        
        <div class="signal-box {'signal-bearish' if vp_analysis['overall']['signal'] == 'bearish' else 'signal-caution' if vp_analysis['overall']['signal'] == 'caution' else 'signal-bullish' if vp_analysis['overall']['signal'] == 'bullish' else 'signal-neutral'}">
            量價關係：{vp_analysis['medium_term']['relationship']}
        </div>
        
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background: #00d4ff;"></div><span>收盤價</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #ffa500;"></div><span>MA20</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #ff6b6b;"></div><span>MA50</span></div>
            <div class="legend-item"><div class="legend-color" style="background: rgba(0, 255, 136, 0.8);"></div><span>支撐位</span></div>
            <div class="legend-item"><div class="legend-color" style="background: rgba(255, 100, 100, 0.8);"></div><span>阻力位</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #00ff88;"></div><span>看漲形態</span></div>
            <div class="legend-item"><div class="legend-color" style="background: #ff4466;"></div><span>看跌形態</span></div>
        </div>
        
        <div class="chart-section">
            <h3 style="color: #00d4ff; margin-bottom: 15px;">📊 價格走勢與技術指標 (90 日)</h3>
            <div class="price-chart">
                <canvas id="priceChart"></canvas>
            </div>
            <div class="volume-chart">
                <canvas id="volumeChart"></canvas>
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="panel">
                <h3>📊 支撐位 (Support Levels)</h3>
                {''.join(f'<div class="level-item level support"><span>{name}</span><span>HKD {level:.2f}</span></div>' for name, level, _ in levels['support_levels'][:5])}
            </div>
            <div class="panel">
                <h3>📈 阻力位 (Resistance Levels)</h3>
                {''.join(f'<div class="level-item level resistance"><span>{name}</span><span>HKD {level:.2f}</span></div>' for name, level, _ in levels['resistance_levels'][:5])}
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="panel">
                <h3>🎯  detected patterns</h3>
                {''.join(f'''<div class="pattern-card {'bullish' if p.get('type') == 'bullish' else 'bearish' if p.get('type') == 'bearish' else ''}">
                    <div class="pattern-name">{p.get('pattern', 'Unknown')}</div>
                    <div class="pattern-detail"><strong>狀態:</strong> {p.get('status', 'N/A')} | <strong>信心度:</strong> {p.get('confidence', 0)*100:.0f}%</div>
                    <div class="pattern-detail">{p.get('notes', '')}</div>
                </div>''' for p in patterns[:5]) if patterns else '<p style="color: #888;">近期無明確形態</p>'}
            </div>
            <div class="panel">
                <h3>📉 量價分析 (Volume-Price)</h3>
                <div class="level-item"><span>10 日價格</span><span>{vp_analysis['short_term']['price_change_10d']}</span></div>
                <div class="level-item"><span>10 日成交量</span><span>{vp_analysis['short_term']['volume_change']}</span></div>
                <div class="level-item"><span>10 日關係</span><span>{vp_analysis['short_term']['relationship']}</span></div>
                <div class="level-item"><span>20 日價格</span><span>{vp_analysis['medium_term']['price_change_20d']}</span></div>
                <div class="level-item"><span>20 日成交量</span><span>{vp_analysis['medium_term']['volume_change']}</span></div>
                <div class="level-item"><span>20 日關係</span><span>{vp_analysis['medium_term']['relationship']}</span></div>
                <div class="level-item"><span>目前均量</span><span>{vp_analysis['overall']['avg_volume_current']}</span></div>
                <div class="level-item"><span>前期均量</span><span>{vp_analysis['overall']['avg_volume_previous']}</span></div>
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="panel">
                <h3>📐 移動平均線狀態</h3>
                <div class="ma-status {'ma-above' if current_price > levels['moving_averages']['MA5'] else 'ma-below'}">MA5:  HKD {levels['moving_averages']['MA5']:.2f} {'↑ 價格之上' if current_price > levels['moving_averages']['MA5'] else '↓ 價格之下'}</div>
                <div class="ma-status {'ma-above' if current_price > levels['moving_averages']['MA10'] else 'ma-below'}">MA10: HKD {levels['moving_averages']['MA10']:.2f} {'↑ 價格之上' if current_price > levels['moving_averages']['MA10'] else '↓ 價格之下'}</div>
                <div class="ma-status {'ma-above' if current_price > levels['moving_averages']['MA20'] else 'ma-below'}">MA20: HKD {levels['moving_averages']['MA20']:.2f} {'↑ 價格之上' if current_price > levels['moving_averages']['MA20'] else '↓ 價格之下'}</div>
                <div class="ma-status {'ma-above' if current_price > levels['moving_averages']['MA50'] else 'ma-below'}">MA50: HKD {levels['moving_averages']['MA50']:.2f} {'↑ 價格之上' if current_price > levels['moving_averages']['MA50'] else '↓ 價格之下'}</div>
                <div class="ma-status {'ma-above' if current_price > levels['moving_averages']['MA200'] else 'ma-below'}">MA200: HKD {levels['moving_averages']['MA200']:.2f} {'↑ 價格之上' if current_price > levels['moving_averages']['MA200'] else '↓ 價格之下'}</div>
            </div>
            <div class="panel">
                <h3>💡 蔡森操作建議</h3>
                <div class="level-item"><span>目前信號</span><span style="color: {'#00ff88' if vp_analysis['overall']['signal'] == 'bullish' else '#ff4466' if vp_analysis['overall']['signal'] == 'bearish' else '#ffa500'}">{vp_analysis['overall']['signal'].upper()}</span></div>
                <div class="level-item"><span>關鍵支撐</span><span>HKD {levels['support_levels'][0][1] if levels['support_levels'] else 'N/A'}</span></div>
                <div class="level-item"><span>關鍵阻力</span><span>HKD {levels['resistance_levels'][0][1] if levels['resistance_levels'] else 'N/A'}</span></div>
                <div class="level-item"><span>止損建議</span><span>跌破 {levels['support_levels'][0][1] if levels['support_levels'] else 'N/A'} 減倉</span></div>
                <div class="level-item"><span>加倉信號</span><span>突破 {levels['resistance_levels'][0][1] if levels['resistance_levels'] else 'N/A'} 且放量</span></div>
            </div>
        </div>
    </div>
    
    <script>
        const labels = {json.dumps(dates)};
        const closeData = {json.dumps(closes)};
        const ma20Data = {json.dumps(ma20)};
        const ma50Data = {json.dumps(ma50)};
        const volumeData = {json.dumps(volumes)};
        const supportLevel = {support_level};
        const resistanceLevel = {resistance_level};
        
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
                    }},
                    {{
                        label: '支撐 ' + supportLevel,
                        data: Array(labels.length).fill(supportLevel),
                        borderColor: 'rgba(0, 255, 136, 0.6)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        tension: 0
                    }},
                    {{
                        label: '阻力 ' + resistanceLevel,
                        data: Array(labels.length).fill(resistanceLevel),
                        borderColor: 'rgba(255, 68, 102, 0.6)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        tension: 0
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
                        labels: {{ color: '#ccc', font: {{ size: 11 }} }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.95)',
                        titleColor: '#00d4ff',
                        bodyColor: '#eee',
                        borderColor: '#333',
                        borderWidth: 1,
                        padding: 10,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': HKD ' + context.parsed.y.toFixed(2);
                            }}
                        }}
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
                        const prevClose = closeData[i-1] || v;
                        return v >= prevClose ? 'rgba(0, 255, 136, 0.5)' : 'rgba(255, 68, 102, 0.5)';
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
    print("🎯 蔡森 (Cai Sen) 當前技術分析 - 騰訊控股 (0700.HK)")
    print("=" * 70)
    print()
    
    # Load data
    data_path = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    print(f"📂 載入數據：{data_path}")
    data = load_csv_data(data_path)
    print(f"   ✅ 載入 {len(data['dates'])} 個交易日")
    print()
    
    # Analyze recent patterns (90-day focus)
    print("🔍 掃描近期形態 (90 日)...")
    patterns = analyze_recent_patterns(data, window=90)
    for p in patterns:
        print(f"   • {p['pattern']} - {p.get('type', 'N/A')} ({p.get('confidence', 0)*100:.0f}%)")
    print()
    
    # Volume-price analysis
    print("📈 量價關係分析...")
    vp_analysis = analyze_volume_price_relationship(data)
    print(f"   短期 (10 日): {vp_analysis['short_term']['relationship']}")
    print(f"   中期 (20 日): {vp_analysis['medium_term']['relationship']}")
    print(f"   整體信號：{vp_analysis['overall']['signal'].upper()}")
    print()
    
    # Key levels
    print("📊 計算關鍵價位...")
    levels = calculate_key_levels(data)
    print(f"   支撐位：{len(levels['support_levels'])} 個")
    print(f"   阻力位：{len(levels['resistance_levels'])} 個")
    print()
    
    # Generate HTML report
    print("🎨 生成互動圖表報告...")
    html = generate_caisen_html_report(data, patterns, levels, vp_analysis)
    
    output_path = '/root/.openclaw/workspace/caisen_data/tencent_caisen_current_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   ✅ 報告已保存：{output_path}")
    
    # Save JSON analysis
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'symbol': '0700.HK',
        'current_price': data['close'][-1],
        'current_date': data['dates'][-1],
        'patterns': patterns,
        'key_levels': levels,
        'volume_price_analysis': vp_analysis
    }
    
    json_path = '/root/.openclaw/workspace/caisen_data/tencent_caisen_current_analysis.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"   💾 JSON 已保存：{json_path}")
    print()
    
    # Summary
    print("=" * 70)
    print("📊 蔡森分析總結")
    print("=" * 70)
    print(f"當前價格：HKD {data['close'][-1]:.2f} ({data['dates'][-1]})")
    print(f"整體信號：{vp_analysis['overall']['signal'].upper()}")
    print(f"量價關係：{vp_analysis['medium_term']['relationship']}")
    print(f"\n detected patterns: {len(patterns)}")
    for p in patterns:
        print(f"   • {p['pattern']} [{p.get('type', 'N/A')}]")
    
    print(f"\n關鍵支撐:")
    for name, level, _ in levels['support_levels'][:3]:
        print(f"   • {name}: HKD {level:.2f}")
    
    print(f"\n關鍵阻力:")
    for name, level, _ in levels['resistance_levels'][:3]:
        print(f"   • {name}: HKD {level:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ 分析完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()
