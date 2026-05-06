#!/usr/bin/env python3
"""
OpenRouter LLM Integration for 蔡森 (Cai Sen) Analysis - ENHANCED VERSION

Enhanced with deep 蔡森 methodology research:
- 量在價先 (Volume precedes price) - Primary focus
- 型態大於指標 (Patterns > Indicators) - No MA reliance
- 突破點/跌破點 (Breakout/Breakdown points) - Key entry signals
- 破底翻 (Spring/False Breakdown) - Bottom reversal pattern
- 假突破 (False Breakout) - Top reversal warning
- 波段漲幅/跌幅 (Swing gain/loss measurement) - Target calculation
- 頸線 (Neckline) - Critical support/resistance levels
- 6+ months historical data for proper pattern context

Provides:
- analyze_chart_image: Send chart images to vision-capable LLM with 蔡森 methodology
- analyze_ohlc_data: Text-based analysis with volume-price focus
- detect_breakout_points: Algorithmic breakout/breakdown detection
- calculate_swing_targets: Measure pattern height for target projection
- combine_signals: Merge algorithmic and LLM analysis
"""

import json
import os
import urllib.request
import ssl
import math
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

# ============================================================================
# Configuration Loading
# ============================================================================

def load_config() -> Dict:
    """Load API configuration from caisen_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'caisen_config.json')
    if not os.path.exists(config_path):
        config_path = '/root/.openclaw/workspace/caisen_config.json'
    
    with open(config_path, 'r') as f:
        return json.load(f)


# ============================================================================
# OpenRouter API Integration
# ============================================================================

def call_openrouter(messages: list, model: str = None, max_tokens: int = 1000, temperature: float = 0.3) -> Dict:
    """Make API call to OpenRouter"""
    config = load_config()
    openrouter_config = config.get('openrouter', config)
    api_key = openrouter_config.get('api_key')
    base_url = openrouter_config.get('base_url', 'https://openrouter.ai/api/v1')
    if not model:
        model = openrouter_config.get('default_model', 'google/gemini-2.0-flash-001')
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    url = f"{base_url}/chat/completions"
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/caisen-trading",
        "X-Title": "CaiSen Trading Analysis - Enhanced"
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=90, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    
    except Exception as e:
        return {
            'error': str(e),
            'choices': [{'message': {'content': f"API Error: {e}"}}]
        }


# ============================================================================
# 蔡森 Methodology - Core Principles (Research-Based)
# ============================================================================

CAISEN_CORE_PRINCIPLES = """
蔡森's Core Trading Philosophy (based on 30+ years of research):

1. 量在價先 (Volume Precedes Price)
   - Volume is the LEADING indicator, price follows
   - Watch volume FIRST, then price action
   - Volume confirms breakouts, warns of reversals
   - "問題量" (Problem Volume) = volume-price divergence

2. 型態大於指標 (Patterns > Indicators)
   - Price patterns are MORE important than oscillators (MACD, KD, RSI)
   - Moving averages are SECONDARY, not primary signals
   - Focus on: W-bottom, M-top, Head & Shoulders, Triangles, Flags
   - Patterns show institutional accumulation/distribution

3. 突破點與跌破點 (Breakout & Breakdown Points)
   - Most EFFICIENT entry points
   - Wait for neckline突破 (breakout) before entering
   - Breakout must be accompanied by INCREASED volume
   - False breakouts (假突破) are major reversal signals

4. 破底翻 (Spring / False Breakdown)
   - Price breaks below support, then quickly reverses back
   - Indicates institutional "stop hunting" and accumulation
   - High-probability BUY signal when market is in uptrend
   - Stop loss: below the false breakdown low

5. 假突破 (False Breakout)
   - Price breaks above resistance but fails to continue
   - Strong SELL signal, especially at market tops
   - Often accompanied by heavy volume (distribution)
   - "會漲很慢，跌會很快" - Upside slow, downside fast

6. 漲幅滿足 / 跌幅滿足 (Measured Moves)
   - Pattern height = projected target distance
   - W-bottom: neckline to bottom → add to breakout point
   - First target: 1x pattern height
   - Second target: 2x pattern height (if momentum continues)
   - Take profits at measured move targets

7. 隨勢而為 (Follow the Trend)
   - Trade WITH the market trend, not against it
   - 破底翻 success rate: 70-80% in bull market, 50% in bear/sideways
   - Check broader market context before individual stocks

8. 小賠大賺 (Small Losses, Big Gains)
   - Cut losses quickly (near cost basis)
   - Let profits run to measured move targets
   - Risk/Reward ratio minimum 1:2.5
   - Strict stop-loss discipline (嚴守停損)

9. 頸線 (Neckline) - Critical Levels
   - Support becomes resistance, resistance becomes support
   - Breakout above neckline = BUY signal
   - Breakdown below neckline = SELL signal
   - After breakout, neckline becomes support (hold above it)

10. 三心 (Three Mindsets)
    - 耐心 (Patience): Wait for pattern completion
    - 決心 (Decisiveness): Enter when signal triggers
    - 平常心 (Equanimity): Don't panic on normal volatility
"""

CAISEN_12_PATTERNS_DETAILED = """
蔡森's 12 Key Patterns - Detailed Specifications:

BOTTOM PATTERNS (Bullish):
1. W-bottom (雙重底)
   - Two lows at similar level (within 3-5%)
   - Second bottom often slightly higher (stronger)
   - Volume: lighter on second bottom
   - Entry: Breakout above neckline with volume
   - Target: Neckline + (Neckline - Bottom)
   - Stop: Below neckline or below bottom low

2. 破底翻 (Spring / False Breakdown)
   - Price breaks below established support
   - Quickly reverses back above support (1-3 days)
   - Volume: heavy on reversal day
   - Entry: When price closes back above support
   - Target: Previous resistance level
   - Stop: Below the false breakdown low

3. 頭肩底 (Head & Shoulders Bottom)
   - Left shoulder, lower head, right shoulder
   - Right shoulder volume > left shoulder volume
   - Entry: Breakout above neckline
   - Target: Neckline + (Neckline - Head low)
   - Stop: Below right shoulder

4. 收斂三角形底部 (Ascending Triangle)
   - Flat resistance, rising support
   - Volume contracts during consolidation
   - Entry: Breakout above flat resistance
   - Target: Resistance + (Resistance - Lowest support)
   - Stop: Below ascending trendline

5. 下飄旗形 (Bullish Flag)
   - Sharp rally (flagpole), then downward consolidation
   - Consolidation volume < rally volume
   - Entry: Breakout above flag upper boundary
   - Target: Flagpole height added to breakout
   - Stop: Below flag lower boundary

