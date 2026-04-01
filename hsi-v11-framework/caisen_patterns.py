#!/usr/bin/env python3
"""
蔡森 (Cai Sen) Pattern Detection Module - Standard Library Version

No external dependencies (pandas/numpy/scipy) required.
"""

import csv
from datetime import datetime
from typing import Dict, List, Optional, Union
import math


def load_data(filepath: str) -> Dict:
    """Load OHLCV data from CSV file into dict of lists"""
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


def get_slice(data: Union[Dict, str], key: str, start: int = None, end: int = None) -> List:
    """Get slice of data array"""
    if isinstance(data, str):
        data = load_data(data)
    
    arr = data[key]
    if start is None and end is None:
        return arr
    return arr[start:end]


def find_local_extrema(prices: List[float], valley: bool, order: int = 5) -> List[int]:
    """Find local peaks (valley=False) or valleys (valley=True)"""
    indices = []
    for i in range(order, len(prices) - order):
        if valley:
            # Check if this is a local minimum
            is_extremum = all(prices[i] <= prices[i-j] for j in range(1, order+1))
            is_extremum = is_extremum and all(prices[i] <= prices[i+j] for j in range(1, order+1))
        else:
            # Check if this is a local maximum
            is_extremum = all(prices[i] >= prices[i-j] for j in range(1, order+1))
            is_extremum = is_extremum and all(prices[i] >= prices[i+j] for j in range(1, order+1))
        
        if is_extremum:
            indices.append(i)
    
    return indices


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


def detect_w_bottom(data: Union[Dict, str], sensitivity: float = 0.75) -> Optional[Dict]:
    """Detect W-bottom pattern (雙重底)"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 60:
        return None
    
    lows = d['low']
    highs = d['high']
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    # Find valleys
    valley_indices = find_local_extrema(lows, valley=True, order=10)
    
    if len(valley_indices) < 2:
        return None
    
    for i in range(len(valley_indices) - 1):
        idx1 = valley_indices[i]
        idx2 = valley_indices[i + 1]
        
        if idx2 - idx1 < 10:
            continue
        
        low1 = lows[idx1]
        low2 = lows[idx2]
        
        # Check if lows are within 15% of each other
        diff_pct = abs(low1 - low2) / min(low1, low2)
        if diff_pct > (1 - sensitivity) * 0.15:
            continue
        
        # Find peak between valleys
        peak_idx = idx1 + max(range(idx1, idx2+1), key=lambda x: highs[x])
        neckline = highs[peak_idx]
        
        second_bottom_higher = low2 > low1
        vol1 = volumes[idx1]
        vol2 = volumes[idx2]
        volume_confirmed = vol2 < vol1 * 1.2
        
        # Check for breakout
        breakout = False
        breakout_idx = None
        for j in range(idx2, len(closes)):
            if closes[j] > neckline:
                breakout = True
                breakout_idx = j
                break
        
        if not breakout or breakout_idx is None:
            continue
        
        entry_price = neckline
        stop_loss = min(low1, low2) * 0.97
        pattern_height = neckline - min(low1, low2)
        target_price = neckline + pattern_height
        
        risk = entry_price - stop_loss
        reward = target_price - entry_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.5
        confidence += 0.15 if second_bottom_higher else 0
        confidence += 0.15 if volume_confirmed else 0
        confidence += 0.20 if breakout else 0
        confidence = min(confidence, 0.95)
        
        return {
            'pattern': 'W-bottom',
            'detected_at': dates[breakout_idx],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 45,
            'volume_confirmation': volume_confirmed,
            'notes': f"Second bottom {'higher' if second_bottom_higher else 'lower'}, volume {'confirmed' if volume_confirmed else 'not confirmed'}"
        }
    
    return None


def detect_m_top(data: Union[Dict, str], sensitivity: float = 0.75) -> Optional[Dict]:
    """Detect M-top pattern (雙重頂)"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 60:
        return None
    
    lows = d['low']
    highs = d['high']
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    peak_indices = find_local_extrema(highs, valley=False, order=10)
    
    if len(peak_indices) < 2:
        return None
    
    for i in range(len(peak_indices) - 1):
        idx1 = peak_indices[i]
        idx2 = peak_indices[i + 1]
        
        if idx2 - idx1 < 10:
            continue
        
        high1 = highs[idx1]
        high2 = highs[idx2]
        
        diff_pct = abs(high1 - high2) / max(high1, high2)
        if diff_pct > (1 - sensitivity) * 0.15:
            continue
        
        # Find trough between peaks
        trough_idx = idx1 + min(range(idx1, idx2+1), key=lambda x: lows[x])
        neckline = lows[trough_idx]
        
        second_peak_lower = high2 < high1
        vol1 = volumes[idx1]
        vol2 = volumes[idx2]
        volume_divergence = vol2 < vol1 * 0.8
        
        # Check for breakdown
        breakdown = False
        breakdown_idx = None
        for j in range(idx2, len(closes)):
            if closes[j] < neckline:
                breakdown = True
                breakdown_idx = j
                break
        
        if not breakdown or breakdown_idx is None:
            continue
        
        entry_price = neckline
        stop_loss = max(high1, high2) * 1.03
        pattern_height = max(high1, high2) - neckline
        target_price = neckline - pattern_height
        
        risk = stop_loss - entry_price
        reward = entry_price - target_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.5
        confidence += 0.15 if second_peak_lower else 0
        confidence += 0.20 if volume_divergence else 0
        confidence += 0.15 if breakdown else 0
        confidence = min(confidence, 0.95)
        
        return {
            'pattern': 'M-top',
            'detected_at': dates[breakdown_idx],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 45,
            'volume_confirmation': volume_divergence,
            'notes': f"Second peak {'lower' if second_peak_lower else 'higher'}, volume divergence {'present' if volume_divergence else 'absent'}"
        }
    
    return None


