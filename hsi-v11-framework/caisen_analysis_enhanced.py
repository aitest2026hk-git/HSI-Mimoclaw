#!/usr/bin/env python3
"""
蔡森 (Cai Sen) Enhanced Analysis Tool
=====================================

This tool implements 蔡森's actual trading methodology with focus on:
- 量在價先 (Volume precedes price) - Volume is THE key indicator
- 型態大於指標 (Patterns > Indicators) - No MA reliance
- Key patterns: 破底翻，假突破，突破點，波段漲跌幅
- 6+ months historical data display
- Comprehensive volume analysis

Based on research from:
- 《多空轉折一手抓》蔡森's book
- ts888.blogspot.com (蔡森's official blog)
- Multiple interviews and technical analysis resources
"""

import csv
import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union


# ============================================================================
# DATA LOADING
# ============================================================================

def load_data(filepath: str) -> Dict:
    """Load OHLCV data from CSV file"""
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


def get_slice(data: Dict, key: str, start: int = None, end: int = None) -> List:
    """Get slice of data array"""
    arr = data[key]
    if start is None and end is None:
        return arr
    return arr[start:end]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calc_mean(values: List[float]) -> float:
    """Calculate mean"""
    return sum(values) / len(values) if values else 0


def calc_std(values: List[float]) -> float:
    """Calculate standard deviation"""
    if len(values) < 2:
        return 0
    mean = calc_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def find_local_extrema(prices: List[float], valley: bool, order: int = 5) -> List[int]:
    """Find local peaks (valley=False) or valleys (valley=True)"""
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


def pct_change(old: float, new: float) -> float:
    """Calculate percentage change"""
    if old == 0:
        return 0
    return ((new - old) / old) * 100


# ============================================================================
# VOLUME ANALYSIS - THE CORE OF 蔡森 METHODOLOGY
# ============================================================================

def analyze_volume_price_relationship(data: Dict) -> Dict:
    """
    Analyze volume-price relationship - 量在價先 (Volume precedes price)
    This is THE most important analysis in 蔡森's methodology
    """
    closes = data['close']
    volumes = data['volume']
    dates = data['dates']
    
    # Analyze different time windows
    windows = [5, 10, 20, 60]
    volume_analysis = {}
    
    for window in windows:
        if len(closes) < window * 2:
            continue
            
        recent_start = -window
        older_start = -window * 2
        
        price_recent = closes[recent_start] if recent_start < 0 else closes[0]
        price_older = closes[older_start] if older_start < 0 else closes[0]
        price_change = pct_change(price_older, price_recent)
        
        vol_recent = calc_mean(volumes[recent_start:])
        vol_older = calc_mean(volumes[older_start:recent_start])
        vol_change = pct_change(vol_older, vol_recent)
        
        # Determine relationship
        if price_change > 3 and vol_change > 10:
            relationship = "量價齊揚 (Bullish confirmation)"
            signal = "bullish"
        elif price_change > 3 and vol_change < -10:
            relationship = "量價背離 (Bearish divergence - WARNING)"
            signal = "bearish_divergence"
        elif price_change < -3 and vol_change > 10:
            relationship = "量增價跌 (Bearish - heavy selling)"
            signal = "bearish"
        elif price_change < -3 and vol_change < -10:
            relationship = "量縮價跌 (Selling exhaustion watch)"
            signal = "watch_exhaustion"
        else:
            relationship = "量價盤整 (Consolidation)"
            signal = "neutral"
        
        volume_analysis[f'{window}d'] = {
            'price_change': round(price_change, 2),
            'volume_change': round(vol_change, 2),
            'relationship': relationship,
            'signal': signal,
            'avg_volume_recent': int(vol_recent),
            'avg_volume_older': int(vol_older)
        }
    
    # Find unusual volume spikes
    avg_vol = calc_mean(volumes[-60:]) if len(volumes) >= 60 else calc_mean(volumes)
    std_vol = calc_std(volumes[-60:]) if len(volumes) >= 60 else calc_std(volumes)
    
    volume_spikes = []
    for i in range(-30, 0):
        if len(volumes) + i >= 0:
            vol = volumes[i]
            if vol > avg_vol + 2 * std_vol:
                volume_spikes.append({
                    'date': dates[i],
                    'volume': int(vol),
                    'multiple': round(vol / avg_vol, 2),
                    'price_change_next_5d': None  # Will calculate if possible
                })
                
                # Calculate what happened in next 5 days
                if i + 5 < 0:
                    price_before = closes[i]
                    price_after = closes[i + 5]
                    volume_spikes[-1]['price_change_next_5d'] = round(pct_change(price_before, price_after), 2)
    
    # Current volume status
    current_vol = volumes[-1]
    current_vs_avg = round(current_vol / avg_vol, 2) if avg_vol > 0 else 0
    
    if current_vs_avg > 2.0:
        volume_status = "異常大量 (Unusually heavy)"
    elif current_vs_avg > 1.5:
        volume_status = "大量 (Heavy)"
    elif current_vs_avg > 0.8:
        volume_status = "正常 (Normal)"
    elif current_vs_avg > 0.5:
        volume_status = "量縮 (Light)"
    else:
        volume_status = "極量縮 (Very light)"
    
    return {
        'multi_window_analysis': volume_analysis,
        'volume_spikes': volume_spikes[-5:],  # Last 5 spikes
        'current_volume_vs_avg': current_vs_avg,
        'volume_status': volume_status,
        'average_volume_60d': int(avg_vol),
        'interpretation': _interpret_volume_analysis(volume_analysis, current_vs_avg)
    }