6. 碗型底 (Bowl Bottom / Rounding Bottom)
   - Gradual U-shaped bottom formation
   - Volume: high on left, low at bottom, high on right
   - Entry: Breakout above rim level
   - Target: Rim + (Rim - Bottom)
   - Stop: Below recent support in bowl

TOP PATTERNS (Bearish):
7. M-top (雙重頂)
   - Two peaks at similar level (within 3-5%)
   - Second peak often on lower volume (divergence)
   - Entry: Breakdown below neckline
   - Target: Neckline - (Peak - Neckline)
   - Stop: Above second peak

8. 假突破 (False Breakout)
   - Price breaks above resistance but closes back below
   - Often on heavy volume (distribution)
   - Entry: When price falls back below resistance
   - Target: Previous support level
   - Stop: Above the false breakout high

9. 頭肩頂 (Head & Shoulders Top)
   - Left shoulder, higher head, right shoulder
   - Right shoulder volume < left shoulder volume
   - Entry: Breakdown below neckline
   - Target: Neckline - (Head high - Neckline)
   - Stop: Above right shoulder

10. 收斂三角形頭部 (Descending Triangle)
    - Flat support, declining resistance
    - Volume contracts during consolidation
    - Entry: Breakdown below flat support
    - Target: Support - (Highest resistance - Support)
    - Stop: Above descending trendline

11. 上飄旗形 (Bearish Flag)
    - Sharp decline (flagpole), then upward consolidation
    - Consolidation volume < decline volume
    - Entry: Breakdown below flag lower boundary
    - Target: Flagpole height subtracted from breakdown
    - Stop: Above flag upper boundary

INTERMEDIATE / WARNING PATTERNS:
12. 問題量 (Problem Volume)
    - Volume-price divergence warning
    - Price up, volume down = weak rally
    - Price down, volume up = heavy distribution
    - Not a direct entry signal, but WARNING to exit
    - Watch for reversal patterns following problem volume

TIME-BASED:
13. 時間波 (Time Waves)
    - Cyclical timing patterns
    - Markets move in rhythmic waves
    - Use for timing entries/exits within patterns
    - Often 3-5 day, 13-21 day, 55 day cycles
