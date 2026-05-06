#!/usr/bin/env python3
"""
HSI Analysis Tool v9 - Trend-Following with Gann Confirmation
Target: 55-60% Direction Accuracy

Key Lessons from v7-v8 Failures:
1. Gann anniversaries alone are NOT predictive at 90-day horizon
2. Counter-trend predictions fail (don't fight the trend!)
3. High confidence ≠ high accuracy (calibration broken)
4. Simpler is better - trend + momentum + volume

v9 Approach:
- PRIMARY: Trend-following (price vs 50/200 MA, ADX for trend strength)
- SECONDARY: Momentum (RSI, rate of change)
- TERTIARY: Volume confirmation (OBV trend)
- GANN: Only as tiebreaker/confirmation, NOT primary signal
"""

import csv
import json
from datetime import datetime, timedelta, timezone
from statistics import mean, stdev
import math

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

def sma(data, period, end_idx):
    if end_idx < period - 1:
        return None
    return mean([data[i]['close'] for i in range(end_idx - period + 1, end_idx + 1)])

def ema(data, period, end_idx):
    if end_idx < period - 1:
        return None
    multiplier = 2 / (period + 1)
    ema_val = sma(data, period, end_idx)
    for i in range(end_idx - period + 2, end_idx + 1):
        ema_val = (data[i]['close'] - ema_val) * multiplier + ema_val
    return ema_val