def _interpret_volume_analysis(volume_analysis: Dict, current_vs_avg: float) -> str:
    """Generate interpretation based on volume analysis"""
    if '20d' not in volume_analysis:
        return "數據不足 (Insufficient data)"
    
    analysis_20d = volume_analysis['20d']
    signal = analysis_20d['signal']
    
    interpretations = {
        'bullish': "✅ 量價配合良好，多頭格局",
        'bearish_divergence': "⚠️ 量價背離，警訊！價格上漲但成交量不足",
        'bearish': "⚠️ 大量下跌，賣壓沉重",
        'watch_exhaustion': "👀 賣壓可能耗盡，觀察是否止跌",
        'neutral': "➡️ 量價盤整，等待方向"
    }
    
    base_interpretation = interpretations.get(signal, "➡️ 觀望")
    
    if current_vs_avg > 2.0:
        base_interpretation += " - 今日成交量異常放大，留意變盤"
    elif current_vs_avg < 0.5:
        base_interpretation += " - 成交量極度萎縮，可能即將變盤"
    
    return base_interpretation


# ============================================================================
# PATTERN DETECTION - 蔡森 12 PATTERNS
# ============================================================================

def detect_breakout_point(data: Dict) -> Optional[Dict]:
    """
    突破點 (Breakout Point) Detection
    Find where price breaks above resistance with volume confirmation
    """
    closes = data['close']
    highs = data['high']
    lows = data['low']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 90:
        return None
    
    # Find resistance level from past 3-6 months
    window = min(120, len(closes))
    resistance_candidates = []
    
    # Find peaks that could be resistance
    peak_indices = find_local_extrema(highs, valley=False, order=8)
    
    for idx in peak_indices:
        if idx > len(closes) - 30:  # Skip very recent peaks
            continue
        resistance_candidates.append(highs[idx])
    
    if not resistance_candidates:
        return None
    
    # The resistance is the most tested level
    resistance = calc_mean(sorted(resistance_candidates)[-3:]) if len(resistance_candidates) >= 3 else max(resistance_candidates)
    
    # Check for recent breakout
    for i in range(len(closes) - 30, len(closes)):
        if closes[i] > resistance:
            # Check volume confirmation
            breakout_vol = volumes[i]
            avg_vol = calc_mean(volumes[i-20:i]) if i >= 20 else calc_mean(volumes[:i])
            
            volume_confirmed = breakout_vol > avg_vol * 1.5
            
            # Calculate measured move target
            # Find support level (bottom of consolidation)
            consolidation_start = max(0, i - 90)
            consolidation_lows = lows[consolidation_start:i]
            support = min(consolidation_lows)
            
            pattern_height = resistance - support
            target = resistance + pattern_height
            
            # Risk/reward
            entry = resistance
            stop_loss = support * 0.97
            risk = entry - stop_loss
            reward = target - entry
            rr_ratio = reward / risk if risk > 0 else 0
            
            confidence = 0.5
            confidence += 0.2 if volume_confirmed else 0
            confidence += 0.15 if rr_ratio > 2 else 0
            confidence += 0.15 if (closes[i] - resistance) / resistance > 0.03 else 0  # >3% breakout
            
            return {
                'pattern': '突破點 (Breakout Point)',
                'detected_at': dates[i],
                'breakout_price': round(closes[i], 2),
                'resistance_level': round(resistance, 2),
                'support_level': round(support, 2),
                'entry_price': round(entry, 2),
                'stop_loss': round(stop_loss, 2),
                'target_price': round(target, 2),
                'risk_reward_ratio': round(rr_ratio, 2),
                'volume_confirmed': volume_confirmed,
                'volume_multiple': round(breakout_vol / avg_vol, 2),
                'confidence': round(min(confidence, 0.95), 2),
                'notes': f"突破 {resistance:.2f}，成交量{'確認' if volume_confirmed else '不足'}"
            }
    
    return None