def detect_head_shoulders(data: Union[Dict, str], type: str = 'top') -> Optional[Dict]:
    """Detect Head & Shoulders pattern"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 80:
        return None
    
    lows = d['low']
    highs = d['high']
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    if type == 'top':
        peak_indices = find_local_extrema(highs, valley=False, order=10)
        
        if len(peak_indices) < 3:
            return None
        
        for i in range(len(peak_indices) - 2):
            idx1, idx2, idx3 = peak_indices[i], peak_indices[i+1], peak_indices[i+2]
            
            if idx2 - idx1 < 15 or idx3 - idx2 < 15:
                continue
            
            high1, high2, high3 = highs[idx1], highs[idx2], highs[idx3]
            
            if not (high2 > high1 and high2 > high3):
                continue
            
            shoulder_diff = abs(high1 - high3) / max(high1, high3)
            if shoulder_diff > 0.10:
                continue
            
            # Find neckline
            trough1_idx = idx1 + min(range(idx1, idx2+1), key=lambda x: lows[x])
            trough2_idx = idx2 + min(range(idx2, idx3+1), key=lambda x: lows[x])
            neckline = min(lows[trough1_idx], lows[trough2_idx])
            
            vol1, vol2, vol3 = volumes[idx1], volumes[idx2], volumes[idx3]
            volume_declining = vol3 < vol2 < vol1
            
            # Check breakdown
            breakdown = False
            breakdown_idx = None
            for j in range(idx3, len(closes)):
                if closes[j] < neckline:
                    breakdown = True
                    breakdown_idx = j
                    break
            
            if not breakdown or breakdown_idx is None:
                continue
            
            entry_price = neckline
            stop_loss = high2 * 1.03
            pattern_height = high2 - neckline
            target_price = neckline - pattern_height
            
            risk = stop_loss - entry_price
            reward = entry_price - target_price
            risk_reward = reward / risk if risk > 0 else 0
            
            confidence = 0.55
            confidence += 0.15 if volume_declining else 0
            confidence += 0.15 if breakdown else 0
            confidence = min(confidence, 0.90)
            
            return {
                'pattern': 'Head & Shoulders Top',
                'detected_at': dates[breakdown_idx],
                'confidence': round(confidence, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target_price': round(target_price, 2),
                'risk_reward_ratio': round(risk_reward, 2),
                'time_horizon_days': 60,
                'volume_confirmation': volume_declining,
                'notes': f"Volume {'declining' if volume_declining else 'not declining'} from left to right"
            }
    
    else:  # Bottom
        valley_indices = find_local_extrema(lows, valley=True, order=10)
        
        if len(valley_indices) < 3:
            return None
        
        for i in range(len(valley_indices) - 2):
            idx1, idx2, idx3 = valley_indices[i], valley_indices[i+1], valley_indices[i+2]
            
            if idx2 - idx1 < 15 or idx3 - idx2 < 15:
                continue
            
            low1, low2, low3 = lows[idx1], lows[idx2], lows[idx3]
            
            if not (low2 < low1 and low2 < low3):
                continue
            
            shoulder_diff = abs(low1 - low3) / min(low1, low3)
            if shoulder_diff > 0.10:
                continue
            
            # Find neckline
            peak1_idx = idx1 + max(range(idx1, idx2+1), key=lambda x: highs[x])
            peak2_idx = idx2 + max(range(idx2, idx3+1), key=lambda x: highs[x])
            neckline = max(highs[peak1_idx], highs[peak2_idx])
            
            vol1, vol2, vol3 = volumes[idx1], volumes[idx2], volumes[idx3]
            volume_declining = vol3 < vol1
            
            # Check breakout
            breakout = False
            breakout_idx = None
            for j in range(idx3, len(closes)):
                if closes[j] > neckline:
                    breakout = True
                    breakout_idx = j
                    break
            
            if not breakout or breakout_idx is None:
                continue
            
            breakout_vol = volumes[breakout_idx] if breakout_idx < len(volumes) else 0
            avg_vol = calc_mean(volumes[-20:])
            volume_confirmed = breakout_vol > avg_vol * 1.5
            
            entry_price = neckline
            stop_loss = low2 * 0.97
            pattern_height = neckline - low2
            target_price = neckline + pattern_height
            
            risk = entry_price - stop_loss
            reward = target_price - entry_price
            risk_reward = reward / risk if risk > 0 else 0
            
            confidence = 0.55
            confidence += 0.15 if volume_declining else 0
            confidence += 0.20 if volume_confirmed else 0
            confidence = min(confidence, 0.90)
            
            return {
                'pattern': 'Head & Shoulders Bottom',
                'detected_at': dates[breakout_idx],
                'confidence': round(confidence, 2),
                'entry_price': round(entry_price, 2),
                'stop_loss': round(stop_loss, 2),
                'target_price': round(target_price, 2),
                'risk_reward_ratio': round(risk_reward, 2),
                'time_horizon_days': 60,
                'volume_confirmation': volume_confirmed,
                'notes': f"Volume {'confirmed' if volume_confirmed else 'not confirmed'} on breakout"
            }
    
    return None


def detect_false_breakout(data: Union[Dict, str], direction: str = 'up') -> Optional[Dict]:
    """Detect False Breakout pattern"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 40:
        return None
    
    lows = d['low']
    highs = d['high']
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    if direction == 'up':  # Bull trap
        recent_highs = highs[-60:-10] if len(highs) > 70 else highs[:-10]
        sorted_highs = sorted(recent_highs)
        resistance = sorted_highs[int(len(sorted_highs) * 0.9)] if sorted_highs else 0
        
        for i in range(len(highs) - 10, len(highs)):
            if highs[i] > resistance:
                if i + 3 < len(closes):
                    if closes[i + 3] < resistance:
                        breakout_vol = volumes[i]
                        reversal_vol = volumes[i + 3]
                        avg_vol = calc_mean(volumes[-30:])
                        
                        light_breakout = breakout_vol < avg_vol * 1.2
                        heavy_reversal = reversal_vol > avg_vol * 1.5
                        
                        entry_price = resistance
                        stop_loss = highs[i] * 1.02
                        recent_low = min(lows[-20:])
                        target_price = recent_low * 0.97
                        
                        risk = stop_loss - entry_price
                        reward = entry_price - target_price
                        risk_reward = reward / risk if risk > 0 else 0
                        
                        confidence = 0.50
                        confidence += 0.15 if light_breakout else 0
                        confidence += 0.15 if heavy_reversal else 0
                        confidence = min(confidence, 0.85)
                        
                        return {
                            'pattern': 'False Breakout (Bull Trap)',
                            'detected_at': dates[i + 3],
                            'confidence': round(confidence, 2),
                            'entry_price': round(entry_price, 2),
                            'stop_loss': round(stop_loss, 2),
                            'target_price': round(target_price, 2),
                            'risk_reward_ratio': round(risk_reward, 2),
                            'time_horizon_days': 30,
                            'volume_confirmation': light_breakout and heavy_reversal,
                            'notes': f"Breakout on {'light' if light_breakout else 'heavy'} volume"
                        }
    
    else:  # Bear trap
        recent_lows = lows[-60:-10] if len(lows) > 70 else lows[:-10]
        sorted_lows = sorted(recent_lows)
        support = sorted_lows[int(len(sorted_lows) * 0.1)] if sorted_lows else float('inf')
        
        for i in range(len(lows) - 10, len(lows)):
            if lows[i] < support:
                if i + 3 < len(closes):
                    if closes[i + 3] > support:
                        breakdown_vol = volumes[i]
                        reversal_vol = volumes[i + 3]
                        avg_vol = calc_mean(volumes[-30:])
                        
                        light_breakdown = breakdown_vol < avg_vol * 1.2
                        heavy_reversal = reversal_vol > avg_vol * 1.5
                        
                        entry_price = support
                        stop_loss = lows[i] * 0.98
                        recent_high = max(highs[-20:])
                        target_price = recent_high * 1.03
                        
                        risk = entry_price - stop_loss
                        reward = target_price - entry_price
                        risk_reward = reward / risk if risk > 0 else 0
                        
                        confidence = 0.50
                        confidence += 0.15 if light_breakdown else 0
                        confidence += 0.15 if heavy_reversal else 0
                        confidence = min(confidence, 0.85)
                        
                        return {
                            'pattern': 'False Breakout (Bear Trap/Spring)',
                            'detected_at': dates[i + 3],
                            'confidence': round(confidence, 2),
                            'entry_price': round(entry_price, 2),
                            'stop_loss': round(stop_loss, 2),
                            'target_price': round(target_price, 2),
                            'risk_reward_ratio': round(risk_reward, 2),
                            'time_horizon_days': 30,
                            'volume_confirmation': light_breakdown and heavy_reversal,
                            'notes': f"Breakdown on {'light' if light_breakdown else 'heavy'} volume"
                        }
    
    return None