def rsi(data, period, end_idx):
    if end_idx < period:
        return 50
    gains = [max(data[i]['close'] - data[i-1]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    losses = [max(data[i-1]['close'] - data[i]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    avg_gain, avg_loss = mean(gains), mean(losses)
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def atr(data, period, end_idx):
    if end_idx < period:
        return None
    tr_values = []
    for i in range(end_idx - period + 1, end_idx + 1):
        high_low = data[i]['high'] - data[i]['low']
        high_close = abs(data[i]['high'] - data[i-1]['close'])
        low_close = abs(data[i]['low'] - data[i-1]['close'])
        tr_values.append(max(high_low, high_close, low_close))
    return mean(tr_values)

def adx(data, period, end_idx):
    """Calculate ADX for trend strength"""
    if end_idx < period * 2:
        return 20  # Default to weak trend
    
    plus_dm, minus_dm, tr_values = [], [], []
    for i in range(end_idx - period + 1, end_idx + 1):
        high_move = data[i]['high'] - data[i-1]['high']
        low_move = data[i-1]['low'] - data[i]['low']
        plus_dm.append(max(high_move, 0) if high_move > low_move else 0)
        minus_dm.append(max(low_move, 0) if low_move > high_move else 0)
        
        high_low = data[i]['high'] - data[i]['low']
        high_close = abs(data[i]['high'] - data[i-1]['close'])
        low_close = abs(data[i]['low'] - data[i-1]['close'])
        tr_values.append(max(high_low, high_close, low_close))
    
    atr_val = mean(tr_values)
    if atr_val == 0:
        return 20
    
    plus_di = (mean(plus_dm) / atr_val) * 100
    minus_di = (mean(minus_dm) / atr_val) * 100
    dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
    return dx

def obv(data, end_idx):
    """Calculate On-Balance Volume"""
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
    """Determine OBV trend direction"""
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

def gann_confirmation_v9(date, tops, bottoms, current_price, trend_direction):
    """
    v9: Gann as CONFIRMATION only, not primary signal
    Only add weight if Gann agrees with trend
    """
    confirmation_bonus = 0
    
    # Check for major anniversary alignment with trend
    major_cycles = {'5-year': 1825, '7-year': 2555}
    
    if trend_direction == 'BEARISH':
        # Look for top anniversaries that confirm bearish view
        for top in tops[-10:]:
            for name, days in major_cycles.items():
                anniv = top['date'] + timedelta(days=days)
                diff = abs((date - anniv).days)
                if diff <= 20:
                    confirmation_bonus += 0.15 * (1 - diff/20)
    
    elif trend_direction == 'BULLISH':
        # Look for bottom anniversaries that confirm bullish view
        for bot in bottoms[-10:]:
            for name, days in major_cycles.items():
                anniv = bot['date'] + timedelta(days=days)
                diff = abs((date - anniv).days)
                if diff <= 20:
                    confirmation_bonus += 0.15 * (1 - diff/20)
    
    # Cap the bonus
    return min(confirmation_bonus, 0.3)

def calculate_trend_score(data, end_idx):
    """
    Calculate primary trend score (-1 to +1)
    Negative = bearish, Positive = bullish
    """
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
    
    # 4. ADX trend strength (weight: 0.2)
    adx_val = adx(data, 14, end_idx)
    plus_di, minus_di = 0, 0
    if end_idx >= 28:
        # Simplified DI calculation
        tr_sum, plus_dm_sum, minus_dm_sum = 0, 0, 0
        for i in range(end_idx - 13, end_idx + 1):
            high_low = data[i]['high'] - data[i]['low']
            high_close = abs(data[i]['high'] - data[i-1]['close'])
            low_close = abs(data[i]['low'] - data[i-1]['close'])
            tr_sum += max(high_low, high_close, low_close)
            
            high_move = data[i]['high'] - data[i-1]['high']
            low_move = data[i-1]['low'] - data[i]['low']
            plus_dm_sum += max(high_move, 0) if high_move > low_move else 0
            minus_dm_sum += max(low_move, 0) if low_move > high_move else 0
        
        atr_val = tr_sum / 14
        if atr_val > 0:
            plus_di = (plus_dm_sum / atr_val) * 100
            minus_di = (minus_dm_sum / atr_val) * 100
    
    if adx_val > 25:  # Strong trend
        if plus_di > minus_di:
            scores.append(0.2)
        else:
            scores.append(-0.2)
    else:
        scores.append(0)  # Weak trend, no directional bias
    
    return sum(scores)

def calculate_momentum_score(data, end_idx):
    """Calculate momentum score (-0.3 to +0.3)"""
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
        scores.append(-0.1)  # Overbought = caution
    elif rsi_val > 55:
        scores.append(0.08)
    elif rsi_val > 45:
        scores.append(0)
    elif rsi_val > 30:
        scores.append(-0.08)
    else:
        scores.append(0.1)  # Oversold = opportunity
    
    return sum(scores)

def calculate_volume_score(data, end_idx):
    """Calculate volume confirmation score (-0.2 to +0.2)"""
    if end_idx < 40:
        return 0
    
    obv_dir = obv_trend(data, end_idx, 20)
    price_change = data[end_idx]['close'] - data[end_idx - 20]['close']
    
    if obv_dir > 0 and price_change > 0:
        return 0.2  # Confirmed uptrend
    elif obv_dir < 0 and price_change < 0:
        return -0.2  # Confirmed downtrend
    elif obv_dir > 0 and price_change < 0:
        return 0.15  # Bullish divergence
    elif obv_dir < 0 and price_change > 0:
        return -0.15  # Bearish divergence
    return 0

def generate_prediction_v9(data, date, tops, bottoms):
    hist = [d for d in data if d['date'] <= date]
    if len(hist) < 250:
        return None
    
    end_idx = len(hist) - 1
    current_price = hist[-1]['close']
    
    # Calculate component scores
    trend_score = calculate_trend_score(hist, end_idx)  # -1 to +1
    momentum_score = calculate_momentum_score(hist, end_idx)  # -0.3 to +0.3
    volume_score = calculate_volume_score(hist, end_idx)  # -0.2 to +0.2
    
    # Combined score (trend is dominant)
    combined_score = trend_score * 0.6 + momentum_score * 0.25 + volume_score * 0.15
    
    # Determine preliminary prediction
    if combined_score > 0.15:
        prelim_direction = 'BULLISH'
    elif combined_score < -0.15:
        prelim_direction = 'BEARISH'
    else:
        prelim_direction = 'NEUTRAL'
    
    # Apply Gann confirmation bonus
    gann_bonus = gann_confirmation_v9(date, tops, bottoms, current_price, prelim_direction)
    
    # Adjust confidence based on Gann confirmation
    base_confidence = 55 + abs(combined_score) * 100
    if gann_bonus > 0.1:
        base_confidence += 10  # Gann confirms
    elif prelim_direction == 'NEUTRAL' and gann_bonus > 0:
        # Gann suggests direction when trend is neutral
        if prelim_direction == 'NEUTRAL':
            # Check if Gann suggests a direction
            if combined_score > 0:
                prelim_direction = 'BULLISH'
                base_confidence += 5
            elif combined_score < 0:
                prelim_direction = 'BEARISH'
                base_confidence += 5
    
    confidence = min(max(base_confidence, 50), 85)
    
    # Calculate risk score (0-100, higher = more bearish)
    risk_score = 50 - (combined_score * 50)
    
    # Expected move
    if prelim_direction == 'BEARISH':
        expected_move = -5 - (confidence - 55) * 0.2
    elif prelim_direction == 'BULLISH':
        expected_move = 5 + (confidence - 55) * 0.2
    else:
        expected_move = 0
    
    # Build signals list for reporting
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
    
    if gann_bonus > 0.1:
        signals.append({'type': 'GANN', 'direction': prelim_direction, 'weight': gann_bonus, 'details': 'Anniversary confirmation'})
    
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
        'date': date, 'price': current_price, 'prediction': prelim_direction,
        'confidence': confidence, 'risk_score': risk_score, 'expected_move': expected_move,
        'trend_score': trend_score, 'momentum_score': momentum_score, 'volume_score': volume_score,
        'signals': signals, 'actual_outcome': actual_outcome, 'actual_move_pct': actual_move_pct
    }

def run_walk_forward_backtest(data, tops, bottoms):
    """Walk-Forward: 5-year train, 1-year test"""
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
            pred = generate_prediction_v9(data, current, tops, bottoms)
            if pred:
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
    
    return {
        'total': len(valid), 'accuracy': correct / len(valid) * 100,
        'high_conf': len(high_conf), 'high_conf_acc': hc_correct / len(high_conf) * 100 if high_conf else 0,
        'major_drops': len(major_drops), 'md_pred': len(md_pred), 'md_recall': len(md_pred)/len(major_drops)*100 if major_drops else 0,
        'major_rallies': len(major_rallies), 'mr_pred': len(mr_pred), 'mr_recall': len(mr_pred)/len(major_rallies)*100 if major_rallies else 0,
        'bullish': bullish, 'bearish': bearish, 'bias': bearish/(bullish+bearish)*100 if (bullish+bearish) > 0 else 0,
        'conf_calibration': conf_calibration
    }

def save_status(accuracy, current, version='v9'):
    status = {'timestamp': datetime.now(timezone.utc).isoformat(), 'model': version, 'accuracy': accuracy, 'current': current, 'status': 'complete'}
    with open('/root/.openclaw/workspace/hsi_status.json', 'w') as f:
        json.dump(status, f, indent=2, default=str)

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    print(f"Loaded {len(data)} points")
    
    print("Finding major extremes...")
    tops, bottoms = find_major_extremes(data)
    print(f"{len(tops)} tops, {len(bottoms)} bottoms")
    
    print("\n" + "="*80)
    print("HSI v9 - TREND-FOLLOWING WITH GANN CONFIRMATION")
    print("="*80)
    
    print("\nRunning Walk-Forward Backtest...")
    results, cycle_results = run_walk_forward_backtest(data, tops, bottoms)
    
    print("\n--- Walk-Forward Cycle Results ---")
    for cycle in cycle_results:
        status = "✅" if cycle['accuracy'] >= 55 else "⚠️"
        print(f"{cycle['test_period']}: {cycle['accuracy']:.1f}% acc, {cycle['predictions']} preds {status}")
    
    accuracy = calc_accuracy(results)
    current = generate_prediction_v9(data, datetime(2026,2,20), tops, bottoms)
    
    print("\n" + "="*80)
    print("AGGREGATE WFO RESULTS")
    print("="*80)
    print(f"\nTotal Predictions: {accuracy.get('total', 0)}")
    acc = accuracy.get('accuracy', 0)
    status = "✅ TARGET MET!" if acc >= 55 else "⚠️ Below target (55%)"
    print(f"Overall Accuracy: {acc:.1f}% {status}")
    print(f"High Conf (70%+): {accuracy.get('high_conf', 0)} predictions, {accuracy.get('high_conf_acc', 0):.1f}% accuracy")
    print(f"Major Drops: {accuracy.get('md_pred', 0)}/{accuracy.get('major_drops', 0)} ({accuracy.get('md_recall', 0):.1f}% recall)")
    print(f"Major Rallies: {accuracy.get('mr_pred', 0)}/{accuracy.get('major_rallies', 0)} ({accuracy.get('mr_recall', 0):.1f}% recall)")
    print(f"Bullish: {accuracy.get('bullish', 0)}, Bearish: {accuracy.get('bearish', 0)}, Bias: {accuracy.get('bias', 0):.1f}% bearish")
    
    if accuracy.get('conf_calibration'):
        print("\nConfidence Calibration:")
        for bin_range, bin_acc in sorted(accuracy['conf_calibration'].items()):
            print(f"  {bin_range}% confidence → {bin_acc:.1f}% actual accuracy")
    
    if current:
        print(f"\n" + "="*80)
        print(f"CURRENT ANALYSIS (Feb 20, 2026)")
        print("="*80)
        print(f"  Prediction: {current['prediction']}")
        print(f"  Confidence: {current['confidence']:.0f}%")
        print(f"  Risk Score: {current['risk_score']:.0f}/100")
        print(f"  Expected Move (90d): {current['expected_move']:+.1f}%")
        print(f"\n  Component Scores:")
        print(f"    Trend: {current['trend_score']:+.3f}")
        print(f"    Momentum: {current['momentum_score']:+.3f}")
        print(f"    Volume: {current['volume_score']:+.3f}")
        
        if current['signals']:
            print(f"\n  Signals ({len(current['signals'])}):")
            for s in current['signals'][:7]:
                print(f"    [{s['direction']}] {s['details']} (w={s['weight']:.2f})")
    
    save_status(accuracy, current)
    
    with open('/root/.openclaw/workspace/hsi_backtest_v9_results.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Date','Price','Pred','Conf','Risk','Actual','Outcome'])
        for r in results:
            w.writerow([r['date'].strftime('%Y-%m-%d'), f"{r['price']:.2f}", r['prediction'], f"{r['confidence']:.1f}", f"{r['risk_score']:.1f}", f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '', r['actual_outcome'] or ''])
    
    with open('/root/.openclaw/workspace/hsi_v9_wfo_summary.json', 'w') as f:
        json.dump({'cycles': cycle_results, 'aggregate': accuracy}, f, indent=2, default=str)
    
    print("\n[OK] v9 complete")

if __name__ == '__main__':
    main()