def detect_bottom_reversal(data: Dict) -> Optional[Dict]:
    """
    破底翻 (Spring / Bottom Reversal) Detection
    Price breaks below support, then quickly reverses back above
    This is one of 蔡森's highest probability patterns (~75-80% success rate)
    """
    closes = data['close']
    highs = data['high']
    lows = data['low']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 60:
        return None
    
    # Find support level
    window = min(90, len(closes))
    valley_indices = find_local_extrema(lows, valley=True, order=8)
    
    support_candidates = []
    for idx in valley_indices:
        if idx < len(closes) - 15:  # Not too recent
            support_candidates.append(lows[idx])
    
    if not support_candidates:
        return None
    
    support = calc_mean(sorted(support_candidates)[:3]) if len(support_candidates) >= 3 else min(support_candidates)
    
    # Look for break below support followed by quick recovery
    for i in range(len(closes) - 40, len(closes) - 5):
        if lows[i] < support:  # Broke below support
            # Check if it recovered within next 3-5 days
            for j in range(i + 1, min(i + 6, len(closes))):
                if closes[j] > support:  # Recovered back above support
                    # Check volume on reversal day
                    breakdown_vol = volumes[i]
                    reversal_vol = volumes[j]
                    avg_vol = calc_mean(volumes[max(0, i-20):i])
                    
                    # Key: reversal should have heavy volume
                    strong_reversal = reversal_vol > avg_vol * 1.8
                    light_breakdown = breakdown_vol < avg_vol * 1.3
                    
                    # Measure the pattern
                    pattern_low = lows[i]
                    pattern_high = max(highs[max(0, j-10):j+1])
                    pattern_height = pattern_high - pattern_low
                    
                    entry = support
                    stop_loss = pattern_low * 0.97
                    target = pattern_high + pattern_height * 0.5
                    
                    risk = entry - stop_loss
                    reward = target - entry
                    rr_ratio = reward / risk if risk > 0 else 0
                    
                    confidence = 0.55
                    confidence += 0.2 if strong_reversal else 0
                    confidence += 0.1 if light_breakdown else 0
                    confidence += 0.15 if rr_ratio > 2 else 0
                    
                    return {
                        'pattern': '破底翻 (Spring/Bottom Reversal)',
                        'detected_at': dates[j],
                        'spring_low': round(pattern_low, 2),
                        'support_level': round(support, 2),
                        'entry_price': round(entry, 2),
                        'stop_loss': round(stop_loss, 2),
                        'target_price': round(target, 2),
                        'risk_reward_ratio': round(rr_ratio, 2),
                        'volume_confirmation': strong_reversal,
                        'breakdown_volume': int(breakdown_vol),
                        'reversal_volume': int(reversal_vol),
                        'avg_volume': int(avg_vol),
                        'confidence': round(min(confidence, 0.90), 2),
                        'notes': f"破 {support:.2f} 後翻轉，{'強勢' if strong_reversal else '弱勢'}成交量"
                    }
    
    return None


def detect_false_breakout(data: Dict, direction: str = 'up') -> Optional[Dict]:
    """
    假突破 (False Breakout) Detection
    Price breaks out but fails to follow through, then reverses
    蔡森's key pattern for counter-trend trades
    """
    closes = data['close']
    highs = data['high']
    lows = data['low']
    volumes = data['volume']
    dates = data['dates']
    
    if len(closes) < 60:
        return None
    
    if direction == 'up':  # Bull trap (假突破 - bearish)
        # Find resistance level
        recent_highs = highs[-80:-10]
        if not recent_highs:
            return None
        
        sorted_highs = sorted(recent_highs)
        resistance = sorted_highs[int(len(sorted_highs) * 0.9)]
        
        # Look for false breakout
        for i in range(len(closes) - 30, len(closes) - 3):
            if highs[i] > resistance:  # Broke above resistance
                # Check if it failed within next 3-5 days
                max_after = max(highs[i:min(i+5, len(closes))])
                close_after = closes[min(i+3, len(closes)-1)]
                
                if close_after < resistance:  # Fell back below resistance
                    breakout_vol = volumes[i]
                    reversal_vol = volumes[i + 3] if i + 3 < len(volumes) else volumes[-1]
                    avg_vol = calc_mean(volumes[max(0, i-20):i])
                    
                    # Key: breakout on light volume, reversal on heavy volume
                    light_breakout = breakout_vol < avg_vol * 1.2
                    heavy_reversal = reversal_vol > avg_vol * 1.5
                    
                    if light_breakout or heavy_reversal:
                        entry = resistance
                        stop_loss = highs[i] * 1.02
                        recent_low = min(lows[-20:])
                        target = recent_low * 0.97
                        
                        risk = stop_loss - entry
                        reward = entry - target
                        rr_ratio = reward / risk if risk > 0 else 0
                        
                        confidence = 0.50
                        confidence += 0.15 if light_breakout else 0
                        confidence += 0.15 if heavy_reversal else 0
                        confidence += 0.1 if rr_ratio > 2 else 0
                        
                        return {
                            'pattern': '假突破 (False Breakout - Bull Trap)',
                            'type': 'bearish',
                            'detected_at': dates[i + 3] if i + 3 < len(dates) else dates[-1],
                            'false_high': round(highs[i], 2),
                            'resistance_level': round(resistance, 2),
                            'entry_price': round(entry, 2),
                            'stop_loss': round(stop_loss, 2),
                            'target_price': round(target, 2),
                            'risk_reward_ratio': round(rr_ratio, 2),
                            'volume_confirmation': light_breakout and heavy_reversal,
                            'breakout_volume': int(breakout_vol),
                            'reversal_volume': int(reversal_vol),
                            'confidence': round(min(confidence, 0.85), 2),
                            'notes': f"突破 {resistance:.2f} 失敗，{'量輕' if light_breakout else '量重'}突破"
                        }
    
    else:  # Bear trap (bullish)
        recent_lows = lows[-80:-10]
        if not recent_lows:
            return None
        
        sorted_lows = sorted(recent_lows)
        support = sorted_lows[int(len(sorted_lows) * 0.1)]
        
        for i in range(len(closes) - 30, len(closes) - 3):
            if lows[i] < support:
                min_after = min(lows[i:min(i+5, len(lows))])
                close_after = closes[min(i+3, len(closes)-1)]
                
                if close_after > support:
                    breakdown_vol = volumes[i]
                    reversal_vol = volumes[i + 3] if i + 3 < len(volumes) else volumes[-1]
                    avg_vol = calc_mean(volumes[max(0, i-20):i])
                    
                    light_breakdown = breakdown_vol < avg_vol * 1.2
                    heavy_reversal = reversal_vol > avg_vol * 1.5
                    
                    if light_breakdown or heavy_reversal:
                        entry = support
                        stop_loss = lows[i] * 0.98
                        recent_high = max(highs[-20:])
                        target = recent_high * 1.03
                        
                        risk = entry - stop_loss
                        reward = target - entry
                        rr_ratio = reward / risk if risk > 0 else 0
                        
                        confidence = 0.50
                        confidence += 0.15 if light_breakdown else 0
                        confidence += 0.15 if heavy_reversal else 0
                        confidence += 0.1 if rr_ratio > 2 else 0
                        
                        return {
                            'pattern': '假突破 (False Breakout - Bear Trap)',
                            'type': 'bullish',
                            'detected_at': dates[i + 3] if i + 3 < len(dates) else dates[-1],
                            'false_low': round(lows[i], 2),
                            'support_level': round(support, 2),
                            'entry_price': round(entry, 2),
                            'stop_loss': round(stop_loss, 2),
                            'target_price': round(target, 2),
                            'risk_reward_ratio': round(rr_ratio, 2),
                            'volume_confirmation': light_breakdown and heavy_reversal,
                            'confidence': round(min(confidence, 0.85), 2),
                            'notes': f"跌破 {support:.2f} 失敗，陷阱"
                        }
    
    return None


