#!/usr/bin/env python3
"""
HSI Analysis Tool v10 - Trend-Following + Solar Term Confluence
Target: 50-55% Direction Accuracy (filtered by solar term timing)

Integration of:
- HSI v9: Trend-following (MA50/200, RSI, OBV) for DIRECTION
- 江恩小龍 Solar Terms: Confluence scoring for TIMING

Key Innovation:
- Only trade high-conviction signals when BOTH systems align
- Solar terms tell you WHEN, v9 tells you WHICH DIRECTION
- Filter out v9 signals outside solar term alert windows

v10 Approach:
- PRIMARY: Trend score from v9 (-1 to +1)
- SECONDARY: Momentum + Volume from v9
- TIMING FILTER: Solar term confluence score (0-100+)
- FINAL SIGNAL: Only generate prediction if confluence > threshold
"""

import csv
import json
import sys
import os
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev
import math

# Add gann_solar to path for solar term integration
sys.path.insert(0, '/root/.openclaw/workspace/gann_solar')
from solar_term_calculator import (
    get_solar_terms_for_year,
    calculate_confluence_score,
    analyze_turn_windows
)

# ============================================================================
# DATA PARSING (same as v9)
# ============================================================================

def parse_volume(vol_str):
    if not vol_str:
        return 0
    vol_str = str(vol_str).strip().upper()
    return float(vol_str.replace('B', '000000000').replace('M', '000000').replace(',', '')) if vol_str else 0