"""


# ============================================================================
# Volume-Price Analysis (蔡森 Core Methodology)
# ============================================================================

def analyze_volume_price_relationship(data: Dict) -> Dict:
    """
    Analyze volume-price relationships per 蔡森 methodology
    
    Focus: 量在價先 (Volume precedes price)
    """
    n = len(data['close'])
    if n < 20:
        return {'error': 'Insufficient data'}
    
    closes = data['close']
    volumes = data['volume']
    highs = data['high']
    lows = data['low']
    
    # Recent 20 days
    recent_vol = volumes[-20:]
    recent_close = closes[-20:]
    
    # Volume trend
    vol_ma10 = sum(recent_vol[-10:]) / 10
    vol_ma20 = sum(recent_vol) / 20
    vol_trend = 'increasing' if vol_ma10 > vol_ma20 * 1.1 else ('decreasing' if vol_ma10 < vol_ma20 * 0.9 else 'flat')
    
    # Price trend
    price_change_20d = (closes[-1] - closes[-20]) / closes[-20] * 100
    price_trend = 'uptrend' if price_change_20d > 5 else ('downtrend' if price_change_20d < -5 else 'sideways')
    
    # Volume-Price Divergence Detection (問題量)
    divergence = None
    divergence_note = ""
    
    if price_trend == 'uptrend' and vol_trend == 'decreasing':
        divergence = 'bearish'
        divergence_note = "價格上漲但成交量萎縮 - 多頭力道減弱 (Price up, volume down - bullish momentum weakening)"
    elif price_trend == 'downtrend' and vol_trend == 'increasing':
        divergence = 'bearish'
        divergence_note = "價格下跌且成交量放大 - 賣壓沉重 (Price down on heavy volume - heavy selling pressure)"
    elif price_trend == 'uptrend' and vol_trend == 'increasing':
        divergence = 'confirming'
        divergence_note = "價量齊揚 - 多頭健康 (Price and volume both rising - healthy uptrend)"
    elif price_trend == 'downtrend' and vol_trend == 'decreasing':
        divergence = 'weak_bearish'
        divergence_note = "下跌量縮 - 賣壓減輕但尚未反轉 (Decline on low volume - selling pressure easing but no reversal yet)"
    
    # Recent volume spikes
    avg_vol = sum(volumes[-60:]) / min(60, len(volumes))
    volume_spikes = []
    for i in range(-20, 0):
        if volumes[i] > avg_vol * 2.0:
            volume_spikes.append({
                'date': data['dates'][i] if 'dates' in data else f'day_{n+i}',
                'volume': volumes[i],
                'volume_ratio': volumes[i] / avg_vol,
                'price_change': (closes[i] - closes[i-1]) / closes[i-1] * 100 if i > -n+1 else 0
            })
    
    # Accumulation/Distribution detection
    # Rising price + rising volume = accumulation
    # Falling price + rising volume = distribution
    recent_direction = []
    for i in range(-10, 0):
        if closes[i] > closes[i-1] and volumes[i] > volumes[i-1]:
            recent_direction.append('accumulation')
        elif closes[i] < closes[i-1] and volumes[i] > volumes[i-1]:
            recent_direction.append('distribution')
    
    accumulation_count = recent_direction.count('accumulation')
    distribution_count = recent_direction.count('distribution')
    
    institutional_activity = 'accumulation' if accumulation_count > distribution_count * 1.5 else \
                            ('distribution' if distribution_count > accumulation_count * 1.5 else 'neutral')
    
    return {
        'volume_trend': vol_trend,
        'price_trend': price_trend,
        'price_change_20d_pct': round(price_change_20d, 2),
        'volume_ma10': round(vol_ma10, 0),
        'volume_ma20': round(vol_ma20, 0),
        'volume_change_pct': round((vol_ma10 - vol_ma20) / vol_ma20 * 100, 2) if vol_ma20 > 0 else 0,
        'divergence': divergence,
        'divergence_note': divergence_note,
        'volume_spikes': volume_spikes[-5:],  # Last 5 spikes
        'institutional_activity': institutional_activity,
        'accumulation_days': accumulation_count,
        'distribution_days': distribution_count,
        'caisen_interpretation': interpret_volume_price(caisen_core=True, 
                                                         divergence=divergence,
                                                         institutional_activity=institutional_activity)
    }


def interpret_volume_price(caisen_core: bool = True, divergence: str = None, 
                          institutional_activity: str = 'neutral') -> str:
    """Interpret volume-price relationship using 蔡森 principles"""
    
    if divergence == 'bearish':
        return "⚠️ 問題量警示：價量背離，趨勢可能反轉。蔡森提醒：量在價先，成交量發出警告訊號。"
    elif divergence == 'confirming':
        return "✅ 價量健康：成交量確認價格走勢，趨勢延續機率高。"
    elif institutional_activity == 'accumulation':
        return "📈 主力收集跡象：近期買超天數多於賣超，可能正在打底或準備突破。"
    elif institutional_activity == 'distribution':
        return "📉 主力出貨跡象：近期賣超天數多於買超，可能正在盤頭或準備跌破。"
    else:
        return "⏸️ 盤整格局：成交量無明顯方向，等待突破訊號。蔡森建議：耐心等待型態完成。"


# ============================================================================
# Breakout & Breakdown Detection (突破點 / 跌破點)
# ============================================================================

def find_neckline_levels(data: Dict, lookback_days: int = 120) -> Dict:
    """
    Find key neckline (頸線) levels using 蔡森 methodology
    
    Neckline: Critical support/resistance that defines patterns
    """
    n = min(lookback_days, len(data['close']))
    highs = data['high'][-n:]
    lows = data['low'][-n:]
    closes = data['close'][-n:]
    dates = data['dates'][-n:] if 'dates' in data else [f'day_{i}' for i in range(n)]
    
    # Find significant resistance levels (peaks)
    resistance_levels = []
    support_levels = []
    
    # Find local maxima (resistance)
    for i in range(5, len(highs) - 5):
        is_peak = all(highs[i] >= highs[i-j] for j in range(1, 6)) and \
                  all(highs[i] >= highs[i+j] for j in range(1, 6))
        if is_peak:
            # Check if this level has been tested multiple times
            touches = sum(1 for h in highs[max(0,i-30):i+1] if abs(h - highs[i]) / highs[i] < 0.03)
            if touches >= 2:
                resistance_levels.append({
                    'price': highs[i],
                    'date': dates[i],
                    'touches': touches,
                    'strength': 'strong' if touches >= 3 else 'moderate'
                })
    
    # Find local minima (support)
    for i in range(5, len(lows) - 5):
        is_valley = all(lows[i] <= lows[i-j] for j in range(1, 6)) and \
                    all(lows[i] <= lows[i+j] for j in range(1, 6))
        if is_valley:
            touches = sum(1 for l in lows[max(0,i-30):i+1] if abs(l - lows[i]) / lows[i] < 0.03)
            if touches >= 2:
                support_levels.append({
                    'price': lows[i],
                    'date': dates[i],
                    'touches': touches,
                    'strength': 'strong' if touches >= 3 else 'moderate'
                })
    
    # Remove duplicates (levels within 2% of each other)
    def deduplicate_levels(levels, tolerance=0.02):
        if not levels:
            return []
        levels = sorted(levels, key=lambda x: x['price'], reverse=True)
        result = [levels[0]]
        for level in levels[1:]:
            if abs(level['price'] - result[-1]['price']) / result[-1]['price'] > tolerance:
                result.append(level)
        return result
    
    resistance_levels = deduplicate_levels(resistance_levels)
    support_levels = deduplicate_levels(support_levels, tolerance=0.02)
    
    # Current price context
    current_price = closes[-1]
    
    # Immediate levels
    immediate_resistance = min([r['price'] for r in resistance_levels if r['price'] > current_price], default=None)
    immediate_support = max([s['price'] for s in support_levels if s['price'] < current_price], default=None)
    
    return {
        'resistance_levels': resistance_levels[:5],  # Top 5
        'support_levels': support_levels[:5],  # Top 5
        'immediate_resistance': immediate_resistance,
        'immediate_support': immediate_support,
        'current_price': current_price,
        'distance_to_resistance': ((immediate_resistance - current_price) / current_price * 100) if immediate_resistance else None,
        'distance_to_support': ((current_price - immediate_support) / immediate_support * 100) if immediate_support else None,
    }


def detect_breakout_points(data: Dict) -> List[Dict]:
    """
    Detect breakout (突破點) and breakdown (跌破點) signals
    
    Per 蔡森: "最有效率的操作是找到突破點和跌破點"
    """
    n = len(data['close'])
    if n < 60:
        return []
    
    closes = data['close']
    highs = data['high']
    lows = data['low']
    volumes = data['volume']
    dates = data['dates'] if 'dates' in data else [f'day_{i}' for i in range(n)]
    
    breakouts = []
    
    # Get neckline levels
    neckline_data = find_neckline_levels(data, lookback_days=180)
    
    # Check for breakouts above resistance
    for res in neckline_data['resistance_levels']:
        res_price = res['price']
        
        # Look for breakout in last 10 days
        for i in range(-10, 0):
            idx = n + i
            if idx < 60:
                continue
                
            # Did price close above resistance?
            if closes[idx] > res_price and closes[idx-1] <= res_price:
                # Check volume confirmation
                vol_ratio = volumes[idx] / (sum(volumes[idx-10:idx]) / 10)
                volume_confirmed = vol_ratio > 1.3
                
                # Check if it held (not a false breakout yet)
                days_held = 0
                for j in range(idx, min(idx+5, n)):
                    if closes[j] < res_price:
                        break
                    days_held += 1
                
                is_false_breakout = days_held < 2 and closes[-1] < res_price
                
                breakout_type = 'false_breakout' if is_false_breakout else \
                               ('confirmed_breakout' if days_held >= 3 and volume_confirmed else 'potential_breakout')
                
                breakouts.append({
                    'type': 'breakout',
                    'subtype': breakout_type,
                    'level': res_price,
                    'breakout_date': dates[idx],
                    'breakout_price': closes[idx],
                    'volume_ratio': round(vol_ratio, 2),
                    'volume_confirmed': volume_confirmed,
                    'days_held': days_held,
                    'current_status': 'failed' if closes[-1] < res_price else 'holding',
                    'caisen_signal': 'SELL - 假突破' if is_false_breakout else ('BUY - 突破確認' if breakout_type == 'confirmed_breakout' else '觀望')
                })
    
    # Check for breakdowns below support
    for sup in neckline_data['support_levels']:
        sup_price = sup['price']
        
        for i in range(-10, 0):
            idx = n + i
            if idx < 60:
                continue
            
            # Did price close below support?
            if closes[idx] < sup_price and closes[idx-1] >= sup_price:
                vol_ratio = volumes[idx] / (sum(volumes[idx-10:idx]) / 10)
                
                days_held = 0
                for j in range(idx, min(idx+5, n)):
                    if closes[j] > sup_price:
                        break
                    days_held += 1
                
                # Check for 破底翻 (spring) - breakdown that quickly reverses
                is_spring = days_held < 3 and closes[-1] > sup_price
                
                breakdown_type = 'spring' if is_spring else \
                                ('confirmed_breakdown' if days_held >= 3 else 'potential_breakdown')
                
                breakouts.append({
                    'type': 'breakdown',
                    'subtype': breakdown_type,
                    'level': sup_price,
                    'breakdown_date': dates[idx],
                    'breakdown_price': closes[idx],
                    'volume_ratio': round(vol_ratio, 2),
                    'days_below': days_held,
                    'current_status': 'reversed' if closes[-1] > sup_price else 'holding',
                    'caisen_signal': 'BUY - 破底翻' if is_spring else ('SELL - 跌破確認' if breakdown_type == 'confirmed_breakdown' else '觀望')
                })
    
    return breakouts


# ============================================================================
# Pattern Detection with 蔡森 Methodology
# ============================================================================

def detect_spring_pattern(data: Dict) -> Optional[Dict]:
    """
    Detect 破底翻 (Spring / False Breakdown) pattern
    
    Characteristics:
    - Price breaks below established support
    - Quickly reverses back above support (1-5 days)
    - Volume increases on reversal
    - High-probability buy signal
    """
    n = len(data['close'])
    if n < 60:
        return None
    
    closes = data['close']
    lows = data['low']
    highs = data['high']
    volumes = data['volume']
    dates = data['dates'] if 'dates' in data else [f'day_{i}' for i in range(n)]
    
    # Find support level (area tested multiple times)
    support_levels = find_neckline_levels(data, lookback_days=120)['support_levels']
    
    if not support_levels:
        return None
    
    for support in support_levels[:3]:  # Check top 3 support levels
        sup_price = support['price']
        
        # Look for breakdown in last 20 days
        for i in range(-20, -2):
            idx = n + i
            
            # Check if price broke below support
            if lows[idx] < sup_price * 0.97:  # At least 3% below
                # Check if price recovered back above support within 5 days
                recovery_found = False
                recovery_idx = None
                max_recovery_days = 5
                
                for j in range(idx+1, min(idx+1+max_recovery_days, n)):
                    if closes[j] > sup_price:
                        recovery_found = True
                        recovery_idx = j
                        break
                
                if recovery_found:
                    # Check volume on recovery day
                    vol_on_recovery = volumes[recovery_idx]
                    avg_vol_before = sum(volumes[idx:recovery_idx]) / (recovery_idx - idx)
                    volume_confirmed = vol_on_recovery > avg_vol_before * 1.2
                    
                    # Calculate entry, stop, target
                    entry_price = sup_price  # Enter when back above support
                    stop_loss = lows[idx] * 0.97  # Below spring low
                    pattern_height = sup_price - lows[idx]
                    target_price = sup_price + pattern_height  # Measured move
                    
                    risk = entry_price - stop_loss
                    reward = target_price - entry_price
                    risk_reward = reward / risk if risk > 0 else 0
                    
                    return {
                        'pattern': '破底翻 (Spring)',
                        'pattern_type': 'bullish_reversal',
                        'support_level': sup_price,
                        'spring_low': lows[idx],
                        'spring_date': dates[idx],
                        'recovery_date': dates[recovery_idx],
                        'recovery_price': closes[recovery_idx],
                        'volume_confirmed': volume_confirmed,
                        'entry_price': round(entry_price, 2),
                        'stop_loss': round(stop_loss, 2),
                        'target_price': round(target_price, 2),
                        'risk_reward_ratio': round(risk_reward, 2),
                        'confidence': 0.75 if volume_confirmed else 0.60,
                        'caisen_notes': '破底翻是主力甩轎動作，清洗浮額後拉升，勝率在大盤多頭時可達 7-8 成',
                        'signal': 'BUY'
                    }
    
    return None


def detect_false_breakout_pattern(data: Dict) -> Optional[Dict]:
    """
    Detect 假突破 (False Breakout) pattern
    
    Characteristics:
    - Price breaks above resistance
    - Fails to continue higher
    - Falls back below resistance level
    - Strong sell signal, especially at tops
    """
    n = len(data['close'])
    if n < 60:
        return None
    
    closes = data['close']
    highs = data['high']
    volumes = data['volume']
    dates = data['dates'] if 'dates' in data else [f'day_{i}' for i in range(n)]
    
    # Find resistance levels
    resistance_levels = find_neckline_levels(data, lookback_days=120)['resistance_levels']
    
    if not resistance_levels:
        return None
    
    for resistance in resistance_levels[:3]:
        res_price = resistance['price']
        
        # Look for breakout attempt in last 20 days
        for i in range(-20, -2):
            idx = n + i
            
            # Check if price broke above resistance
            if highs[idx] > res_price * 1.02:  # At least 2% above
                # Check if price fell back below resistance within 5 days
                failure_found = False
                failure_idx = None
                
                for j in range(idx+1, min(idx+6, n)):
                    if closes[j] < res_price:
                        failure_found = True
                        failure_idx = j
                        break
                
                if failure_found:
                    # Check volume on breakout day (often heavy = distribution)
                    vol_on_breakout = volumes[idx]
                    avg_vol_before = sum(volumes[idx-10:idx]) / 10
                    heavy_volume_on_breakout = vol_on_breakout > avg_vol_before * 1.5
                    
                    # Current price still below resistance?
                    still_below = closes[-1] < res_price
                    
                    if still_below:
                        entry_price = res_price  # Sell when fails at resistance
                        stop_loss = highs[idx] * 1.02  # Above false breakout high
                        pattern_height = res_price - lows[n-60:n].min() if hasattr(lows[n-60:n], 'min') else res_price * 0.1
                        target_price = res_price - pattern_height  # Measured move down
                        
                        risk = stop_loss - entry_price
                        reward = entry_price - target_price
                        risk_reward = reward / risk if risk > 0 else 0
                        
                        return {
                            'pattern': '假突破 (False Breakout)',
                            'pattern_type': 'bearish_reversal',
                            'resistance_level': res_price,
                            'false_breakout_high': highs[idx],
                            'false_breakout_date': dates[idx],
                            'failure_date': dates[failure_idx],
                            'failure_price': closes[failure_idx],
                            'heavy_volume_on_breakout': heavy_volume_on_breakout,
                            'entry_price': round(entry_price, 2),
                            'stop_loss': round(stop_loss, 2),
                            'target_price': round(target_price, 2),
                            'risk_reward_ratio': round(risk_reward, 2),
                            'confidence': 0.80 if heavy_volume_on_breakout else 0.65,
                            'caisen_notes': '假突破是主力出貨訊號，尤其是高檔爆量假突破，跌會很快',
                            'signal': 'SELL'
                        }
    
    return None


# ============================================================================
# Swing Target Calculation (波段漲幅/跌幅滿足)
# ============================================================================

def calculate_swing_targets(data: Dict, pattern_type: str = 'W-bottom') -> Dict:
    """
    Calculate measured move targets (漲幅滿足 / 跌幅滿足)
    
    Per 蔡森: Pattern height = projected target distance
    """
    n = len(data['close'])
    if n < 60:
        return {'error': 'Insufficient data'}
    
    closes = data['close']
    highs = data['high']
    lows = data['low']
    current_price = closes[-1]
    
    # Find recent swing high and low (last 120 days)
    lookback = min(120, n)
    recent_high = max(highs[-lookback:])
    recent_low = min(lows[-lookback:])
    
    # Find neckline level
    neckline_data = find_neckline_levels(data, lookback_days=lookback)
    neckline = neckline_data.get('immediate_resistance') or neckline_data.get('immediate_support') or current_price
    
    targets = {
        'pattern_type': pattern_type,
        'current_price': current_price,
        'recent_swing_high': recent_high,
        'recent_swing_low': recent_low,
        'neckline': neckline,
        'pattern_measurements': []
    }
    
    if pattern_type == 'W-bottom':
        # Find the two bottoms
        valley_indices = []
        for i in range(10, lookback - 10):
            idx = n - lookback + i
            is_valley = all(lows[idx] <= lows[idx-j] for j in range(1, 6)) and \
                        all(lows[idx] <= lows[idx+j] for j in range(1, 6))
            if is_valley:
                valley_indices.append(idx)
        
        if len(valley_indices) >= 2:
            # Take two most recent valleys
            bottom1_idx = valley_indices[-2]
            bottom2_idx = valley_indices[-1]
            bottom_price = min(lows[bottom1_idx], lows[bottom2_idx])
            
            # Find peak between valleys (neckline)
            peak_between = max(highs[bottom1_idx:bottom2_idx+1])
            neckline = peak_between
            
            pattern_height = neckline - bottom_price
            first_target = neckline + pattern_height
            second_target = first_target + pattern_height
            
            targets['pattern_measurements'] = [{
                'pattern': 'W-bottom',
                'bottom_price': round(bottom_price, 2),
                'neckline': round(neckline, 2),
                'pattern_height': round(pattern_height, 2),
                'first_target': round(first_target, 2),
                'second_target': round(second_target, 2),
                'upside_potential_1': round((first_target - current_price) / current_price * 100, 2) if current_price < first_target else 0,
                'upside_potential_2': round((second_target - current_price) / current_price * 100, 2) if current_price < second_target else 0,
                'caisen_method': '底部至頸線距離＝突破後等幅距離'
            }]
    
    elif pattern_type == 'M-top':
        # Find the two peaks
        peak_indices = []
        for i in range(10, lookback - 10):
            idx = n - lookback + i
            is_peak = all(highs[idx] >= highs[idx-j] for j in range(1, 6)) and \
                      all(highs[idx] >= highs[idx+j] for j in range(1, 6))
            if is_peak:
                peak_indices.append(idx)
        
        if len(peak_indices) >= 2:
            peak1_idx = peak_indices[-2]
            peak2_idx = peak_indices[-1]
            peak_price = max(highs[peak1_idx], highs[peak2_idx])
            
            # Find valley between peaks (neckline)
            neckline = min(lows[peak1_idx:peak2_idx+1])
            
            pattern_height = peak_price - neckline
            first_target = neckline - pattern_height
            second_target = first_target - pattern_height
            
            targets['pattern_measurements'] = [{
                'pattern': 'M-top',
                'peak_price': round(peak_price, 2),
                'neckline': round(neckline, 2),
                'pattern_height': round(pattern_height, 2),
                'first_target': round(first_target, 2),
                'second_target': round(second_target, 2),
                'downside_risk_1': round((current_price - first_target) / current_price * 100, 2) if current_price > first_target else 0,
                'downside_risk_2': round((current_price - second_target) / current_price * 100, 2) if current_price > second_target else 0,
                'caisen_method': '頭部至頸線距離＝跌破後等幅距離'
            }]
    
    return targets


# ============================================================================
# LLM Analysis Functions (Enhanced with 蔡森 Methodology)
# ============================================================================

def analyze_chart_image(image_path: str, stock_symbol: str = "0700.HK", 
                       include_volume: bool = True, history_months: int = 6) -> Dict:
    """
    Analyze a chart image using vision-capable LLM with 蔡森 methodology
    
    Args:
        image_path: Path to chart image (PNG/JPG)
        stock_symbol: Stock symbol for context
        include_volume: Ensure volume is shown on chart
        history_months: Minimum months of history (蔡森 recommends 6+ months)
    
    Returns:
        Dict with LLM analysis including pattern detection, entry/exit levels, confidence
    """
    config = load_config()
    
    # Check if image exists
    if not os.path.exists(image_path):
        return {
            'error': f'Image not found: {image_path}',
            'signal': 'HOLD',
            'confidence': 0
        }
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Encode to base64
    import base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Determine MIME type
    mime_type = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'
    
    # Build enhanced prompt with 蔡森 methodology
    system_prompt = f"""你是一位精通蔡森 (Cai Sen) 量價型態學的技術分析專家。