def calculate_swing_range(data: Dict) -> Dict:
    """
    波段漲幅/跌幅 (Swing Gain/Loss) Calculation
    Calculate potential swing ranges based on pattern measurements
    """
    closes = data['close']
    highs = data['high']
    lows = data['low']
    
    current_price = closes[-1]
    
    # Find recent swing high and low
    window = min(120, len(closes))
    swing_high = max(highs[-window:])
    swing_low = min(lows[-window:])
    
    # Calculate where we are in the range
    range_size = swing_high - swing_low
    position_in_range = (current_price - swing_low) / range_size * 100 if range_size > 0 else 50
    
    # Calculate potential moves
    upside_to_high = pct_change(current_price, swing_high)
    downside_to_low = pct_change(current_price, swing_low)
    
    # Measure recent swings
    recent_peaks = find_local_extrema(highs, valley=False, order=10)
    recent_valleys = find_local_extrema(lows, valley=True, order=10)
    
    swing_measurements = []
    
    # Measure recent up swings
    for i in range(len(recent_valleys) - 1):
        valley_idx = recent_valleys[i]
        # Find next peak after this valley
        peaks_after = [p for p in recent_peaks if p > valley_idx]
        if peaks_after:
            peak_idx = peaks_after[0]
            swing_gain = pct_change(lows[valley_idx], highs[peak_idx])
            swing_measurements.append({
                'type': 'up_swing',
                'from': lows[valley_idx],
                'to': highs[peak_idx],
                'gain_pct': round(swing_gain, 2)
            })
    
    # Measure recent down swings
    for i in range(len(recent_peaks) - 1):
        peak_idx = recent_peaks[i]
        valleys_after = [v for v in recent_valleys if v > peak_idx]
        if valleys_after:
            valley_idx = valleys_after[0]
            swing_loss = pct_change(highs[peak_idx], lows[valley_idx])
            swing_measurements.append({
                'type': 'down_swing',
                'from': highs[peak_idx],
                'to': lows[valley_idx],
                'loss_pct': round(swing_loss, 2)
            })
    
    # Calculate average swing sizes
    up_swings = [s['gain_pct'] for s in swing_measurements if s['type'] == 'up_swing']
    down_swings = [abs(s['loss_pct']) for s in swing_measurements if s['type'] == 'down_swing']
    
    avg_up_swing = calc_mean(up_swings) if up_swings else 0
    avg_down_swing = calc_mean(down_swings) if down_swings else 0
    
    return {
        'current_price': round(current_price, 2),
        'swing_high': round(swing_high, 2),
        'swing_low': round(swing_low, 2),
        'range_size': round(range_size, 2),
        'position_in_range_pct': round(position_in_range, 1),
        'upside_to_high_pct': round(upside_to_high, 2),
        'downside_to_low_pct': round(downside_to_low, 2),
        'avg_up_swing_pct': round(avg_up_swing, 2),
        'avg_down_swing_pct': round(avg_down_swing, 2),
        'interpretation': _interpret_swing_position(position_in_range)
    }


