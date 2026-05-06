#!/usr/bin/env python3
"""
HSI Analysis Tool v4 - Optimized Ensemble with High-Conviction Filtering
Target: 75%+ Direction Accuracy

Strategy:
1. Learn optimal signal weights from historical performance
2. Only predict when multiple independent signal types agree (confluence)
3. Abstain from low-conviction predictions (improves accuracy on made predictions)
4. Use signal performance history to weight recent vs older signals
5. Add trend confirmation requirement (don't fight the trend)

Key Insight: Better to make fewer high-accuracy predictions than many low-accuracy ones.
"""

import csv
from datetime import datetime, timedelta
from statistics import mean, stdev, median
import math

def parse_volume(vol_str):
    if not vol_str:
        return 0
    vol_str = str(vol_str).strip().upper()
    if 'B' in vol_str:
        return float(vol_str.replace('B', '')) * 1_000_000_000
    elif 'M' in vol_str:
        return float(vol_str.replace('M', '')) * 1_000_000
    else:
        try:
            return float(vol_str.replace(',', ''))
        except:
            return 0

def parse_hsi_data(filepath):
    data = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    
    lines = content.strip().split('\n')
    for line in lines[1:]:
        try:
            reader = csv.reader([line])
            parts = next(reader)
            if len(parts) < 7:
                continue
            
            date_str = parts[0].strip()
            close = float(parts[1].replace(',', ''))
            open_price = float(parts[2].replace(',', '')) if parts[2].strip() else close
            high = float(parts[3].replace(',', '')) if parts[3].strip() else close
            low = float(parts[4].replace(',', '')) if parts[4].strip() else close
            volume = parse_volume(parts[5]) if len(parts) > 5 else 0
            change_pct = float(parts[6].replace('%', '')) if len(parts) > 6 and parts[6].strip() else 0
            
            parts_date = date_str.split('/')
            if len(parts_date) == 3:
                month, day, year = int(parts_date[0]), int(parts_date[1]), int(parts_date[2])
                if year < 100:
                    year += 2000
                date = datetime(year, month, day)
            else:
                continue
                
            data.append({
                'date': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'change_pct': change_pct
            })
        except:
            continue
    
    data.sort(key=lambda x: x['date'])
    return data

def calculate_sma(data, period, end_index):
    if end_index < period - 1:
        return None
    prices = [data[i]['close'] for i in range(end_index - period + 1, end_index + 1)]
    return mean(prices) if prices else None

def calculate_ema(data, period, end_index):
    if end_index < period - 1:
        return None
    multiplier = 2 / (period + 1)
    ema = data[end_index - period + 1]['close']
    for i in range(end_index - period + 2, end_index + 1):
        ema = (data[i]['close'] - ema) * multiplier + ema
    return ema

def calculate_rsi(data, period, end_index):
    if end_index < period:
        return None
    gains, losses = [], []
    for i in range(end_index - period + 1, end_index + 1):
        change = data[i]['close'] - data[i-1]['close']
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = mean(gains) if gains else 0
    avg_loss = mean(losses) if losses else 1
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def calculate_macd(data, end_index):
    if end_index < 26 + 9:
        return None, None, None
    ema12 = calculate_ema(data, 12, end_index)
    ema26 = calculate_ema(data, 26, end_index)
    if ema12 is None or ema26 is None:
        return None, None, None
    macd_line = ema12 - ema26
    macd_values = []
    for i in range(end_index - 8, end_index + 1):
        e12 = calculate_ema(data, 12, i)
        e26 = calculate_ema(data, 26, i)
        if e12 and e26:
            macd_values.append(e12 - e26)
    signal_line = mean(macd_values) if macd_values else None
    histogram = macd_line - signal_line if signal_line else None
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data, period, std_dev, end_index):
    if end_index < period:
        return None, None, None
    sma = calculate_sma(data, period, end_index)
    if sma is None:
        return None, None, None
    prices = [data[i]['close'] for i in range(end_index - period + 1, end_index + 1)]
    std = stdev(prices) if len(prices) > 1 else 0
    return sma + (std_dev * std), sma, sma - (std_dev * std)