{CAISEN_CORE_PRINCIPLES}

{CAISEN_12_PATTERNS_DETAILED}

請用繁體中文回答，並嚴格遵循蔡森的方法論進行分析。"""

    user_prompt = f"""請分析這張 {stock_symbol} 的股票走勢圖。

【蔡森分析要點】
1. 量價關係：成交量是否確認價格走勢？有無問題量（價量背離）？
2. 型態辨識：圖中可見哪種蔡森 12 型態？（W 底、M 頭、破底翻、假突破等）
3. 頸線位置：關鍵支撐/壓力位在哪裡？
4. 突破/跌破：近期有無突破點或跌破點？是否確認？
5. 波段測幅：若型態完成，漲幅/跌幅滿足目標在哪裡？

【重要提醒】
- 蔡森不重視均線，請專注於「量」與「價」的關係
- 型態大於指標，請優先辨識 K 線型態
- 量在價先，成交量是最領先的訊號
- 請確保圖表包含至少 6 個月歷史資料以正確判斷型態

請以 JSON 格式提供分析結果：

{{
    "patterns_detected": [
        {{
            "name": "型態名稱（中英文）",
            "confidence": 0.0-1.0,
            "description": "你在圖上看到什麼",
            "stage": "forming|confirmed|failed",
            "evidence": "為什麼你認為這是這個型態"
        }}
    ],
    "volume_price_analysis": {{
        "volume_trend": "increasing|decreasing|flat",
        "price_trend": "uptrend|downtrend|sideways",
        "divergence": "none|bearish|confirming",
        "institutional_activity": "accumulation|distribution|neutral",
        "notes": "量價關係觀察"
    }},
    "key_levels": {{
        "neckline": price,
        "immediate_resistance": [price1, price2],
        "immediate_support": [price1, price2],
        "critical_level": price,
        "level_description": "為什麼這個價位關鍵"
    }},
    "breakout_analysis": {{
        "recent_breakout": true|false,
        "breakout_level": price,
        "breakout_confirmed": true|false,
        "is_false_breakout": true|false,
        "is_spring": true|false
    }},
    "swing_targets": {{
        "pattern_height": price,
        "first_target": price,
        "second_target": price,
        "calculation_method": "蔡森測幅方法說明"
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "entry_price": price,
        "stop_loss": price,
        "target_price": price,
        "risk_reward_ratio": ratio,
        "time_horizon_days": number,
        "position_sizing": "建議部位大小"
    }},
    "reasoning": "詳細分析說明（繁體中文）",
    "caisen_principles_applied": ["適用的蔡森原則"],
    "risk_warnings": ["風險提醒"]
}}