def _interpret_swing_position(position_pct: float) -> str:
    """Interpret where price is in the swing range"""
    if position_pct > 80:
        return "接近波段高點，留意是否出現假突破或頭部型態"
    elif position_pct > 60:
        return "波段中上檔，多頭格局，觀察是否持續"
    elif position_pct > 40:
        return "波段中間，盤整格局"
    elif position_pct > 20:
        return "波段中下檔，空頭格局，觀察是否止跌"
    else:
        return "接近波段低點，留意是否出現破底翻或底部型態"


# ============================================================================
# TREND LINE ANALYSIS - 蔡森's Method
# ============================================================================

def draw_trend_lines(data: Dict) -> Dict:
    """
    Draw trend lines using 蔡森's method
    Focus on connecting significant pivot points
    """
    highs = data['high']
    lows = data['low']
    closes = data['close']
    dates = data['dates']
    
    if len(closes) < 60:
        return {'trend_lines': [], 'interpretation': '數據不足'}
    
    trend_lines = []
    
    # Find significant peaks and valleys
    peak_indices = find_local_extrema(highs, valley=False, order=10)
    valley_indices = find_local_extrema(lows, valley=True, order=10)
    
    # Draw resistance line (connecting peaks)
    if len(peak_indices) >= 2:
        # Take last 2-3 significant peaks
        recent_peaks = peak_indices[-3:] if len(peak_indices) >= 3 else peak_indices[-2:]
        
        if len(recent_peaks) >= 2:
            idx1, idx2 = recent_peaks[-2], recent_peaks[-1]
            p1, p2 = highs[idx1], highs[idx2]
            
            # Calculate slope
            slope = (p2 - p1) / (idx2 - idx1)
            
            # Project forward
            current_idx = len(closes) - 1
            projected_resistance = p2 + slope * (current_idx - idx2)
            
            trend_type = "下降" if slope < 0 else "上升" if slope > 0 else "水平"
            
            trend_lines.append({
                'type': 'resistance',
                'trend': trend_type,
                'points': [(dates[idx1], p1), (dates[idx2], p2)],
                'current_level': round(projected_resistance, 2),
                'slope': round(slope, 4),
                'description': f"{trend_type}阻力線，當前位於 {projected_resistance:.2f}"
            })
    
    # Draw support line (connecting valleys)
    if len(valley_indices) >= 2:
        recent_valleys = valley_indices[-3:] if len(valley_indices) >= 3 else valley_indices[-2:]
        
        if len(recent_valleys) >= 2:
            idx1, idx2 = recent_valleys[-2], recent_valleys[-1]
            p1, p2 = lows[idx1], lows[idx2]
            
            slope = (p2 - p1) / (idx2 - idx1)
            current_idx = len(closes) - 1
            projected_support = p2 + slope * (current_idx - idx2)
            
            trend_type = "下降" if slope < 0 else "上升" if slope > 0 else "水平"
            
            trend_lines.append({
                'type': 'support',
                'trend': trend_type,
                'points': [(dates[idx1], p1), (dates[idx2], p2)],
                'current_level': round(projected_support, 2),
                'slope': round(slope, 4),
                'description': f"{trend_type}支撐線，當前位於 {projected_support:.2f}"
            })
    
    # Interpretation
    current_price = closes[-1]
    interpretation = []
    
    for line in trend_lines:
        distance_pct = abs(current_price - line['current_level']) / current_price * 100
        if distance_pct < 3:
            interpretation.append(f"⚠️ 價格接近{line['type']}線 ({line['current_level']:.2f})，留意突破或反彈")
    
    if not interpretation:
        interpretation.append("➡️ 價格位於趨勢線中間，等待方向")
    
    return {
        'trend_lines': trend_lines,
        'current_price': round(current_price, 2),
        'interpretation': ' | '.join(interpretation)
    }


# ============================================================================
# COMPREHENSIVE ANALYSIS
# ============================================================================

def run_comprehensive_analysis(data: Dict) -> Dict:
    """Run complete 蔡森 analysis"""
    print("🔍 執行蔡森綜合分析...")
    
    results = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'data_range': {
            'from': data['dates'][0],
            'to': data['dates'][-1],
            'total_days': len(data['dates'])
        },
        'current_price': float(data['close'][-1]),
        'volume_analysis': analyze_volume_price_relationship(data),
        'swing_analysis': calculate_swing_range(data),
        'trend_lines': draw_trend_lines(data),
        'patterns_detected': []
    }
    
    # Detect patterns
    pattern_detectors = [
        ('突破點', lambda: detect_breakout_point(data)),
        ('破底翻', lambda: detect_bottom_reversal(data)),
        ('假突破 (多頭陷阱)', lambda: detect_false_breakout(data, direction='up')),
        ('假突破 (空頭陷阱)', lambda: detect_false_breakout(data, direction='down')),
    ]
    
    for name, detector in pattern_detectors:
        try:
            result = detector()
            if result:
                results['patterns_detected'].append(result)
                print(f"   ✅ 偵測到: {name}")
        except Exception as e:
            print(f"   ⚠️ {name} 偵測錯誤: {e}")
    
    # Generate overall signal
    results['overall_signal'] = _generate_overall_signal(results)
    
    return results