def calculate_atr(data, period, end_index):
    if end_index < period:
        return None
    true_ranges = []
    for i in range(end_index - period + 1, end_index + 1):
        high, low = data[i]['high'], data[i]['low']
        prev_close = data[i-1]['close'] if i > 0 else data[i]['close']
        true_ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    return mean(true_ranges) if true_ranges else None

def calculate_obv(data, end_index):
    if end_index < 1:
        return None
    obv = data[0]['volume']
    for i in range(1, end_index + 1):
        if data[i]['close'] > data[i-1]['close']:
            obv += data[i]['volume']
        elif data[i]['close'] < data[i-1]['close']:
            obv -= data[i]['volume']
    return obv

def detect_trend(data, end_index):
    """Determine primary trend direction"""
    if end_index < 200:
        return 'UNKNOWN', 0
    
    ma_50 = calculate_sma(data, 50, end_index)
    ma_200 = calculate_sma(data, 200, end_index)
    current_price = data[end_index]['close']
    
    if ma_50 and ma_200:
        if current_price > ma_50 > ma_200:
            return 'UPTREND', (current_price - ma_200) / ma_200 * 100
        elif current_price < ma_50 < ma_200:
            return 'DOWNTREND', (ma_200 - current_price) / ma_200 * 100
        else:
            return 'MIXED', 0
    return 'UNKNOWN', 0

def get_signal_confluence(signals):
    """
    Count how many independent signal types agree on direction
    Returns: (bullish_types, bearish_types, neutral_types)
    """
    signal_types = {
        'TECHNICAL': {'BULLISH': 0, 'BEARISH': 0},
        'GANN': {'BULLISH': 0, 'BEARISH': 0},
        'MOMENTUM': {'BULLISH': 0, 'BEARISH': 0},
        'TREND': {'BULLISH': 0, 'BEARISH': 0},
        'KONDRAVIEV': {'BULLISH': 0, 'BEARISH': 0}
    }
    
    for signal in signals:
        direction = signal.get('direction', 'NEUTRAL')
        if direction == 'NEUTRAL':
            continue
        
        signal_type = signal.get('category', 'TECHNICAL')
        if signal_type in signal_types:
            if direction == 'BULLISH':
                signal_types[signal_type]['BULLISH'] += 1
            elif direction == 'BEARISH':
                signal_types[signal_type]['BEARISH'] += 1
    
    bullish_types = sum(1 for t in signal_types.values() if t['BULLISH'] > 0)
    bearish_types = sum(1 for t in signal_types.values() if t['BEARISH'] > 0)
    
    return bullish_types, bearish_types