def detect_triangle(data: Union[Dict, str], type: str = 'ascending') -> Optional[Dict]:
    """Detect Triangle pattern"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 60:
        return None
    
    window = 60
    highs = d['high'][-window:]
    lows = d['low'][-window:]
    closes = d['close'][-window:]
    volumes = d['volume'][-window:]
    dates = d['dates'][-window:]
    
    if type == 'ascending':
        sorted_highs = sorted(highs)
        resistance = sorted_highs[int(len(sorted_highs) * 0.95)]
        
        top_5_pct = sorted_highs[int(len(sorted_highs) * 0.95)]
        top_25_pct = sorted_highs[int(len(sorted_highs) * 0.75)]
        flat_top = (top_5_pct - top_25_pct) / top_25_pct < 0.03 if top_25_pct > 0 else False
        
        if not flat_top:
            return None
        
        first_half_lows = lows[:window//2]
        second_half_lows = lows[window//2:]
        rising_support = calc_mean(second_half_lows) > calc_mean(first_half_lows) * 1.02
        
        if not rising_support:
            return None
        
        breakout = closes[-1] > resistance
        breakout_vol = volumes[-1]
        avg_vol = calc_mean(volumes[:-5])
        volume_confirmed = breakout_vol > avg_vol * 1.5
        
        if not breakout:
            return None
        
        pattern_height = resistance - min(lows)
        
        entry_price = resistance
        stop_loss = max(lows[-10:]) * 0.97
        target_price = resistance + pattern_height
        
        risk = entry_price - stop_loss
        reward = target_price - entry_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.55
        confidence += 0.15 if rising_support else 0
        confidence += 0.15 if volume_confirmed else 0
        confidence = min(confidence, 0.85)
        
        return {
            'pattern': 'Ascending Triangle',
            'detected_at': dates[-1],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 45,
            'volume_confirmation': volume_confirmed,
            'notes': f"Flat resistance at {resistance:.2f}"
        }
    
    else:  # Descending
        sorted_lows = sorted(lows)
        support = sorted_lows[int(len(sorted_lows) * 0.05)]
        
        bottom_5_pct = sorted_lows[int(len(sorted_lows) * 0.05)]
        bottom_25_pct = sorted_lows[int(len(sorted_lows) * 0.25)]
        flat_bottom = (bottom_25_pct - bottom_5_pct) / bottom_5_pct < 0.03 if bottom_5_pct > 0 else False
        
        if not flat_bottom:
            return None
        
        first_half_highs = highs[:window//2]
        second_half_highs = highs[window//2:]
        declining_resistance = calc_mean(second_half_highs) < calc_mean(first_half_highs) * 0.98
        
        if not declining_resistance:
            return None
        
        breakdown = closes[-1] < support
        breakdown_vol = volumes[-1]
        avg_vol = calc_mean(volumes[:-5])
        volume_confirmed = breakdown_vol > avg_vol * 1.3
        
        if not breakdown:
            return None
        
        pattern_height = max(highs) - support
        
        entry_price = support
        stop_loss = min(highs[-10:]) * 1.03
        target_price = support - pattern_height
        
        risk = stop_loss - entry_price
        reward = entry_price - target_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.55
        confidence += 0.15 if declining_resistance else 0
        confidence += 0.15 if volume_confirmed else 0
        confidence = min(confidence, 0.85)
        
        return {
            'pattern': 'Descending Triangle',
            'detected_at': dates[-1],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 45,
            'volume_confirmation': volume_confirmed,
            'notes': f"Flat support at {support:.2f}"
        }
    
    return None


def detect_flag(data: Union[Dict, str], type: str = 'bull') -> Optional[Dict]:
    """Detect Flag pattern"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    if len(d['close']) < 40:
        return None
    
    lows = d['low']
    highs = d['high']
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    if type == 'bull':
        flagpole_start = None
        flagpole_end = None
        
        for i in range(len(closes) - 15, len(closes) - 5):
            for j in range(i + 5, min(i + 10, len(closes))):
                gain = (closes[j] - closes[i]) / closes[i]
                if gain >= 0.12:
                    flagpole_start = i
                    flagpole_end = j
                    break
            if flagpole_end:
                break
        
        if not flagpole_end:
            return None
        
        flagpole_vol = calc_mean(volumes[flagpole_start:flagpole_end+1])
        prior_vol = calc_mean(volumes[max(0, flagpole_start-10):flagpole_start]) if flagpole_start >= 10 else calc_mean(volumes[:flagpole_start])
        heavy_flagpole = flagpole_vol > prior_vol * 1.5
        
        if not heavy_flagpole:
            return None
        
        flag_start = flagpole_end + 1
        flag_end = len(closes) - 1
        
        if flag_end - flag_start < 5:
            return None
        
        flag_closes = closes[flag_start:flag_end+1]
        flag_volumes = volumes[flag_start:flag_end+1]
        
        flag_drift = (flag_closes[-1] - flag_closes[0]) / flag_closes[0] if flag_closes[0] > 0 else 0
        downward_drift = flag_drift < -0.02
        
        avg_flag_vol = calc_mean(flag_volumes)
        light_flag = avg_flag_vol < flagpole_vol * 0.7
        
        if not downward_drift or not light_flag:
            return None
        
        flag_high = max(highs[flag_start:flag_end+1])
        breakout = closes[-1] > flag_high
        breakout_vol = volumes[-1]
        volume_confirmed = breakout_vol > avg_flag_vol * 2.0
        
        if not breakout:
            return None
        
        flagpole_height = closes[flagpole_end] - closes[flagpole_start]
        
        entry_price = flag_high
        stop_loss = min(lows[flag_start:flag_end+1]) * 0.97
        target_price = closes[-1] + flagpole_height
        
        risk = entry_price - stop_loss
        reward = target_price - entry_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.55
        confidence += 0.15 if heavy_flagpole else 0
        confidence += 0.15 if light_flag else 0
        confidence += 0.10 if volume_confirmed else 0
        confidence = min(confidence, 0.90)
        
        return {
            'pattern': 'Bullish Flag',
            'detected_at': dates[-1],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 30,
            'volume_confirmation': volume_confirmed,
            'notes': f"Flagpole {flagpole_height:.2f} points"
        }
    
    else:  # Bear flag
        flagpole_start = None
        flagpole_end = None
        
        for i in range(len(closes) - 15, len(closes) - 5):
            for j in range(i + 5, min(i + 10, len(closes))):
                decline = (closes[i] - closes[j]) / closes[i]
                if decline >= 0.12:
                    flagpole_start = i
                    flagpole_end = j
                    break
            if flagpole_end:
                break
        
        if not flagpole_end:
            return None
        
        flagpole_vol = calc_mean(volumes[flagpole_start:flagpole_end+1])
        prior_vol = calc_mean(volumes[max(0, flagpole_start-10):flagpole_start]) if flagpole_start >= 10 else calc_mean(volumes[:flagpole_start])
        heavy_flagpole = flagpole_vol > prior_vol * 1.5
        
        if not heavy_flagpole:
            return None
        
        flag_start = flagpole_end + 1
        flag_end = len(closes) - 1
        
        if flag_end - flag_start < 5:
            return None
        
        flag_closes = closes[flag_start:flag_end+1]
        flag_volumes = volumes[flag_start:flag_end+1]
        
        flag_drift = (flag_closes[-1] - flag_closes[0]) / flag_closes[0] if flag_closes[0] > 0 else 0
        upward_drift = flag_drift > 0.02
        
        avg_flag_vol = calc_mean(flag_volumes)
        light_flag = avg_flag_vol < flagpole_vol * 0.7
        
        if not upward_drift or not light_flag:
            return None
        
        flag_low = min(lows[flag_start:flag_end+1])
        breakdown = closes[-1] < flag_low
        breakdown_vol = volumes[-1]
        volume_confirmed = breakdown_vol > avg_flag_vol * 1.5
        
        if not breakdown:
            return None
        
        flagpole_height = closes[flagpole_start] - closes[flagpole_end]
        
        entry_price = flag_low
        stop_loss = max(highs[flag_start:flag_end+1]) * 1.03
        target_price = closes[-1] - flagpole_height
        
        risk = stop_loss - entry_price
        reward = entry_price - target_price
        risk_reward = reward / risk if risk > 0 else 0
        
        confidence = 0.55
        confidence += 0.15 if heavy_flagpole else 0
        confidence += 0.15 if light_flag else 0
        confidence += 0.10 if volume_confirmed else 0
        confidence = min(confidence, 0.90)
        
        return {
            'pattern': 'Bearish Flag',
            'detected_at': dates[-1],
            'confidence': round(confidence, 2),
            'entry_price': round(entry_price, 2),
            'stop_loss': round(stop_loss, 2),
            'target_price': round(target_price, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'time_horizon_days': 30,
            'volume_confirmation': volume_confirmed,
            'notes': f"Flagpole {flagpole_height:.2f} points"
        }
    
    return None


def analyze_volume_price(data: Union[Dict, str]) -> Dict:
    """Analyze volume-price relationships"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    closes = d['close']
    volumes = d['volume']
    dates = d['dates']
    
    recent_closes = closes[-20:]
    recent_volumes = volumes[-20:]
    
    price_trend = (recent_closes[-1] - recent_closes[0]) / recent_closes[0] if recent_closes[0] > 0 else 0
    vol_start = calc_mean(recent_volumes[:5])
    vol_end = calc_mean(recent_volumes[-5:])
    volume_trend = (vol_end - vol_start) / vol_start if vol_start > 0 else 0
    
    divergence_score = 0
    divergence_type = "None"
    
    if price_trend > 0.05 and volume_trend < -0.2:
        divergence_score = 0.8
        divergence_type = "Bearish Divergence (price up, volume down)"
    elif price_trend < -0.05 and volume_trend < -0.2:
        divergence_score = 0.3
        divergence_type = "Potential Selling Exhaustion"
    elif price_trend > 0.05 and volume_trend > 0.3:
        divergence_score = -0.5
        divergence_type = "Bullish Confirmation (price up, volume up)"
    elif price_trend < -0.05 and volume_trend > 0.3:
        divergence_score = 0.7
        divergence_type = "Bearish Confirmation (price down, volume up)"
    
    unusual_volume_dates = []
    avg_vol = calc_mean(volumes[-60:]) if len(volumes) >= 60 else calc_mean(volumes)
    std_vol = calc_std(volumes[-60:]) if len(volumes) >= 60 else calc_std(volumes)
    
    for i in range(-20, 0):
        if volumes[i] > avg_vol + 2 * std_vol:
            unusual_volume_dates.append({
                'date': dates[i],
                'volume': int(volumes[i]),
                'avg_volume': int(avg_vol),
                'multiple': round(volumes[i] / avg_vol, 2)
            })
    
    if divergence_score > 0.6:
        interpretation = "⚠️ Strong bearish divergence"
    elif divergence_score > 0.3:
        interpretation = "⚠️ Moderate bearish divergence"
    elif divergence_score > 0:
        interpretation = "⚠️ Mild concern - volume not confirming"
    elif divergence_score > -0.3:
        interpretation = "✅ Neutral - volume and price in sync"
    elif divergence_score > -0.6:
        interpretation = "✅ Bullish confirmation"
    else:
        interpretation = "✅ Strong bullish confirmation"
    
    return {
        'divergence_score': round(divergence_score, 2),
        'divergence_type': divergence_type,
        'price_trend_20d': round(price_trend * 100, 2),
        'volume_trend_20d': round(volume_trend * 100, 2),
        'unusual_volume_spikes': unusual_volume_dates,
        'current_volume_vs_avg': round(volumes[-1] / avg_vol, 2) if avg_vol > 0 else 0,
        'interpretation': interpretation
    }


def calculate_support_resistance(data: Union[Dict, str]) -> List[Dict]:
    """Calculate support and resistance levels"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    highs = d['high']
    lows = d['low']
    closes = d['close']
    current_price = closes[-1]
    
    levels = []
    window = min(100, len(d['close']))
    
    recent_highs = highs[-window:]
    recent_lows = lows[-window:]
    
    peak_threshold = sorted(recent_highs)[int(len(recent_highs) * 0.90)]
    for i in range(-window, 0):
        if highs[i] >= peak_threshold:
            distance_pct = (highs[i] - current_price) / current_price * 100
            if distance_pct > 2:  # At least 2% above
                levels.append({
                    'type': 'resistance',
                    'price': round(highs[i], 2),
                    'distance_pct': round(distance_pct, 2),
                    'strength': 'strong' if distance_pct < 5 else 'moderate'
                })
    
    valley_threshold = sorted(recent_lows)[int(len(recent_lows) * 0.10)]
    for i in range(-window, 0):
        if lows[i] <= valley_threshold:
            distance_pct = (current_price - lows[i]) / current_price * 100
            if distance_pct > 2:
                levels.append({
                    'type': 'support',
                    'price': round(lows[i], 2),
                    'distance_pct': round(distance_pct, 2),
                    'strength': 'strong' if distance_pct < 5 else 'moderate'
                })
    
    levels.sort(key=lambda x: x['price'])
    unique_levels = []
    for level in levels:
        if not unique_levels or abs(level['price'] - unique_levels[-1]['price']) / level['price'] > 0.02:
            unique_levels.append(level)
    
    supports = [l for l in unique_levels if l['type'] == 'support'][-3:]
    resistances = [l for l in unique_levels if l['type'] == 'resistance'][:3]
    
    return supports + resistances


def calculate_target_price(pattern_data: Dict) -> float:
    """Calculate target price from pattern"""
    return pattern_data.get('target_price', 0.0)


def scan_all_patterns(data: Union[Dict, str]) -> Dict:
    """Scan for all patterns"""
    if isinstance(data, str):
        d = load_data(data)
    else:
        d = data
    
    results = {
        'scan_date': datetime.now().strftime('%Y-%m-%d'),
        'patterns_detected': [],
        'volume_analysis': analyze_volume_price(d),
        'support_resistance': calculate_support_resistance(d),
        'current_price': float(d['close'][-1]),
        'signals': []
    }
    
    detectors = [
        ('W-bottom', lambda: detect_w_bottom(d)),
        ('M-top', lambda: detect_m_top(d)),
        ('H&S Top', lambda: detect_head_shoulders(d, type='top')),
        ('H&S Bottom', lambda: detect_head_shoulders(d, type='bottom')),
        ('False Breakout (Up)', lambda: detect_false_breakout(d, direction='up')),
        ('False Breakout (Down)', lambda: detect_false_breakout(d, direction='down')),
        ('Ascending Triangle', lambda: detect_triangle(d, type='ascending')),
        ('Descending Triangle', lambda: detect_triangle(d, type='descending')),
        ('Bullish Flag', lambda: detect_flag(d, type='bull')),
        ('Bearish Flag', lambda: detect_flag(d, type='bear')),
    ]
    
    for name, detector in detectors:
        try:
            result = detector()
            if result:
                results['patterns_detected'].append(result)
                if 'Bottom' in name or 'Bullish' in name or 'Down' in name:
                    signal = 'BUY'
                elif 'Top' in name or 'Bearish' in name or 'Up' in name:
                    signal = 'SELL'
                else:
                    signal = 'HOLD'
                
                results['signals'].append({
                    'pattern': name,
                    'signal': signal,
                    'confidence': result['confidence'],
                    'entry': result['entry_price'],
                    'target': result['target_price'],
                    'stop': result['stop_loss']
                })
        except Exception as e:
            print(f"Error detecting {name}: {e}")
    
    if results['signals']:
        buy_signals = [s for s in results['signals'] if s['signal'] == 'BUY']
        sell_signals = [s for s in results['signals'] if s['signal'] == 'SELL']
        
        if len(buy_signals) > len(sell_signals):
            avg_confidence = calc_mean([s['confidence'] for s in buy_signals])
            results['overall_signal'] = {
                'direction': 'BUY',
                'confidence': round(avg_confidence, 2),
                'patterns_supporting': len(buy_signals)
            }
        elif len(sell_signals) > len(buy_signals):
            avg_confidence = calc_mean([s['confidence'] for s in sell_signals])
            results['overall_signal'] = {
                'direction': 'SELL',
                'confidence': round(avg_confidence, 2),
                'patterns_supporting': len(sell_signals)
            }
        else:
            results['overall_signal'] = {'direction': 'HOLD', 'confidence': 0.5, 'note': 'Mixed signals'}
    else:
        results['overall_signal'] = {'direction': 'HOLD', 'confidence': 0.5, 'note': 'No clear patterns'}
    
    return results


if __name__ == '__main__':
    data_file = '/root/.openclaw/workspace/caisen_data/0700_HK_2y.csv'
    
    print("🔍 Scanning Tencent (0700.HK) for 蔡森 patterns...")
    print()
    
    results = scan_all_patterns(data_file)
    
    print(f"📊 Scan Date: {results['scan_date']}")
    print(f"💰 Current Price: HKD {results['current_price']:.2f}")
    print()
    
    print(f"📈 Overall Signal: {results['overall_signal']['direction']}")
    print(f"   Confidence: {results['overall_signal']['confidence']*100:.0f}%")
    if 'note' in results['overall_signal']:
        print(f"   Note: {results['overall_signal']['note']}")
    print()
    
    if results['patterns_detected']:
        print(f"🎯 Patterns Detected: {len(results['patterns_detected'])}")
        for pattern in results['patterns_detected']:
            print(f"   • {pattern['pattern']}")
            print(f"     Confidence: {pattern['confidence']*100:.0f}%")
            print(f"     Entry: HKD {pattern['entry_price']:.2f}")
            print(f"     Target: HKD {pattern['target_price']:.2f}")
            print(f"     Stop: HKD {pattern['stop_loss']:.2f}")
            print()
    else:
        print("No clear patterns detected at this time.")
        print()
    
    print(f"📊 Volume Analysis:")
    vol = results['volume_analysis']
    print(f"   Divergence: {vol['divergence_type']}")
    print(f"   Score: {vol['divergence_score']}")
    print(f"   Interpretation: {vol['interpretation']}")
    print()
    
    print(f"📏 Key Levels:")
    for level in results['support_resistance'][:6]:
        marker = "🟢" if level['type'] == 'support' else "🔴"
        print(f"   {marker} {level['type'].upper()}: HKD {level['price']:.2f} ({level['distance_pct']:+.1f}%)")