def _generate_overall_signal(results: Dict) -> Dict:
    """Generate overall trading signal based on all analysis"""
    buy_signals = 0
    sell_signals = 0
    confidence_factors = []
    
    # Volume analysis signal
    vol_analysis = results['volume_analysis']
    if '20d' in vol_analysis.get('multi_window_analysis', {}):
        vol_signal = vol_analysis['multi_window_analysis']['20d']['signal']
        if vol_signal == 'bullish':
            buy_signals += 1
            confidence_factors.append(0.7)
        elif vol_signal == 'bearish':
            sell_signals += 1
            confidence_factors.append(0.7)
    
    # Pattern signals
    for pattern in results['patterns_detected']:
        confidence = pattern.get('confidence', 0.5)
        confidence_factors.append(confidence)
        
        pattern_name = pattern['pattern']
        if '破底翻' in pattern_name or ('假突破' in pattern_name and pattern.get('type') == 'bullish'):
            buy_signals += 1
        elif '假突破' in pattern_name and pattern.get('type') == 'bearish':
            sell_signals += 1
        elif '突破點' in pattern_name:
            buy_signals += 1
    
    # Swing position
    swing = results['swing_analysis']
    position = swing.get('position_in_range_pct', 50)
    if position < 25:
        buy_signals += 0.5
    elif position > 75:
        sell_signals += 0.5
    
    # Determine overall signal
    if buy_signals > sell_signals + 1:
        direction = "BUY"
        base_confidence = 0.6
    elif sell_signals > buy_signals + 1:
        direction = "SELL"
        base_confidence = 0.6
    else:
        direction = "HOLD"
        base_confidence = 0.5
    
    # Adjust confidence
    avg_confidence = calc_mean(confidence_factors) if confidence_factors else 0.5
    final_confidence = (base_confidence + avg_confidence) / 2
    
    return {
        'direction': direction,
        'confidence': round(final_confidence, 2),
        'buy_signals': buy_signals,
        'sell_signals': sell_signals,
        'reasoning': _generate_signal_reasoning(results, direction)
    }


def _generate_signal_reasoning(results: Dict, direction: str) -> str:
    """Generate reasoning for the signal"""
    reasons = []
    
    # Volume reasoning
    vol_status = results['volume_analysis'].get('volume_status', '')
    if vol_status:
        reasons.append(f"成交量: {vol_status}")
    
    # Pattern reasoning
    if results['patterns_detected']:
        pattern_names = [p['pattern'] for p in results['patterns_detected']]
        reasons.append(f"形態: {', '.join(pattern_names)}")
    
    # Swing reasoning
    swing_interp = results['swing_analysis'].get('interpretation', '')
    if swing_interp:
        reasons.append(f"波段: {swing_interp}")
    
    return ' | '.join(reasons) if reasons else "綜合判斷"


# ============================================================================
# CHART GENERATION (6+ months display)
# ============================================================================