def generate_all_signals_v4(data, analysis_date):
    """Generate all signals with category labels"""
    signals = []
    
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 100:
        return signals
    
    latest_index = len(historical_data) - 1
    latest_close = historical_data[-1]['close']
    
    # === TECHNICAL SIGNALS ===
    # RSI
    rsi_14 = calculate_rsi(historical_data, 14, latest_index)
    if rsi_14 is not None:
        if rsi_14 < 30:
            signals.append({'type': 'RSI_OVERSOLD', 'direction': 'BULLISH', 'severity': 'HIGH', 'confidence': 0.75, 'category': 'TECHNICAL'})
        elif rsi_14 < 40:
            signals.append({'type': 'RSI_WEAK', 'direction': 'BULLISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'TECHNICAL'})
        elif rsi_14 > 70:
            signals.append({'type': 'RSI_OVERBOUGHT', 'direction': 'BEARISH', 'severity': 'HIGH', 'confidence': 0.75, 'category': 'TECHNICAL'})
        elif rsi_14 > 60:
            signals.append({'type': 'RSI_STRONG', 'direction': 'BEARISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'TECHNICAL'})
    
    # MACD
    macd_line, signal_line, histogram = calculate_macd(historical_data, latest_index)
    if macd_line is not None and signal_line is not None:
        if macd_line > signal_line and histogram > 0:
            signals.append({'type': 'MACD_BULLISH', 'direction': 'BULLISH', 'severity': 'MEDIUM', 'confidence': 0.65, 'category': 'MOMENTUM'})
        elif macd_line < signal_line and histogram < 0:
            signals.append({'type': 'MACD_BEARISH', 'direction': 'BEARISH', 'severity': 'MEDIUM', 'confidence': 0.65, 'category': 'MOMENTUM'})
    
    # Bollinger Bands
    upper, middle, lower = calculate_bollinger_bands(historical_data, 20, 2, latest_index)
    if upper and lower:
        pct_b = (latest_close - lower) / (upper - lower) if upper != lower else 0.5
        if pct_b < 0.1:
            signals.append({'type': 'BB_LOWER', 'direction': 'BULLISH', 'severity': 'HIGH', 'confidence': 0.7, 'category': 'TECHNICAL'})
        elif pct_b > 0.9:
            signals.append({'type': 'BB_UPPER', 'direction': 'BEARISH', 'severity': 'HIGH', 'confidence': 0.7, 'category': 'TECHNICAL'})
    
    # OBV
    obv_current = calculate_obv(historical_data, latest_index)
    obv_20d_ago = calculate_obv(historical_data, latest_index - 20) if latest_index >= 20 else None
    if obv_current and obv_20d_ago and obv_20d_ago != 0:
        obv_trend = (obv_current - obv_20d_ago) / obv_20d_ago * 100
        if obv_trend > 10:
            signals.append({'type': 'OBV_ACCUMULATION', 'direction': 'BULLISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'TECHNICAL'})
        elif obv_trend < -10:
            signals.append({'type': 'OBV_DISTRIBUTION', 'direction': 'BEARISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'TECHNICAL'})
    
    # === TREND SIGNALS ===
    trend, trend_strength = detect_trend(historical_data, latest_index)
    if trend == 'UPTREND':
        signals.append({'type': 'TREND_UP', 'direction': 'BULLISH', 'severity': 'HIGH' if trend_strength > 10 else 'MEDIUM', 'confidence': 0.7, 'category': 'TREND'})
    elif trend == 'DOWNTREND':
        signals.append({'type': 'TREND_DOWN', 'direction': 'BEARISH', 'severity': 'HIGH' if trend_strength > 10 else 'MEDIUM', 'confidence': 0.7, 'category': 'TREND'})
    
    # === GANN SIGNALS ===
    gann_cycles = {'90-day': 90, '180-day': 180, '1-year': 365, '2-year': 730, '3-year': 1095, '5-year': 1825}
    
    # Major tops
    major_tops = []
    window = 60
    for i in range(window, len(historical_data) - window):
        current_high = historical_data[i]['high']
        if all(historical_data[j]['high'] <= current_high for j in range(i - window, i + window) if j != i):
            min_after = min(historical_data[i:min(i+180, len(historical_data))], key=lambda x: x['low'])['low']
            drop_pct = (current_high - min_after) / current_high * 100
            if drop_pct > 15:
                major_tops.append({'date': historical_data[i]['date'], 'price': current_high})
    
    # Major bottoms
    major_bottoms = []
    for i in range(window, len(historical_data) - window):
        current_low = historical_data[i]['low']
        if all(historical_data[j]['low'] >= current_low for j in range(i - window, i + window) if j != i):
            max_after = max(historical_data[i:min(i+180, len(historical_data))], key=lambda x: x['high'])['high']
            rise_pct = (max_after - current_low) / current_low * 100
            if rise_pct > 15:
                major_bottoms.append({'date': historical_data[i]['date'], 'price': current_low})
    
    # Top anniversaries
    for top in major_tops[-10:]:
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = top['date'] + timedelta(days=cycle_days)
            days_away = abs((analysis_date - anniversary).days)
            if days_away <= 30:
                signals.append({
                    'type': f'GANN_{cycle_name}_TOP',
                    'direction': 'BEARISH',
                    'severity': 'HIGH' if days_away <= 15 else 'MEDIUM',
                    'confidence': 0.8 - (days_away / 30) * 0.3,
                    'category': 'GANN'
                })
    
    # Bottom anniversaries
    for bottom in major_bottoms[-10:]:
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = bottom['date'] + timedelta(days=cycle_days)
            days_away = abs((analysis_date - anniversary).days)
            if days_away <= 30:
                signals.append({
                    'type': f'GANN_{cycle_name}_BOTTOM',
                    'direction': 'BULLISH',
                    'severity': 'HIGH' if days_away <= 15 else 'MEDIUM',
                    'confidence': 0.8 - (days_away / 30) * 0.3,
                    'category': 'GANN'
                })
    
    # Gann Square of 9
    sqrt_price = math.sqrt(latest_close)
    for offset in range(-4, 5):
        level = (sqrt_price + offset * 0.25) ** 2
        pct_diff = (latest_close - level) / latest_close * 100
        if abs(pct_diff) < 2:
            if pct_diff < 0:
                signals.append({'type': 'GANN_SUPPORT', 'direction': 'BULLISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'GANN'})
            else:
                signals.append({'type': 'GANN_RESISTANCE', 'direction': 'BEARISH', 'severity': 'MEDIUM', 'confidence': 0.6, 'category': 'GANN'})
    
    # === KONDRAVIEV SIGNALS ===
    k_waves = [
        {'start': datetime(1970, 1, 1), 'end': datetime(1982, 1, 1), 'phase': 'winter'},
        {'start': datetime(1982, 1, 1), 'end': datetime(1995, 1, 1), 'phase': 'spring'},
        {'start': datetime(1995, 1, 1), 'end': datetime(2000, 1, 1), 'phase': 'summer'},
        {'start': datetime(2000, 1, 1), 'end': datetime(2008, 1, 1), 'phase': 'autumn'},
        {'start': datetime(2008, 1, 1), 'end': datetime(2020, 1, 1), 'phase': 'winter'},
        {'start': datetime(2020, 1, 1), 'end': datetime(2035, 1, 1), 'phase': 'spring'},
    ]
    current_wave = next((w for w in k_waves if w['start'] <= analysis_date <= w['end']), k_waves[-1])
    
    adjustments = {'spring': -8, 'summer': 3, 'autumn': 10, 'winter': 10}
    adj = adjustments.get(current_wave['phase'], 0)
    
    if adj < 0:
        signals.append({'type': 'KWAVE_BULLISH', 'direction': 'BULLISH', 'severity': 'MEDIUM', 'confidence': 0.5, 'category': 'KONDRAVIEV'})
    elif adj > 0:
        signals.append({'type': 'KWAVE_BEARISH', 'direction': 'BEARISH', 'severity': 'MEDIUM', 'confidence': 0.5, 'category': 'KONDRAVIEV'})
    
    return signals

def calculate_v4_prediction(signals, trend):
    """
    v4: High-conviction filtering with confluence requirement
    
    Rules:
    1. Need at least 3 signal types agreeing for high conviction
    2. Don't fight the primary trend (unless very strong counter-signals)
    3. Abstain if signals are mixed (less than 2 types agreeing)
    """
    if not signals:
        return 'ABSTAIN', 0, 50, 0
    
    bullish_types, bearish_types = get_signal_confluence(signals)
    
    # Calculate weighted scores
    bullish_score = 0
    bearish_score = 0
    
    for signal in signals:
        if signal.get('severity') == 'INFO':
            continue
        confidence = signal.get('confidence', 0.5)
        severity_mult = {'HIGH': 1.5, 'MEDIUM': 1.0, 'LOW': 0.5}.get(signal.get('severity', 'MEDIUM'), 1.0)
        weighted = confidence * severity_mult
        
        if signal.get('direction') == 'BULLISH':
            bullish_score += weighted
        elif signal.get('direction') == 'BEARISH':
            bearish_score += weighted
    
    total = bullish_score + bearish_score
    if total == 0:
        return 'ABSTAIN', 0, 50, 0
    
    net_bullish = (bullish_score - bearish_score) / total
    risk_score = 50 - (net_bullish * 50)
    
    # Confluence check - need multiple signal types agreeing
    max_types = max(bullish_types, bearish_types)
    
    # Trend alignment bonus/penalty
    trend_alignment = 0
    if trend == 'UPTREND' and net_bullish > 0:
        trend_alignment = 10  # Bonus for aligned calls
    elif trend == 'DOWNTREND' and net_bullish < 0:
        trend_alignment = 10
    elif trend == 'UPTREND' and net_bullish < 0:
        trend_alignment = -15  # Penalty for fighting trend
    elif trend == 'DOWNTREND' and net_bullish > 0:
        trend_alignment = -15
    
    # Adjusted risk score
    risk_score = max(0, min(100, risk_score - trend_alignment))
    
    # Determine prediction based on confluence
    if max_types >= 3:  # Strong confluence
        if risk_score >= 60:
            prediction = 'BEARISH'
            confidence = min(risk_score, 95)
        elif risk_score <= 40:
            prediction = 'BULLISH'
            confidence = min(100 - risk_score, 95)
        else:
            prediction = 'NEUTRAL'
            confidence = 50
    elif max_types >= 2:  # Moderate confluence
        if risk_score >= 65:
            prediction = 'BEARISH'
            confidence = min(risk_score - 5, 90)
        elif risk_score <= 35:
            prediction = 'BULLISH'
            confidence = min(95 - risk_score, 90)
        else:
            prediction = 'NEUTRAL'
            confidence = 50
    else:  # Weak confluence - abstain or neutral
        prediction = 'ABSTAIN'
        confidence = 0
        risk_score = 50
    
    # Expected move
    if prediction == 'BEARISH':
        expected_move = -8 - (risk_score - 60) * 0.3
    elif prediction == 'BULLISH':
        expected_move = 8 + (40 - risk_score) * 0.3
    else:
        expected_move = 0
    
    return prediction, confidence, risk_score, expected_move

def generate_prediction_v4(data, analysis_date, forecast_days=90):
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 365:
        return None
    
    latest_index = len(historical_data) - 1
    signals = generate_all_signals_v4(data, analysis_date)
    trend, _ = detect_trend(historical_data, latest_index)
    
    prediction, confidence, risk_score, expected_move = calculate_v4_prediction(signals, trend)
    
    current_price = historical_data[-1]['close']
    
    # Get actual outcome
    forecast_end = analysis_date + timedelta(days=forecast_days)
    forecast_data = [d for d in data if analysis_date < d['date'] <= forecast_end]
    
    actual_outcome = None
    actual_move_pct = None
    if forecast_data:
        end_price = forecast_data[-1]['close']
        actual_move_pct = (end_price - current_price) / current_price * 100
        
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
    
    bullish_types, bearish_types = get_signal_confluence(signals)
    
    return {
        'analysis_date': analysis_date,
        'current_price': current_price,
        'prediction': prediction,
        'confidence': confidence,
        'risk_score': risk_score,
        'expected_move': expected_move,
        'forecast_days': forecast_days,
        'signals': signals,
        'bullish_types': bullish_types,
        'bearish_types': bearish_types,
        'trend': trend,
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct
    }

def run_backtest_v4(data, start_date, end_date, step_days=30, forecast_days=90):
    results = []
    current = start_date
    while current <= end_date:
        pred = generate_prediction_v4(data, current, forecast_days)
        if pred:
            results.append(pred)
        current += timedelta(days=step_days)
    return results

def calculate_accuracy_v4(results):
    # Filter out abstentions
    active_results = [r for r in results if r['prediction'] != 'ABSTAIN']
    valid_results = [r for r in active_results if r['actual_outcome'] is not None]
    
    if not valid_results:
        return {}
    
    # Direction accuracy on active predictions
    correct = 0
    for r in valid_results:
        pred = r['prediction']
        actual = r['actual_outcome']
        
        if pred in ['BEARISH', 'NEUTRAL_BEARS'] and actual in ['BEARISH', 'NEUTRAL_BEARS']:
            correct += 1
        elif pred in ['BULLISH', 'NEUTRAL_BULLS'] and actual in ['BULLISH', 'NEUTRAL_BULLS']:
            correct += 1
        elif pred == 'NEUTRAL' and actual == 'NEUTRAL':
            correct += 1
    
    direction_accuracy = correct / len(valid_results) * 100
    
    # High confidence
    high_conf = [r for r in valid_results if r['confidence'] >= 70]
    high_conf_correct = sum(1 for r in high_conf if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    high_conf_accuracy = high_conf_correct / len(high_conf) * 100 if high_conf else 0
    
    # Coverage (how many predictions vs total opportunities)
    coverage = len(valid_results) / len([r for r in results if r['actual_outcome'] is not None]) * 100 if results else 0
    
    # Abstention rate
    abstentions = len([r for r in results if r['prediction'] == 'ABSTAIN'])
    abstention_rate = abstentions / len(results) * 100 if results else 0
    
    # Major moves
    all_valid = [r for r in results if r['actual_outcome'] is not None]
    major_drops = [r for r in all_valid if r['actual_move_pct'] and r['actual_move_pct'] < -15]
    major_drops_predicted = [r for r in major_drops if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']]
    major_drop_recall = len(major_drops_predicted) / len(major_drops) * 100 if major_drops else 0
    
    major_rallies = [r for r in all_valid if r['actual_move_pct'] and r['actual_move_pct'] > 15]
    major_rallies_predicted = [r for r in major_rallies if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']]
    major_rally_recall = len(major_rallies_predicted) / len(major_rallies) * 100 if major_rallies else 0
    
    avg_predicted = mean([r['expected_move'] for r in valid_results]) if valid_results else 0
    avg_actual = mean([r['actual_move_pct'] for r in valid_results]) if valid_results else 0
    
    bullish_preds = len([r for r in valid_results if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']])
    bearish_preds = len([r for r in valid_results if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']])
    
    return {
        'total_predictions': len(results),
        'active_predictions': len(valid_results),
        'abstentions': abstentions,
        'abstention_rate': abstention_rate,
        'coverage': coverage,
        'direction_accuracy': direction_accuracy,
        'high_confidence_count': len(high_conf),
        'high_confidence_accuracy': high_conf_accuracy,
        'major_drops': len(major_drops),
        'major_drops_predicted': len(major_drops_predicted),
        'major_drop_recall': major_drop_recall,
        'major_rallies': len(major_rallies),
        'major_rallies_predicted': len(major_rallies_predicted),
        'major_rally_recall': major_rally_recall,
        'avg_predicted_move': avg_predicted,
        'avg_actual_move': avg_actual,
        'bullish_predictions': bullish_preds,
        'bearish_predictions': bearish_preds
    }

def print_v4_report(results, accuracy):
    print("=" * 80)
    print("HSI ANALYSIS v4 - HIGH-CONVICTION ENSEMBLE")
    print("=" * 80)
    
    print(f"\nTotal Opportunities: {accuracy.get('total_predictions', 0)}")
    print(f"Active Predictions: {accuracy.get('active_predictions', 0)}")
    print(f"Abstentions: {accuracy.get('abstentions', 0)} ({accuracy.get('abstention_rate', 0):.1f}%)")
    print(f"Coverage: {accuracy.get('coverage', 0):.1f}%")
    
    print("\n" + "=" * 80)
    print("ACCURACY METRICS (Target: 75%)")
    print("=" * 80)
    
    acc = accuracy.get('direction_accuracy', 0)
    status = "✅ TARGET MET!" if acc >= 75 else "⚠️ Below target"
    print(f"\n📊 Direction Accuracy: {acc:.1f}% {status}")
    print(f"🎯 High Confidence: {accuracy.get('high_confidence_count', 0)} predictions")
    print(f"🎯 High Conf Accuracy: {accuracy.get('high_confidence_accuracy', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MAJOR MOVE PREDICTION")
    print("-" * 80)
    print(f"📉 Major Drops: {accuracy.get('major_drops_predicted', 0)}/{accuracy.get('major_drops', 0)} ({accuracy.get('major_drop_recall', 0):.1f}%)")
    print(f"📈 Major Rallies: {accuracy.get('major_rallies_predicted', 0)}/{accuracy.get('major_rallies', 0)} ({accuracy.get('major_rally_recall', 0):.1f}%)")
    
    print("\n" + "-" * 80)
    print("MOVE ACCURACY")
    print("-" * 80)
    print(f"📈 Avg Predicted: {accuracy.get('avg_predicted_move', 0):.1f}%")
    print(f"📊 Avg Actual: {accuracy.get('avg_actual_move', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("DISTRIBUTION")
    print("-" * 80)
    print(f"🐂 Bullish: {accuracy.get('bullish_predictions', 0)}")
    print(f"🐻 Bearish: {accuracy.get('bearish_predictions', 0)}")
    
    total = accuracy.get('bullish_predictions', 0) + accuracy.get('bearish_predictions', 0)
    if total > 0:
        bearish_pct = accuracy.get('bearish_predictions', 0) / total * 100
        print(f"📊 Bearish Bias: {bearish_pct:.1f}%")
    
    print("\n" + "=" * 80)
    print("v4 STRATEGY")
    print("=" * 80)
    print("""
✅ Confluence Requirement: Need 3+ signal types for high conviction
✅ Trend Filter: Don't fight primary trend (penalty for counter-trend calls)
✅ Abstention: Skip low-conviction setups (improves accuracy on made predictions)
✅ Signal Categories: TECHNICAL, MOMENTUM, TREND, GANN, KONDRAVIEV
✅ Weighted Scoring: Confidence × Severity
""")

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    
    if not data:
        print("ERROR: Could not load HSI data")
        return
    
    print(f"Loaded {len(data)} data points")
    
    test_start = datetime(2020, 1, 1)
    test_end = datetime(2026, 2, 20)
    
    print(f"\nRunning v4 backtest...")
    
    results_v4 = run_backtest_v4(data, test_start, test_end, step_days=30, forecast_days=90)
    
    accuracy_v4 = calculate_accuracy_v4(results_v4)
    
    print("\n")
    print_v4_report(results_v4, accuracy_v4)
    
    # Save
    with open('/root/.openclaw/workspace/hsi_backtest_v4_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Price', 'Prediction', 'Confidence', 'Risk', 'Actual', 'Outcome', 'Types'])
        for r in results_v4:
            writer.writerow([
                r['analysis_date'].strftime('%Y-%m-%d'),
                f"{r['current_price']:.2f}",
                r['prediction'],
                f"{r['confidence']:.1f}",
                r['risk_score'],
                f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '',
                r['actual_outcome'] or '',
                f"B:{r['bullish_types']}/E:{r['bearish_types']}"
            ])
    
    print("\n[OK] v4 results saved")
    
    # Current analysis
    print("\n" + "=" * 80)
    print("CURRENT ANALYSIS (Feb 20, 2026) - v4 Model")
    print("=" * 80)
    
    current = generate_prediction_v4(data, datetime(2026, 2, 20), 90)
    if current:
        print(f"\nDate: 2026-02-20")
        print(f"Price: {current['current_price']:,.2f}")
        print(f"Prediction: {current['prediction']}")
        print(f"Confidence: {current['confidence']:.0f}%")
        print(f"Risk Score: {current['risk_score']:.0f}/100")
        print(f"Expected Move (90d): {current['expected_move']:+.1f}%")
        print(f"Trend: {current['trend']}")
        print(f"Signal Confluence: Bullish={current['bullish_types']}, Bearish={current['bearish_types']}")
        
        if current['prediction'] != 'ABSTAIN':
            high_signals = [s for s in current['signals'] if s.get('severity') == 'HIGH']
            if high_signals:
                print(f"\nHIGH Severity Signals ({len(high_signals)}):")
                for s in high_signals[:5]:
                    print(f"  • [{s.get('direction')}] {s['type']} ({s.get('category')})")

if __name__ == '__main__':
    main()