請具體指出價位，並用蔡森的方法論計算目標價和停損。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    # Call API with vision model
    result = call_openrouter(messages, model='google/gemini-2.0-flash-001', max_tokens=2000)
    
    if 'error' in result:
        return {
            'error': result.get('error', 'Unknown API error'),
            'signal': 'HOLD',
            'confidence': 0
        }
    
    # Parse response
    try:
        content = result['choices'][0]['message']['content']
        
        # Try to extract JSON from response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            analysis = json.loads(json_str)
        else:
            # Fallback: return raw content
            analysis = {
                'raw_analysis': content,
                'signal': {'direction': 'HOLD', 'confidence': 0.5}
            }
        
        analysis['model_used'] = 'google/gemini-2.0-flash-001'
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['image_analyzed'] = image_path
        analysis['methodology'] = '蔡森量價型態學'
        analysis['history_months'] = history_months
        
        return analysis
    
    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse LLM response: {e}',
            'raw_content': result['choices'][0]['message']['content'] if 'choices' in result else None,
            'signal': 'HOLD',
            'confidence': 0
        }


def analyze_ohlc_data(data_dict: Dict, stock_symbol: str = "0700.HK", 
                      history_months: int = 6) -> Dict:
    """
    Analyze OHLC data using text-based LLM with 蔡森 methodology
    
    Args:
        data_dict: Dict with 'dates', 'open', 'high', 'low', 'close', 'volume' lists
        stock_symbol: Stock symbol
        history_months: Minimum months of data (6+ recommended)
    
    Returns:
        Dict with LLM analysis
    """
    # Ensure we have at least 6 months (~120 trading days)
    n = min(max(120, len(data_dict['close'])), len(data_dict['close']))
    
    # Prepare data for analysis
    recent_data = []
    for i in range(-n, 0):
        recent_data.append({
            'date': data_dict['dates'][i] if 'dates' in data_dict else f'day_{n+i}',
            'open': data_dict['open'][i],
            'high': data_dict['high'][i],
            'low': data_dict['low'][i],
            'close': data_dict['close'][i],
            'volume': data_dict['volume'][i]
        })
    
    # Calculate summary statistics
    current_price = data_dict['close'][-1]
    
    # 6-month high/low
    high_6m = max(data_dict['high'][-n:])
    low_6m = min(data_dict['low'][-n:])
    
    # Price changes
    price_20d_ago = data_dict['close'][-20] if len(data_dict['close']) >= 20 else data_dict['close'][0]
    price_60d_ago = data_dict['close'][-60] if len(data_dict['close']) >= 60 else data_dict['close'][0]
    price_change_20d = ((current_price - price_20d_ago) / price_20d_ago) * 100
    price_change_60d = ((current_price - price_60d_ago) / price_60d_ago) * 100
    
    # Volume analysis
    avg_vol_recent = sum(data_dict['volume'][-10:]) / 10
    avg_vol_older = sum(data_dict['volume'][-30:-10]) / 20 if len(data_dict['volume']) >= 30 else avg_vol_recent
    vol_change_pct = ((avg_vol_recent - avg_vol_older) / avg_vol_older) * 100 if avg_vol_older > 0 else 0
    
    # Run algorithmic analysis first
    vol_price_analysis = analyze_volume_price_relationship(data_dict)
    breakout_points = detect_breakout_points(data_dict)
    spring_pattern = detect_spring_pattern(data_dict)
    false_breakout = detect_false_breakout_pattern(data_dict)
    swing_targets = calculate_swing_targets(data_dict, pattern_type='W-bottom')
    
    # Build enhanced prompt with algorithmic findings
    system_prompt = f"""你是一位精通蔡森 (Cai Sen) 量價型態學的技術分析專家。

{CAISEN_CORE_PRINCIPLES}

蔡森不重視均線（MA），專注於「量」與「價」的關係以及 K 線型態。
請用繁體中文回答。"""

    user_prompt = f"""分析 {stock_symbol} 的量價數據（{n}天，約{n/20:.1f}個月）。

【當前價格】: HKD {current_price:.2f}
【6 個月範圍】: HKD {low_6m:.2f} - HKD {high_6m:.2f}
【20 日漲跌】: {price_change_20d:+.1f}%
【60 日漲跌】: {price_change_60d:+.1f}%
【成交量趨勢】: {vol_change_pct:+.1f}% (近期 vs 前期)

【算法分析結果】
量價關係：{json.dumps(vol_price_analysis, ensure_ascii=False, indent=2)}

突破/跌破點：{json.dumps(breakout_points[-3:], ensure_ascii=False, indent=2) if breakout_points else '無明顯突破'}

破底翻偵測：{json.dumps(spring_pattern, ensure_ascii=False, indent=2) if spring_pattern else '未偵測到'}

假突破偵測：{json.dumps(false_breakout, ensure_ascii=False, indent=2) if false_breakout else '未偵測到'}

波段測幅：{json.dumps(swing_targets, ensure_ascii=False, indent=2)}

【最近 15 天數據】
{json.dumps(recent_data[-15:], ensure_ascii=False, indent=2)}

請根據蔡森方法論提供分析，以 JSON 格式回覆：

{{
    "trend_analysis": {{
        "direction": "uptrend|downtrend|sideways",
        "strength": "strong|moderate|weak",
        "evidence": "說明",
        "market_context": "大盤環境評估"
    }},
    "volume_price_analysis": {{
        "volume_trend": "increasing|decreasing|flat",
        "confirming_price": true|false,
        "divergence_detected": true|false,
        "divergence_type": "none|bearish|confirming",
        "institutional_activity": "accumulation|distribution|neutral",
        "notes": "量價關係觀察（繁體中文）"
    }},
    "patterns_detected": [
        {{
            "name": "型態名稱",
            "confidence": 0.0-1.0,
            "stage": "forming|confirmed|failed",
            "evidence": "為什麼"
        }}
    ],
    "key_levels": {{
        "neckline": price,
        "immediate_resistance": price,
        "strong_resistance": price,
        "immediate_support": price,
        "strong_support": price,
        "notes": "頸線與關鍵價位說明"
    }},
    "breakout_status": {{
        "near_breakout": true|false,
        "breakout_level": price,
        "breakdown_level": price,
        "watch_for": "需要觀察什麼"
    }},
    "swing_targets": {{
        "measured_move_up": price,
        "measured_move_down": price,
        "calculation_basis": "計算基礎"
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "entry_price": price,
        "stop_loss": price,
        "target_price": price,
        "risk_reward_ratio": ratio,
        "position_size_pct": number,
        "reasoning": "訊號理由（繁體中文）"
    }},
    "caisen_principles_applied": ["適用的蔡森原則"],
    "risk_factors": ["風險因素"],
    "action_plan": "具體操作計畫（繁體中文）"
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    result = call_openrouter(messages, model='google/gemini-2.0-flash-001', max_tokens=2000)
    
    if 'error' in result:
        return {
            'error': result.get('error'),
            'signal': 'HOLD',
            'confidence': 0
        }
    
    try:
        content = result['choices'][0]['message']['content']
        
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            analysis = json.loads(json_str)
        else:
            analysis = {
                'raw_analysis': content,
                'signal': {'direction': 'HOLD', 'confidence': 0.5}
            }
        
        # Add algorithmic analysis results
        analysis['algorithmic_analysis'] = {
            'volume_price': vol_price_analysis,
            'breakout_points': breakout_points,
            'spring_pattern': spring_pattern,
            'false_breakout': false_breakout,
            'swing_targets': swing_targets
        }
        
        analysis['model_used'] = 'google/gemini-2.0-flash-001'
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['data_points_analyzed'] = n
        analysis['history_months'] = round(n / 20, 1)
        analysis['methodology'] = '蔡森量價型態學'
        
        return analysis
    
    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse LLM response: {e}',
            'raw_content': result['choices'][0]['message']['content'] if 'choices' in result else None,
            'signal': 'HOLD',
            'confidence': 0
        }


# ============================================================================
# Signal Combination
# ============================================================================

def combine_signals(algorithmic_detection: Dict, llm_analysis: Dict) -> Dict:
    """
    Combine algorithmic pattern detection with LLM analysis
    
    Weighting: 60% algorithmic (objective), 40% LLM (subjective reasoning)
    """
    combined = {
        'timestamp': datetime.now().isoformat(),
        'methodology': '蔡森量價型態學',
        'algorithmic_analysis': algorithmic_detection,
        'llm_analysis': llm_analysis,
        'combined_signal': {}
    }
    
    # Extract algorithmic signal
    algo_signal = algorithmic_detection.get('overall_signal', {})
    algo_direction = algo_signal.get('direction', 'HOLD')
    algo_confidence = algo_signal.get('confidence', 0.5)
    
    # Extract LLM signal
    llm_signal = llm_analysis.get('signal', {})
    llm_direction = llm_signal.get('direction', 'HOLD')
    llm_confidence = llm_signal.get('confidence', 0.5)
    
    # Combine signals with weighting
    direction_scores = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
    
    algo_score = direction_scores.get(algo_direction, 0) * algo_confidence
    llm_score = direction_scores.get(llm_direction, 0) * llm_confidence
    
    weighted_score = (algo_score * 0.6 + llm_score * 0.4)
    
    if weighted_score > 0.3:
        final_direction = 'BUY'
    elif weighted_score < -0.3:
        final_direction = 'SELL'
    else:
        final_direction = 'HOLD'
    
    final_confidence = (algo_confidence * 0.6 + llm_confidence * 0.4)
    
    # Get entry/exit levels (prefer algorithmic)
    entry_price = None
    stop_loss = None
    target_price = None
    
    # Check for specific patterns first
    if algorithmic_detection.get('spring_pattern'):
        spring = algorithmic_detection['spring_pattern']
        entry_price = spring.get('entry_price')
        stop_loss = spring.get('stop_loss')
        target_price = spring.get('target_price')
    elif algorithmic_detection.get('false_breakout'):
        fb = algorithmic_detection['false_breakout']
        entry_price = fb.get('entry_price')
        stop_loss = fb.get('stop_loss')
        target_price = fb.get('target_price')
    elif algorithmic_detection.get('patterns_detected'):
        patterns = algorithmic_detection['patterns_detected']
        if patterns:
            best_pattern = max(patterns, key=lambda x: x.get('confidence', 0))
            entry_price = best_pattern.get('entry_price')
            stop_loss = best_pattern.get('stop_loss')
            target_price = best_pattern.get('target_price')
    
    # Fallback to LLM levels
    if not entry_price and llm_signal:
        entry_price = llm_signal.get('entry_price')
        stop_loss = llm_signal.get('stop_loss')
        target_price = llm_signal.get('target_price')
    
    # Calculate risk/reward
    if entry_price and stop_loss and target_price:
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
    else:
        risk_reward = 0
    
    combined['combined_signal'] = {
        'direction': final_direction,
        'confidence': round(final_confidence, 2),
        'entry_price': round(entry_price, 2) if entry_price else None,
        'stop_loss': round(stop_loss, 2) if stop_loss else None,
        'target_price': round(target_price, 2) if target_price else None,
        'risk_reward_ratio': round(risk_reward, 2),
        'algorithmic_signal': algo_direction,
        'algorithmic_confidence': algo_confidence,
        'llm_signal': llm_direction,
        'llm_confidence': llm_confidence,
        'agreement': algo_direction == llm_direction,
        'reasoning': generate_combined_reasoning(algorithmic_detection, llm_analysis, final_direction),
        'caisen_summary': generate_caisen_summary(algorithmic_detection, llm_analysis)
    }
    
    return combined


def generate_combined_reasoning(algo: Dict, llm: Dict, final_direction: str) -> str:
    """Generate human-readable reasoning for combined signal"""
    parts = []
    
    # Algorithmic patterns
    if algo.get('spring_pattern'):
        parts.append(f"算法偵測到破底翻（Spring）型態，這是蔡森的高勝率買進訊號。")
    elif algo.get('false_breakout'):
        parts.append(f"算法偵測到假突破型態，這是蔡森的重要賣出訊號。")
    
    patterns = algo.get('patterns_detected', [])
    if patterns:
        pattern_names = [p.get('pattern', p.get('name', 'Unknown')) for p in patterns[:3]]
        parts.append(f"算法偵測型態：{', '.join(pattern_names)}。")
    
    # Volume analysis
    vol_analysis = algo.get('volume_price_analysis', {})
    if vol_analysis.get('caisen_interpretation'):
        parts.append(f"量價分析：{vol_analysis['caisen_interpretation']}")
    
    # LLM reasoning
    if 'reasoning' in llm:
        reasoning = llm['reasoning'][:200]
        parts.append(f"LLM 分析：{reasoning}...")
    
    # Agreement/disagreement
    algo_sig = algo.get('overall_signal', {}).get('direction', 'HOLD')
    llm_sig = llm.get('signal', {}).get('direction', 'HOLD')
    
    if algo_sig == llm_sig:
        parts.append(f"✅ 算法與 LLM 分析一致，均為{final_direction}訊號。")
    else:
        parts.append(f"⚠️ 算法 ({algo_sig}) 與 LLM ({llm_sig}) 訊號不同，採用加權平均。")
    
    return " ".join(parts)


def generate_caisen_summary(algo: Dict, llm: Dict) -> str:
    """Generate 蔡森-style summary in Traditional Chinese"""
    summary_parts = []
    
    # Market context
    trend = llm.get('trend_analysis', {}).get('direction', 'sideways')
    if trend == 'uptrend':
        summary_parts.append("【多頭格局】")
    elif trend == 'downtrend':
        summary_parts.append("【空頭格局】")
    else:
        summary_parts.append("【盤整格局】")
    
    # Volume-price
    vol_analysis = algo.get('volume_price_analysis', {})
    divergence = vol_analysis.get('divergence')
    if divergence == 'bearish':
        summary_parts.append("⚠️ 問題量警示")
    elif divergence == 'confirming':
        summary_parts.append("✅ 價量健康")
    
    # Patterns
    if algo.get('spring_pattern'):
        summary_parts.append("📈 破底翻買點")
    if algo.get('false_breakout'):
        summary_parts.append("📉 假突破賣點")
    
    # Signal
    signal = algo.get('overall_signal', {}).get('direction', 'HOLD')
    if signal == 'BUY':
        summary_parts.append("🟢 買進訊號")
    elif signal == 'SELL':
        summary_parts.append("🔴 賣出訊號")
    else:
        summary_parts.append("⚪ 觀望")
    
    return " ".join(summary_parts)


# ============================================================================
# Testing & Utilities
# ============================================================================

def test_api_key() -> Dict:
    """Test if API key is working"""
    messages = [
        {"role": "user", "content": "你好，請用繁體中文回答。如果 API 正常運作，請回覆「API 測試成功」。"}
    ]
    
    result = call_openrouter(messages, max_tokens=50)
    
    if 'error' in result:
        return {
            'status': 'failed',
            'error': result['error']
        }
    
    response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    return {
        'status': 'success',
        'response': response_text,
        'model_used': result.get('model', 'unknown')
    }


def quick_analysis_summary(analysis: Dict) -> str:
    """Generate quick summary of analysis for display"""
    if 'error' in analysis:
        return f"❌ 錯誤：{analysis['error']}"
    
    signal = analysis.get('signal', {})
    direction = signal.get('direction', 'HOLD')
    confidence = signal.get('confidence', 0)
    
    emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(direction, '⚪')
    
    summary = f"{emoji} 訊號：{direction} (信心度：{confidence:.0%})\n"
    
    if signal.get('entry_price'):
        summary += f"進場價：{signal['entry_price']:.2f}\n"
    if signal.get('stop_loss'):
        summary += f"停損價：{signal['stop_loss']:.2f}\n"
    if signal.get('target_price'):
        summary += f"目標價：{signal['target_price']:.2f}\n"
    if signal.get('risk_reward_ratio'):
        summary += f"風險報酬比：{signal['risk_reward_ratio']:.2f}\n"
    
    return summary


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    print("🧪 測試 OpenRouter API（蔡森增強版）...")
    print()
    
    # Test API key
    test_result = test_api_key()
    print(f"API 測試：{test_result['status'].upper()}")
    if test_result['status'] == 'success':
        print(f"回應：{test_result['response']}")
        print(f"模型：{test_result['model_used']}")
    else:
        print(f"錯誤：{test_result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 60)
    print("蔡森量價型態學分析模組 - 增強版")
    print("=" * 60)
    print()
    print("核心功能：")
    print("  ✅ analyze_chart_image() - 圖表影像分析（含型態辨識）")
    print("  ✅ analyze_ohlc_data() - OHLCV 數據分析（量價關係）")
    print("  ✅ detect_breakout_points() - 突破點/跌破點偵測")
    print("  ✅ detect_spring_pattern() - 破底翻型態偵測")
    print("  ✅ detect_false_breakout_pattern() - 假突破型態偵測")
    print("  ✅ calculate_swing_targets() - 波段漲跌幅測幅")
    print("  ✅ combine_signals() - 算法與 LLM 訊號整合")
    print()
    print("蔡森方法論特色：")
    print("  📊 量在價先 - 成交量為最領先指標")
    print("  📈 型態大於指標 - 不依賴均線，專注 K 線型態")
    print("  🎯 突破點/跌破點 - 最有效率進場點")
    print("  🔄 破底翻/假突破 - 高勝率反轉訊號")
    print("  📐 漲幅滿足/跌幅滿足 - 測幅目標計算")
    print("  📅 6 個月+ 歷史資料 - 完整型態判斷")
    print()
    print("✅ OpenRouter 分析模組（蔡森增強版）載入成功")