def generate_enhanced_chart(data: Dict, analysis: Dict, output_path: str):
    """Generate enhanced HTML chart with 6+ months data and volume"""
    print(f"\n📈 生成圖表 (6個月以上數據)...")
    
    # Use last 180 days (6+ months)
    display_days = min(180, len(data['dates']))
    start_idx = len(data['dates']) - display_days
    
    dates_display = data['dates'][start_idx:]
    closes_display = data['close'][start_idx:]
    highs_display = data['high'][start_idx:]
    lows_display = data['low'][start_idx:]
    volumes_display = data['volume'][start_idx:]
    
    # Calculate volume colors
    volume_colors = []
    for i in range(len(dates_display)):
        actual_idx = start_idx + i
        if actual_idx > 0:
            if data['close'][actual_idx] >= data['close'][actual_idx - 1]:
                volume_colors.append('rgba(0, 212, 255, 0.5)')  # Blue for up
            else:
                volume_colors.append('rgba(255, 82, 82, 0.5)')  # Red for down
        else:
            volume_colors.append('rgba(200, 200, 200, 0.5)')
    
    # Add pattern markers
    pattern_annotations = []
    for pattern in analysis.get('patterns_detected', []):
        # Try to find the date in our display range
        pattern_date = pattern.get('detected_at', '')
        if pattern_date in dates_display:
            idx = dates_display.index(pattern_date)
            pattern_annotations.append({
                'x': idx,
                'y': lows_display[idx] * 0.98,
                'text': pattern['pattern'].split('(')[0],
                'type': 'buy' if '破底翻' in pattern['pattern'] or '突破點' in pattern['pattern'] else 'sell'
            })
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>蔡森分析 - 0700.HK</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation"></script>
    <style>
        body {{ 
            font-family: 'Microsoft YaHei', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ 
            color: #00d4ff; 
            text-align: center;
            margin-bottom: 10px;
            font-size: 2em;
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 30px;
        }}
        .chart-container {{ 
            position: relative; 
            height: 500px; 
            margin: 20px 0;
            background: rgba(22, 33, 62, 0.5);
            border-radius: 10px;
            padding: 20px;
        }}
        .volume-container {{
            position: relative;
            height: 150px;
            margin: 10px 0 20px 0;
            background: rgba(22, 33, 62, 0.5);
            border-radius: 10px;
            padding: 10px;
        }}
        .info-panel {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-box {{
            background: rgba(22, 33, 62, 0.8);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #00d4ff;
        }}
        .info-box h3 {{
            color: #00d4ff;
            margin-top: 0;
            font-size: 1.1em;
        }}
        .info-box ul {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .info-box li {{
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .info-box li:last-child {{
            border-bottom: none;
        }}
        .signal-box {{
            background: rgba(22, 33, 62, 0.8);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .signal-direction {{
            font-size: 2em;
            font-weight: bold;
            padding: 10px 30px;
            border-radius: 5px;
            display: inline-block;
        }}
        .signal-buy {{
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
            border: 2px solid #00d4ff;
        }}
        .signal-sell {{
            background: rgba(255, 82, 82, 0.2);
            color: #ff5252;
            border: 2px solid #ff5252;
        }}
        .signal-hold {{
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 2px solid #ffc107;
        }}
        .confidence {{
            margin-top: 10px;
            color: #888;
        }}
        .pattern-tag {{
            display: inline-block;
            padding: 5px 10px;
            margin: 5px;
            border-radius: 15px;
            font-size: 0.9em;
            background: rgba(0, 212, 255, 0.2);
            color: #00d4ff;
        }}
        .pattern-tag.sell {{
            background: rgba(255, 82, 82, 0.2);
            color: #ff5252;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 騰訊控股 (0700.HK) - 蔡森技術分析</h1>
        <p class="subtitle">數據區間: {dates_display[0]} 至 {dates_display[-1]} ({display_days}交易日)</p>
        
        <div class="signal-box">
            <div class="signal-direction signal-{analysis['overall_signal']['direction'].lower()}">
                {analysis['overall_signal']['direction']}
            </div>
            <div class="confidence">
                信心度: {analysis['overall_signal']['confidence']*100:.0f}%
            </div>
            <div style="margin-top: 15px; color: #aaa;">
                {analysis['overall_signal']['reasoning']}
            </div>
        </div>
        
        <div class="info-panel">
            <div class="info-box">
                <h3>📊 量價分析</h3>
                <ul>
                    <li>當前價格: <strong style="color: #00d4ff;">HKD {analysis['current_price']:.2f}</strong></li>
                    <li>成交量狀態: {analysis['volume_analysis'].get('volume_status', 'N/A')}</li>
                    <li>量價關係 (20日): {analysis['volume_analysis']['multi_window_analysis'].get('20d', {}).get('relationship', 'N/A')}</li>
                    <li>平均成交量: {analysis['volume_analysis'].get('average_volume_60d', 0):,}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>📈 波段分析</h3>
                <ul>
                    <li>波段高點: HKD {analysis['swing_analysis'].get('swing_high', 0):.2f}</li>
                    <li>波段低點: HKD {analysis['swing_analysis'].get('swing_low', 0):.2f}</li>
                    <li>當前位置: {analysis['swing_analysis'].get('position_in_range_pct', 0):.1f}%</li>
                    <li>解讀: {analysis['swing_analysis'].get('interpretation', 'N/A')}</li>
                </ul>
            </div>
            
            <div class="info-box">
                <h3>📐 趨勢線</h3>
                <ul>
                    {''.join([f"<li>{line['description']}</li>" for line in analysis['trend_lines'].get('trend_lines', [])]) or '<li>無明顯趨勢線</li>'}
                </ul>
                <div style="margin-top: 10px; color: #aaa; font-size: 0.9em;">
                    {analysis['trend_lines'].get('interpretation', '')}
                </div>
            </div>
            
            <div class="info-box">
                <h3>🎯 偵測形態</h3>
                {''.join([f'<span class="pattern-tag{" sell" if "假突破" in p["pattern"] and p.get("type") == "bearish" else ""}">{p["pattern"].split("(")[0]}</span>' for p in analysis['patterns_detected']]) or '<span style="color: #888;">無明顯形態</span>'}
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>
        
        <div class="volume-container">
            <canvas id="volumeChart"></canvas>
        </div>
    </div>
    
    <script>
        // Price data
        const priceCtx = document.getElementById('priceChart').getContext('2d');
        const priceData = {json.dumps(closes_display)};
        const highData = {json.dumps(highs_display)};
        const lowData = {json.dumps(lows_display)};
        const labels = {json.dumps(dates_display)};
        
        // Create gradient
        const gradient = priceCtx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(0, 212, 255, 0.3)');
        gradient.addColorStop(1, 'rgba(0, 212, 255, 0.0)');
        
        new Chart(priceCtx, {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [{{
                    label: '收盤價 (HKD)',
                    data: priceData,
                    borderColor: '#00d4ff',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHoverRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        labels: {{ color: '#00d4ff' }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(22, 33, 62, 0.9)',
                        titleColor: '#00d4ff',
                        bodyColor: '#eee',
                        borderColor: '#00d4ff',
                        borderWidth: 1,
                        callbacks: {{
                            label: function(context) {{
                                return 'HKD ' + context.parsed.y.toFixed(2);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        ticks: {{ 
                            color: '#888',
                            maxTicksLimit: 10,
                            maxRotation: 45
                        }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }},
                    y: {{
                        ticks: {{ color: '#888' }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
                    }}
                }}
            }}
        }});
        
        // Volume data
        const volumeCtx = document.getElementById('volumeChart').getContext('2d');
        const volumeData = {json.dumps(volumes_display)};
        const volumeColors = {json.dumps(volume_colors)};
        
        new Chart(volumeCtx, {{
            type: 'bar',
            data: {{
                labels: labels,
                datasets: [{{
                    label: '成交量',
                    data: volumeData,
                    backgroundColor: volumeColors,
                    borderColor: 'transparent',
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(22, 33, 62, 0.9)',
                        titleColor: '#00d4ff',
                        bodyColor: '#eee',
                        callbacks: {{
                            label: function(context) {{
                                return context.parsed.y.toLocaleString();
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        display: false,
                        grid: {{ display: false }}
                    }},
                    y: {{
                        ticks: {{ 
                            color: '#888',
                            callback: function(value) {{
                                return (value / 1000000).toFixed(1) + 'M';
                            }}
                        }},
                        grid: {{ color: 'rgba(255,255,255,0.05)' }}
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
    
    print(f"   ✅ 圖表已保存至: {output_path}")
    return output_path


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""
    print("=" * 70)
    print("🎯 蔡森 (Cai Sen) 增強分析工具")
    print("   量在價先 | 型態大於指標 | 隨勢而為")
    print("=" * 70)
    print()
    
    # Load data
    data_path = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    print(f"📂 載入數據: {data_path}")
    
    try:
        data = load_data(data_path)
        print(f"   ✅ 載入 {len(data['close'])} 交易日數據")
        print(f"   📅 數據區間: {data['dates'][0]} 至 {data['dates'][-1]}")
    except Exception as e:
        print(f"   ❌ 載入失敗: {e}")
        return
    
    # Check if we have enough data (6+ months)
    trading_days_6m = 6 * 21  # ~126 trading days
    if len(data['close']) < trading_days_6m:
        print(f"   ⚠️ 警告: 數據不足 6 個月 (僅 {len(data['close'])} 天)")
    else:
        print(f"   ✅ 數據充足 ({len(data['close'])} 天，約 {len(data['close'])//21} 個月)")
    
    print()
    
    # Run comprehensive analysis
    analysis = run_comprehensive_analysis(data)
    
    # Save analysis results
    output_json = '/root/.openclaw/workspace/caisen_data/caisen_enhanced_analysis.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"\n💾 分析結果已保存: {output_json}")
    
    # Generate enhanced chart
    chart_path = '/root/.openclaw/workspace/caisen_data/caisen_enhanced_chart.html'
    generate_enhanced_chart(data, analysis, chart_path)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 分析摘要")
    print("=" * 70)
    
    print(f"\n💰 當前價格: HKD {analysis['current_price']:.2f}")
    
    print(f"\n📈 總體信號: {analysis['overall_signal']['direction']}")
    print(f"   信心度: {analysis['overall_signal']['confidence']*100:.0f}%")
    print(f"   理由: {analysis['overall_signal']['reasoning']}")
    
    print(f"\n📊 量價分析:")
    vol = analysis['volume_analysis']
    print(f"   成交量狀態: {vol.get('volume_status', 'N/A')}")
    if '20d' in vol.get('multi_window_analysis', {}):
        print(f"   20 日量價關係: {vol['multi_window_analysis']['20d']['relationship']}")
    print(f"   解讀: {vol.get('interpretation', 'N/A')}")
    
    print(f"\n📐 波段分析:")
    swing = analysis['swing_analysis']
    print(f"   波段區間: HKD {swing.get('swing_low', 0):.2f} - HKD {swing.get('swing_high', 0):.2f}")
    print(f"   當前位置: {swing.get('position_in_range_pct', 0):.1f}%")
    print(f"   解讀: {swing.get('interpretation', 'N/A')}")
    
    if analysis['patterns_detected']:
        print(f"\n🎯 偵測到的形態 ({len(analysis['patterns_detected'])} 個):")
        for i, pattern in enumerate(analysis['patterns_detected'], 1):
            print(f"\n   [{i}] {pattern['pattern']}")
            print(f"       偵測日期: {pattern.get('detected_at', 'N/A')}")
            print(f"       信心度: {pattern.get('confidence', 0)*100:.0f}%")
            if 'entry_price' in pattern:
                print(f"       進場價: HKD {pattern['entry_price']:.2f}")
                print(f"       目標價: HKD {pattern['target_price']:.2f}")
                print(f"       停損價: HKD {pattern['stop_loss']:.2f}")
                print(f"       風險回報比: {pattern.get('risk_reward_ratio', 0):.2f}")
            print(f"       備註: {pattern.get('notes', '')}")
    
    print(f"\n📐 趨勢線分析:")
    print(f"   {analysis['trend_lines'].get('interpretation', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("✅ 分析完成!")
    print("=" * 70)
    
    return analysis


if __name__ == '__main__':
    main()