def parse_hsi_data(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    for line in content.strip().split('\n')[1:]:
        try:
            parts = next(csv.reader([line]))
            if len(parts) < 7:
                continue
            date_str = parts[0].strip()
            close = float(parts[1].replace(',', ''))
            open_p = float(parts[2].replace(',', '')) if parts[2].strip() else close
            high = float(parts[3].replace(',', '')) if parts[3].strip() else close
            low = float(parts[4].replace(',', '')) if parts[4].strip() else close
            volume = parse_volume(parts[5]) if len(parts) > 5 else 0
            change_pct = float(parts[6].replace('%', '')) if len(parts) > 6 and parts[6].strip() else 0
            parts_date = date_str.split('/')
            if len(parts_date) != 3:
                continue
            month, day, year = int(parts_date[0]), int(parts_date[1]), int(parts_date[2])
            if year < 100:
                year += 2000
            data.append({'date': datetime(year, month, day), 'open': open_p, 'high': high, 'low': low, 'close': close, 'volume': volume, 'change_pct': change_pct})
        except:
            continue
    data.sort(key=lambda x: x['date'])
    return data

# ============================================================================
# TECHNICAL INDICATORS (same as v9)
# ============================================================================

def sma(data, period, end_idx):
    if end_idx < period - 1:
        return None
    return mean([data[i]['close'] for i in range(end_idx - period + 1, end_idx + 1)])

def rsi(data, period, end_idx):
    if end_idx < period:
        return 50
    gains = [max(data[i]['close'] - data[i-1]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    losses = [max(data[i-1]['close'] - data[i]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    avg_gain, avg_loss = mean(gains), mean(losses)
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def obv(data, end_idx):
    if end_idx < 1:
        return 0
    obv_val = 0
    for i in range(1, end_idx + 1):
        if data[i]['close'] > data[i-1]['close']:
            obv_val += data[i]['volume']
        elif data[i]['close'] < data[i-1]['close']:
            obv_val -= data[i]['volume']
    return obv_val

def obv_trend(data, end_idx, period=20):
    if end_idx < period * 2:
        return 0
    current_obv = obv(data, end_idx)
    prev_obv = obv(data, end_idx - period)
    if prev_obv == 0:
        return 0
    change = (current_obv - prev_obv) / abs(prev_obv) * 100
    if change > 5:
        return 1
    elif change < -5:
        return -1
    return 0

# ============================================================================
# SOLAR TERM INTEGRATION (NEW for v10)
# ============================================================================

def load_solar_term_signals(data):
    """
    Load solar term confluence signals for the entire data range.
    Uses 江恩小龍's methodology from gann_solar module.
    """
    # Get date range from data
    min_date = min(d['date'] for d in data)
    max_date = max(d['date'] for d in data)
    
    start_year = min_date.year - 1  # Include buffer
    end_year = max_date.year + 1
    
    print(f"Loading solar term signals for {start_year}-{end_year}...")
    
    # Get all solar terms for the range
    all_solar_terms = []
    for year in range(start_year, end_year + 1):
        terms = get_solar_terms_for_year(year)
        all_solar_terms.extend(terms)
    
    # Create a lookup dict: date -> confluence score
    date_confluence = {}
    
    # Generate signals from major historical pivots
    # Extended pivot list covering 1980-2026 (from HSI analysis research)
    major_pivots = [
        # 1980s
        datetime(1987, 10, 1),   # Black Monday low
        datetime(1989, 6, 1),    # Major top
        # 1990s
        datetime(1994, 1, 1),    # Major low
        datetime(1997, 8, 1),    # Asian crisis top
        datetime(1998, 8, 1),    # Asian crisis low
        # 2000s
        datetime(2000, 3, 1),    # Dotcom top
        datetime(2003, 4, 1),    # SARS low
        datetime(2007, 10, 1),   # GFC top
        datetime(2008, 10, 1),   # GFC low
        # 2010s
        datetime(2015, 4, 1),    # Bubble top
        datetime(2016, 1, 1),    # 大寒 low
        datetime(2018, 1, 26),   # 大寒 top
        # 2020s
        datetime(2020, 3, 23),   # 春分 COVID low (Tier 1)
        datetime(2021, 2, 18),   # 雨水 Major top
        datetime(2022, 10, 24),  # 霜降 Major low
        datetime(2024, 4, 20),   # 穀雨 bottom (小龍's prediction)
        datetime(2024, 5, 21),   # 小滿 top (小龍's prediction)
        datetime(2024, 10, 8),   # 寒露 Recent high
    ]
    
    # Analyze turn windows from these pivots
    all_signals = []
    for pivot in major_pivots:
        # Add anniversary signals (1-5 years)
        for year_offset in range(1, 7):
            try:
                anniv = pivot.replace(year=pivot.year + year_offset)
                all_signals.append({
                    'type': f'Anniversary_{year_offset}yr',
                    'date': anniv,
                    'strength': 'strong' if year_offset <= 3 else 'medium'
                })
            except:
                pass
        
        # Add Gann square root cycles from each pivot
        current = min_date
        while current <= max_date:
            days_elapsed = (current - pivot).days
            if days_elapsed > 0:
                sqrt_cycle = int(math.sqrt(days_elapsed))
                for i in range(1, 4):
                    future_days = (sqrt_cycle + i) ** 2
                    future_date = pivot + timedelta(days=future_days)
                    if min_date <= future_date <= max_date:
                        all_signals.append({
                            'type': f'Sqrt_{sqrt_cycle + i}²',
                            'date': future_date,
                            'strength': 'medium'
                        })
            current += timedelta(days=365)
    
    # Add solar term signals (all tiers)
    for term in all_solar_terms:
        all_signals.append({
            'type': f'SolarTerm_Tier{term["tier"]}',
            'date': term['date'],
            'tier': term['tier'],
            'angle': term.get('gann_angle'),
            'strength': 'strong' if term['tier'] == 1 else ('medium' if term['tier'] == 2 else 'weak')
        })
    
    print(f"Generated {len(all_signals)} total signals from {len(major_pivots)} pivots")
    
    # Calculate confluence score for each date in range
    current = min_date
    while current <= max_date:
        result = calculate_confluence_score(current, all_signals)
        date_confluence[current.strftime('%Y-%m-%d')] = {
            'score': result['score'],
            'confidence': result['confidence'],
            'matching_signals': result.get('matching_signals', [])
        }
        current += timedelta(days=1)
    
    print(f"Loaded {len(date_confluence)} days of solar term confluence data")
    return date_confluence

def get_solar_term_bonus(date, date_confluence):
    """
    Get solar term confluence bonus for a given date.
    Returns bonus multiplier (0.0 to 0.5) based on confluence score.
    """
    date_str = date.strftime('%Y-%m-%d')
    
    if date_str not in date_confluence:
        return 0.0, 'LOW', []
    
    confluence = date_confluence[date_str]
    score = confluence['score']
    confidence = confluence['confidence']
    signals = confluence.get('matching_signals', [])
    
    # Convert score to bonus multiplier
    # Higher confluence = higher bonus to confidence
    if score >= 70:  # VERY HIGH
        bonus = 0.4  # +40% confidence boost
    elif score >= 50:  # HIGH
        bonus = 0.25  # +25% confidence boost
    elif score >= 30:  # MEDIUM
        bonus = 0.1   # +10% confidence boost
    else:  # LOW
        bonus = 0.0   # No boost
    
    return bonus, confidence, signals

# ============================================================================
# V10 SIGNAL GENERATION (Integrated)
# ============================================================================

def find_major_extremes(data, window=60, min_move=15):
    tops, bottoms = [], []
    for i in range(window, len(data) - window):
        if all(data[j]['high'] <= data[i]['high'] for j in range(i-window, i+window) if j != i):
            min_after = min(data[i:min(i+180, len(data))], key=lambda x: x['low'])['low']
            if (data[i]['high'] - min_after) / data[i]['high'] * 100 > min_move:
                tops.append({'date': data[i]['date'], 'price': data[i]['high'], 'drop': (data[i]['high'] - min_after) / data[i]['high'] * 100})
        if all(data[j]['low'] >= data[i]['low'] for j in range(i-window, i+window) if j != i):
            max_after = max(data[i:min(i+180, len(data))], key=lambda x: x['high'])['high']
            if (max_after - data[i]['low']) / data[i]['low'] * 100 > min_move:
                bottoms.append({'date': data[i]['date'], 'price': data[i]['low'], 'rise': (max_after - data[i]['low']) / data[i]['low'] * 100})
    return tops, bottoms

def calculate_trend_score(data, end_idx):
    """Calculate primary trend score (-1 to +1) - same as v9"""
    if end_idx < 200:
        return 0
    
    scores = []
    
    # 1. Price vs 50-day MA (weight: 0.3)
    m50 = sma(data, 50, end_idx)
    if m50:
        pct_vs_m50 = (data[end_idx]['close'] - m50) / m50
        if pct_vs_m50 > 0.05:
            scores.append(0.3)
        elif pct_vs_m50 > 0:
            scores.append(0.15)
        elif pct_vs_m50 > -0.05:
            scores.append(-0.15)
        else:
            scores.append(-0.3)
    
    # 2. Price vs 200-day MA (weight: 0.3)
    m200 = sma(data, 200, end_idx)
    if m200:
        pct_vs_m200 = (data[end_idx]['close'] - m200) / m200
        if pct_vs_m200 > 0.05:
            scores.append(0.3)
        elif pct_vs_m200 > 0:
            scores.append(0.15)
        elif pct_vs_m200 > -0.05:
            scores.append(-0.15)
        else:
            scores.append(-0.3)
    
    # 3. 50-day MA slope (weight: 0.2)
    m50_prev = sma(data, 50, end_idx - 20)
    if m50 and m50_prev:
        slope = (m50 - m50_prev) / m50_prev
        if slope > 0.01:
            scores.append(0.2)
        elif slope > 0:
            scores.append(0.1)
        elif slope > -0.01:
            scores.append(-0.1)
        else:
            scores.append(-0.2)
    
    # 4. Simple trend strength (weight: 0.2)
    m50_20 = sma(data, 50, end_idx - 20) if end_idx >= 70 else m50
    if m50 and m50_20:
        if m50 > m50_20 * 1.01:
            scores.append(0.2)  # Uptrend
        elif m50 < m50_20 * 0.99:
            scores.append(-0.2)  # Downtrend
        else:
            scores.append(0)  # Flat
    
    return sum(scores)

def calculate_momentum_score(data, end_idx):
    """Calculate momentum score (-0.3 to +0.3) - same as v9"""
    if end_idx < 90:
        return 0
    
    scores = []
    
    # 1. 90-day rate of change (weight: 0.15)
    roc_90 = (data[end_idx]['close'] - data[end_idx - 90]['close']) / data[end_idx - 90]['close']
    if roc_90 > 0.15:
        scores.append(0.15)
    elif roc_90 > 0.05:
        scores.append(0.08)
    elif roc_90 > -0.05:
        scores.append(0)
    elif roc_90 > -0.15:
        scores.append(-0.08)
    else:
        scores.append(-0.15)
    
    # 2. RSI (weight: 0.15)
    rsi_val = rsi(data, 14, end_idx)
    if rsi_val > 70:
        scores.append(-0.1)  # Overbought
    elif rsi_val > 55:
        scores.append(0.08)
    elif rsi_val > 45:
        scores.append(0)
    elif rsi_val > 30:
        scores.append(-0.08)
    else:
        scores.append(0.1)  # Oversold
    
    return sum(scores)

def calculate_volume_score(data, end_idx):
    """Calculate volume confirmation score (-0.2 to +0.2) - same as v9"""
    if end_idx < 40:
        return 0
    
    obv_dir = obv_trend(data, end_idx, 20)
    price_change = data[end_idx]['close'] - data[end_idx - 20]['close']
    
    if obv_dir > 0 and price_change > 0:
        return 0.2
    elif obv_dir < 0 and price_change < 0:
        return -0.2
    elif obv_dir > 0 and price_change < 0:
        return 0.15  # Bullish divergence
    elif obv_dir < 0 and price_change > 0:
        return -0.15  # Bearish divergence
    return 0

def generate_prediction_v10(data, date, tops, bottoms, date_confluence):
    """
    v10: Generate prediction with solar term timing filter.
    
    Key difference from v9:
    - Solar term confluence affects BOTH confidence AND whether we generate a signal
    - Low confluence = reduce confidence or skip prediction
    - High confluence = boost confidence
    """
    hist = [d for d in data if d['date'] <= date]
    if len(hist) < 250:
        return None
    
    end_idx = len(hist) - 1
    current_price = hist[-1]['close']
    
    # Calculate component scores (same as v9)
    trend_score = calculate_trend_score(hist, end_idx)  # -1 to +1
    momentum_score = calculate_momentum_score(hist, end_idx)  # -0.3 to +0.3
    volume_score = calculate_volume_score(hist, end_idx)  # -0.2 to +0.2
    
    # Combined score (trend is dominant)
    combined_score = trend_score * 0.6 + momentum_score * 0.25 + volume_score * 0.15
    
    # Get solar term confluence bonus (NEW for v10)
    solar_bonus, solar_confidence, solar_signals = get_solar_term_bonus(date, date_confluence)
    
    # Determine preliminary prediction
    if combined_score > 0.15:
        prelim_direction = 'BULLISH'
    elif combined_score < -0.15:
        prelim_direction = 'BEARISH'
    else:
        prelim_direction = 'NEUTRAL'
    
    # V10 KEY INNOVATION: Solar term filtering
    # If solar confluence is LOW, reduce confidence or skip
    # If solar confluence is HIGH, boost confidence
    
    base_confidence = 55 + abs(combined_score) * 100
    
    # Apply solar term adjustment
    if solar_bonus >= 0.4:  # VERY HIGH confluence (70+ points)
        base_confidence += 15  # Major boost
        confidence_boost = 15
    elif solar_bonus >= 0.25:  # HIGH confluence (50-69 points)
        base_confidence += 10
        confidence_boost = 10
    elif solar_bonus >= 0.1:  # MEDIUM confluence (30-49 points)
        base_confidence += 5
        confidence_boost = 5
    else:  # LOW confluence (<30 points)
        base_confidence -= 10  # Penalty for low confluence
        confidence_boost = -10
    
    # Cap confidence
    confidence = min(max(base_confidence, 50), 90)
    
    # V10 FILTER: Skip prediction if confluence is too low AND signal is weak
    # This reduces false signals
    skip_prediction = False
    if solar_bonus == 0 and abs(combined_score) < 0.2:
        # Low confluence + weak technical signal = skip
        skip_prediction = True
        prelim_direction = 'NEUTRAL'
        confidence = 50
    
    # Calculate risk score (0-100, higher = more bearish)
    risk_score = 50 - (combined_score * 50)
    
    # Expected move
    if prelim_direction == 'BEARISH':
        expected_move = -5 - (confidence - 55) * 0.2
    elif prelim_direction == 'BULLISH':
        expected_move = 5 + (confidence - 55) * 0.2
    else:
        expected_move = 0
    
    # Build signals list
    signals = []
    m50 = sma(hist, 50, end_idx)
    m200 = sma(hist, 200, end_idx)
    if m50 and m200:
        if data[end_idx]['close'] > m50 > m200:
            signals.append({'type': 'TREND', 'direction': 'BULLISH', 'weight': 0.6, 'details': 'Price > MA50 > MA200'})
        elif data[end_idx]['close'] < m50 < m200:
            signals.append({'type': 'TREND', 'direction': 'BEARISH', 'weight': 0.6, 'details': 'Price < MA50 < MA200'})
    
    rsi_val = rsi(hist, 14, end_idx)
    if rsi_val:
        if rsi_val > 70:
            signals.append({'type': 'RSI', 'direction': 'BEARISH', 'weight': 0.2, 'details': f'RSI {rsi_val:.0f} overbought'})
        elif rsi_val < 30:
            signals.append({'type': 'RSI', 'direction': 'BULLISH', 'weight': 0.2, 'details': f'RSI {rsi_val:.0f} oversold'})
    
    obv_dir = obv_trend(hist, end_idx, 20)
    if obv_dir != 0:
        direction = 'BULLISH' if obv_dir > 0 else 'BEARISH'
        signals.append({'type': 'OBV', 'direction': direction, 'weight': 0.2, 'details': f'OBV {"rising" if obv_dir > 0 else "falling"}'})
    
    # Add solar term signal (NEW)
    if solar_bonus > 0:
        signals.append({
            'type': 'SOLAR_TERM',
            'direction': 'TIMING',
            'weight': solar_bonus,
            'details': f'{solar_confidence} confluence ({len(solar_signals)} signals)',
            'confluence_score': date_confluence.get(date.strftime('%Y-%m-%d'), {}).get('score', 0)
        })
    
    # Calculate actual outcome for backtest
    forecast_end = date + timedelta(days=90)
    future = [d for d in data if date < d['date'] <= forecast_end]
    actual_outcome = None
    actual_move_pct = None
    if future:
        actual_move_pct = (future[-1]['close'] - current_price) / current_price * 100
        if actual_move_pct < -10:
            actual_outcome = 'BEARISH'
        elif actual_move_pct < -5:
            actual_outcome = 'NEUTRAL_BEARS'
        elif actual_move_pct < 5:
            actual_outcome = 'NEUTRAL'
        elif actual_move_pct < 10:
            actual_outcome = 'NEUTRAL_BULLS'
        else:
            actual_outcome = 'BULLISH'
    
    return {
        'date': date,
        'price': current_price,
        'prediction': prelim_direction,
        'confidence': confidence,
        'risk_score': risk_score,
        'expected_move': expected_move,
        'trend_score': trend_score,
        'momentum_score': momentum_score,
        'volume_score': volume_score,
        'solar_bonus': solar_bonus,
        'solar_confidence': solar_confidence,
        'solar_confluence_score': date_confluence.get(date.strftime('%Y-%m-%d'), {}).get('score', 0),
        'skip_prediction': skip_prediction,
        'signals': signals,
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct
    }

# ============================================================================
# BACKTESTING (same structure as v9, enhanced metrics)
# ============================================================================

def run_walk_forward_backtest(data, tops, bottoms, date_confluence):
    """Walk-Forward: 5-year train, 1-year test (same as v9)"""
    all_results = []
    cycle_results = []
    
    cycles = [
        (datetime(2015,1,1), datetime(2020,1,1), datetime(2020,12,31)),
        (datetime(2016,1,1), datetime(2021,1,1), datetime(2021,12,31)),
        (datetime(2017,1,1), datetime(2022,1,1), datetime(2022,12,31)),
        (datetime(2018,1,1), datetime(2023,1,1), datetime(2023,12,31)),
        (datetime(2019,1,1), datetime(2024,1,1), datetime(2024,12,31)),
        (datetime(2020,1,1), datetime(2025,1,1), datetime(2025,12,31)),
        (datetime(2021,1,1), datetime(2026,1,1), datetime(2026,2,20)),
    ]
    
    for train_start, test_start, test_end in cycles:
        current = test_start
        cycle_preds = []
        while current <= test_end:
            pred = generate_prediction_v10(data, current, tops, bottoms, date_confluence)
            if pred and not pred.get('skip_prediction', False):
                cycle_preds.append(pred)
            current += timedelta(days=30)
        
        if cycle_preds:
            cycle_acc = calc_accuracy(cycle_preds)
            cycle_results.append({
                'test_period': f"{test_start.strftime('%Y')}-{test_end.strftime('%Y')}",
                'predictions': len(cycle_preds),
                'accuracy': cycle_acc.get('accuracy', 0),
                'high_conf': cycle_acc.get('high_conf', 0),
                'high_conf_acc': cycle_acc.get('high_conf_acc', 0)
            })
            all_results.extend(cycle_preds)
    
    return all_results, cycle_results

def calc_accuracy(results):
    """Calculate accuracy metrics (same as v9)"""
    valid = [r for r in results if r['actual_outcome'] is not None]
    if not valid:
        return {}
    
    correct = sum(1 for r in valid if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    high_conf = [r for r in valid if r['confidence'] >= 70]
    hc_correct = sum(1 for r in high_conf if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    major_drops = [r for r in valid if r['actual_move_pct'] and r['actual_move_pct'] < -15]
    md_pred = [r for r in major_drops if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']]
    
    major_rallies = [r for r in valid if r['actual_move_pct'] and r['actual_move_pct'] > 15]
    mr_pred = [r for r in major_rallies if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']]
    
    bullish = len([r for r in valid if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']])
    bearish = len([r for r in valid if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']])
    
    # Confidence calibration
    conf_bins = {50: [], 60: [], 70: [], 80: []}
    for r in valid:
        for bin_edge in conf_bins.keys():
            if r['confidence'] >= bin_edge and r['confidence'] < bin_edge + 10:
                conf_bins[bin_edge].append(r)
                break
    
    conf_calibration = {}
    for bin_edge, bin_results in conf_bins.items():
        if bin_results:
            bin_correct = sum(1 for r in bin_results if (
                (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
                (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
                (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
            ))
            conf_calibration[f"{bin_edge}-{bin_edge+9}"] = bin_correct / len(bin_results) * 100
    
    # NEW for v10: Solar term correlation
    high_solar = [r for r in valid if r.get('solar_confluence_score', 0) >= 50]
    high_solar_correct = sum(1 for r in high_solar if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    low_solar = [r for r in valid if r.get('solar_confluence_score', 0) < 30]
    low_solar_correct = sum(1 for r in low_solar if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    return {
        'total': len(valid),
        'accuracy': correct / len(valid) * 100 if valid else 0,
        'high_conf': len(high_conf),
        'high_conf_acc': hc_correct / len(high_conf) * 100 if high_conf else 0,
        'major_drops': len(major_drops),
        'md_pred': len(md_pred),
        'md_recall': len(md_pred)/len(major_drops)*100 if major_drops else 0,
        'major_rallies': len(major_rallies),
        'mr_pred': len(mr_pred),
        'mr_recall': len(mr_pred)/len(major_rallies)*100 if major_rallies else 0,
        'bullish': bullish,
        'bearish': bearish,
        'bias': bearish/(bullish+bearish)*100 if (bullish+bearish) > 0 else 0,
        'conf_calibration': conf_calibration,
        # NEW: Solar term correlation
        'high_solar_count': len(high_solar),
        'high_solar_acc': high_solar_correct / len(high_solar) * 100 if high_solar else 0,
        'low_solar_count': len(low_solar),
        'low_solar_acc': low_solar_correct / len(low_solar) * 100 if low_solar else 0
    }

def save_status(accuracy, current, version='v10'):
    status = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'model': version,
        'accuracy': accuracy,
        'current': current,
        'status': 'complete'
    }
    with open('/root/.openclaw/workspace/hsi_status.json', 'w') as f:
        json.dump(status, f, indent=2, default=str)

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*80)
    print("HSI v10 - TREND-FOLLOWING + SOLAR TERM CONFLUENCE (江恩小龍)")
    print("="*80)
    
    print("\nLoading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    print(f"Loaded {len(data)} points ({data[0]['date'].strftime('%Y-%m-%d')} to {data[-1]['date'].strftime('%Y-%m-%d')})")
    
    print("\nFinding major extremes...")
    tops, bottoms = find_major_extremes(data)
    print(f"{len(tops)} tops, {len(bottoms)} bottoms")
    
    print("\n" + "="*80)
    print("LOADING SOLAR TERM CONFLUENCE DATA (江恩小龍 Methodology)")
    print("="*80)
    date_confluence = load_solar_term_signals(data)
    
    print("\n" + "="*80)
    print("RUNNING WALK-FORWARD BACKTEST (v10)")
    print("="*80)
    results, cycle_results = run_walk_forward_backtest(data, tops, bottoms, date_confluence)
    
    print("\n--- Walk-Forward Cycle Results ---")
    for cycle in cycle_results:
        status = "✅" if cycle['accuracy'] >= 50 else "⚠️"
        print(f"{cycle['test_period']}: {cycle['accuracy']:.1f}% acc, {cycle['predictions']} preds {status}")
    
    accuracy = calc_accuracy(results)
    current = generate_prediction_v10(data, datetime(2026,2,20), tops, bottoms, date_confluence)
    
    print("\n" + "="*80)
    print("AGGREGATE PERFORMANCE")
    print("="*80)
    print(f"Total Predictions: {accuracy['total']}")
    print(f"Overall Accuracy: {accuracy['accuracy']:.1f}%")
    print(f"High Confidence (70%+): {accuracy['high_conf']} predictions @ {accuracy['high_conf_acc']:.1f}% acc")
    print(f"Major Drop Recall: {accuracy['md_recall']:.1f}% ({accuracy['md_pred']}/{accuracy['major_drops']})")
    print(f"Major Rally Recall: {accuracy['mr_recall']:.1f}% ({accuracy['mr_pred']}/{accuracy['major_rallies']})")
    print(f"Bias: {accuracy['bias']:.1f}% bearish")
    
    # NEW: Solar term correlation
    print("\n" + "="*80)
    print("SOLAR TERM CORRELATION (NEW v10)")
    print("="*80)
    print(f"High Solar (50+ pts): {accuracy['high_solar_count']} predictions @ {accuracy['high_solar_acc']:.1f}% acc")
    print(f"Low Solar (<30 pts): {accuracy['low_solar_count']} predictions @ {accuracy['low_solar_acc']:.1f}% acc")
    print(f"Solar Term Edge: {accuracy['high_solar_acc'] - accuracy['low_solar_acc']:.1f} percentage points")
    
    print("\n" + "="*80)
    print("CURRENT ANALYSIS (Feb 20, 2026)")
    print("="*80)
    if current:
        print(f"Prediction: {current['prediction']}")
        print(f"Confidence: {current['confidence']:.0f}%")
        print(f"Risk Score: {current['risk_score']:.0f}/100")
        print(f"Expected Move (90d): {current['expected_move']:.1f}%")
        print(f"Trend Score: {current['trend_score']:.2f}")
        print(f"Momentum Score: {current['momentum_score']:.2f}")
        print(f"Volume Score: {current['volume_score']:.2f}")
        print(f"Solar Confluence: {current['solar_confluence_score']} pts ({current['solar_confidence']})")
        print(f"Solar Bonus: +{current['solar_bonus']*100:.0f}% confidence")
        
        if current['signals']:
            print("\nSignals:")
            for sig in current['signals']:
                print(f"  • {sig['type']}: {sig['direction']} ({sig['details']})")
    
    # Save status
    save_status(accuracy, current, 'v10')
    print("\n" + "="*80)
    print("Status saved to hsi_status.json")
    print("="*80)
    
    # Save WFO summary
    wfo_summary = {
        'cycles': cycle_results,
        'aggregate': accuracy,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    with open('/root/.openclaw/workspace/hsi_v10_wfo_summary.json', 'w') as f:
        json.dump(wfo_summary, f, indent=2, default=str)
    print("WFO summary saved to hsi_v10_wfo_summary.json")
    
    # Save detailed results
    with open('/root/.openclaw/workspace/hsi_backtest_v10_results.csv', 'w') as f:
        f.write('date,price,prediction,confidence,risk_score,expected_move,trend_score,momentum_score,volume_score,solar_confluence,solar_bonus,actual_outcome,actual_move_pct\n')
        for r in results:
            f.write(f"{r['date'].strftime('%Y-%m-%d')},{r['price']},{r['prediction']},{r['confidence']:.1f},{r['risk_score']:.1f},{r['expected_move']:.2f},{r['trend_score']:.3f},{r['momentum_score']:.3f},{r['volume_score']:.3f},{r.get('solar_confluence_score', 0)},{r.get('solar_bonus', 0):.2f},{r.get('actual_outcome', 'N/A')},{r.get('actual_move_pct', 'N/A')}\n")
    print("Results saved to hsi_backtest_v10_results.csv")
    
    print("\n" + "="*80)
    print("V10 DEVELOPMENT COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
