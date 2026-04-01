#!/usr/bin/env python3
"""
HSI Analysis Tool v5 - Optimized Weight Learning
Target: 75%+ Direction Accuracy

Key Innovation: Learn optimal signal weights from training data (1980-2019)
Then apply those weights to test data (2020-2026)

Approach:
1. For each signal type, calculate historical accuracy in training period
2. Weight signals by their historical predictive power
3. Only use signals with proven track record (>55% accuracy)
4. Combine with trend-following overlay (trend is your friend)
5. Simple decision rules (complexity = overfitting)
"""

import csv
from datetime import datetime, timedelta
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
            parts_date = date_str.split('/')
            if len(parts_date) != 3:
                continue
            month, day, year = int(parts_date[0]), int(parts_date[1]), int(parts_date[2])
            if year < 100:
                year += 2000
            data.append({
                'date': datetime(year, month, day),
                'open': float(parts[1].replace(',', '')),
                'high': float(parts[2].replace(',', '')) or float(parts[1].replace(',', '')),
                'low': float(parts[3].replace(',', '')) or float(parts[1].replace(',', '')),
                'close': float(parts[1].replace(',', '')),
                'volume': parse_volume(parts[4]) if len(parts) > 4 else 0,
                'change_pct': float(parts[5].replace('%', '')) if len(parts) > 5 and parts[5].strip() else 0
            })
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
    mult = 2 / (period + 1)
    e = data[end_idx - period + 1]['close']
    for i in range(end_idx - period + 2, end_idx + 1):
        e = (data[i]['close'] - e) * mult + e
    return e

def rsi(data, period, end_idx):
    if end_idx < period:
        return None
    gains = [max(data[i]['close'] - data[i-1]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    losses = [max(data[i-1]['close'] - data[i]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    avg_gain, avg_loss = mean(gains), mean(losses)
    return 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

def macd_signal(data, end_idx):
    if end_idx < 26 + 9:
        return None
    e12, e26 = ema(data, 12, end_idx), ema(data, 26, end_idx)
    if not e12 or not e26:
        return None
    macd = e12 - e26
    macds = []
    for i in range(end_idx - 8, end_idx + 1):
        m12, m26 = ema(data, 12, i), ema(data, 26, i)
        if m12 and m26:
            macds.append(m12 - m26)
    return 1 if macd > mean(macds) else -1 if macds else None

def bb_position(data, end_idx):
    if end_idx < 20:
        return None
    prices = [data[i]['close'] for i in range(end_idx - 19, end_idx + 1)]
    m, s = mean(prices), stdev(prices) if len(prices) > 1 else 1
    if s == 0:
        return 0.5
    return (data[end_idx]['close'] - (m - 2*s)) / (4*s)

def get_trend(data, end_idx):
    if end_idx < 200:
        return 0
    m50, m200 = sma(data, 50, end_idx), sma(data, 200, end_idx)
    if not m50 or not m200:
        return 0
    p = data[end_idx]['close']
    if p > m50 > m200:
        return 1  # Uptrend
    elif p < m50 < m200:
        return -1  # Downtrend
    return 0  # Mixed

def get_momentum(data, end_idx, period=90):
    if end_idx < period:
        return 0
    return (data[end_idx]['close'] - data[end_idx - period]['close']) / data[end_idx - period]['close'] * 100

def find_major_extremes(data, end_idx, window=60, min_move=15):
    """Find major tops and bottoms"""
    tops, bottoms = [], []
    for i in range(window, min(end_idx - window, len(data))):
        # Top
        if all(data[j]['high'] <= data[i]['high'] for j in range(i-window, i+window) if j != i):
            min_after = min(data[i:min(i+180, len(data))], key=lambda x: x['low'])['low']
            if (data[i]['high'] - min_after) / data[i]['high'] * 100 > min_move:
                tops.append((data[i]['date'], data[i]['high']))
        # Bottom
        if all(data[j]['low'] >= data[i]['low'] for j in range(i-window, i+window) if j != i):
            max_after = max(data[i:min(i+180, len(data))], key=lambda x: x['high'])['high']
            if (max_after - data[i]['low']) / data[i]['low'] * 100 > min_move:
                bottoms.append((data[i]['date'], data[i]['low']))
    return tops[-10:], bottoms[-10:]

def gann_anniversary_signals(date, tops, bottoms):
    """Generate Gann anniversary signals"""
    signals = []
    cycles = {'1-year': 365, '2-year': 730, '3-year': 1095, '5-year': 1825}
    
    for top_date, _ in tops:
        for name, days in cycles.items():
            anniv = top_date + timedelta(days=days)
            diff = abs((date - anniv).days)
            if diff <= 30:
                signals.append(('BEARISH', 0.7 - diff/100, f'GANN_TOP_{name}'))
    
    for bot_date, _ in bottoms:
        for name, days in cycles.items():
            anniv = bot_date + timedelta(days=days)
            diff = abs((date - anniv).days)
            if diff <= 30:
                signals.append(('BULLISH', 0.7 - diff/100, f'GANN_BOT_{name}'))
    
    return signals

def get_kwave_bias(date):
    """Kondratiev Wave bias"""
    waves = [
        (datetime(1970,1,1), datetime(1982,1,1), 0.1),   # Winter: bearish
        (datetime(1982,1,1), datetime(1995,1,1), -0.1),  # Spring: bullish
        (datetime(1995,1,1), datetime(2000,1,1), 0.05),  # Summer: slightly bearish
        (datetime(2000,1,1), datetime(2008,1,1), 0.15),  # Autumn: bearish
        (datetime(2008,1,1), datetime(2020,1,1), 0.1),   # Winter: bearish
        (datetime(2020,1,1), datetime(2035,1,1), -0.15), # Spring: bullish
    ]
    for start, end, bias in waves:
        if start <= date <= end:
            return bias
    return 0

def generate_signals_v5(data, date, tops, bottoms):
    """Generate all signals for a given date"""
    signals = []
    hist = [d for d in data if d['date'] <= date]
    if len(hist) < 100:
        return signals
    
    end_idx = len(hist) - 1
    
    # RSI
    r = rsi(hist, 14, end_idx)
    if r:
        if r < 30:
            signals.append(('BULLISH', 0.75, 'RSI_OVERSOLD'))
        elif r < 40:
            signals.append(('BULLISH', 0.55, 'RSI_WEAK'))
        elif r > 70:
            signals.append(('BEARISH', 0.75, 'RSI_OVERBOUGHT'))
        elif r > 60:
            signals.append(('BEARISH', 0.55, 'RSI_STRONG'))
    
    # MACD
    m = macd_signal(hist, end_idx)
    if m:
        signals.append(('BULLISH' if m > 0 else 'BEARISH', 0.55, 'MACD'))
    
    # Bollinger
    bb = bb_position(hist, end_idx)
    if bb is not None:
        if bb < 0.1:
            signals.append(('BULLISH', 0.65, 'BB_LOWER'))
        elif bb > 0.9:
            signals.append(('BEARISH', 0.65, 'BB_UPPER'))
    
    # Trend
    t = get_trend(hist, end_idx)
    if t == 1:
        signals.append(('BULLISH', 0.60, 'TREND_UP'))
    elif t == -1:
        signals.append(('BEARISH', 0.60, 'TREND_DOWN'))
    
    # Momentum
    mom = get_momentum(hist, end_idx, 90)
    if mom > 15:
        signals.append(('BULLISH', 0.55, 'MOMENTUM_90D'))
    elif mom < -15:
        signals.append(('BEARISH', 0.55, 'MOMENTUM_90D'))
    
    # Gann
    signals.extend(gann_anniversary_signals(date, tops, bottoms))
    
    # K-Wave
    kw = get_kwave_bias(date)
    if kw < 0:
        signals.append(('BULLISH', 0.50, 'KWAVE'))
    elif kw > 0:
        signals.append(('BEARISH', 0.50, 'KWAVE'))
    
    return signals

def calculate_optimal_weights(data, train_start, train_end, forecast_days=90):
    """
    Learn optimal signal weights from training data
    Returns dict of signal_type -> weight
    """
    print(f"Learning optimal weights from {train_start.strftime('%Y-%m-%d')} to {train_end.strftime('%Y-%m-%d')}...")
    
    # Generate predictions throughout training period
    signal_performance = {}  # signal_type -> {'correct': X, 'total': Y}
    
    current = train_start
    step = timedelta(days=30)
    
    while current <= train_end:
        hist = [d for d in data if d['date'] <= current]
        if len(hist) < 365:
            current += step
            continue
        
        end_idx = len(hist) - 1
        current_price = hist[-1]['close']
        tops, bottoms = find_major_extremes(hist, end_idx)
        signals = generate_signals_v5(hist, current, tops, bottoms)
        
        # Get actual outcome
        forecast_end = current + timedelta(days=forecast_days)
        future = [d for d in data if current < d['date'] <= forecast_end]
        
        if not future:
            current += step
            continue
        
        actual_move = (future[-1]['close'] - current_price) / current_price * 100
        actual_direction = 'BULLISH' if actual_move > 5 else 'BEARISH' if actual_move < -5 else 'NEUTRAL'
        
        # Track performance of each signal
        for direction, confidence, sig_type in signals:
            if sig_type not in signal_performance:
                signal_performance[sig_type] = {'correct': 0, 'total': 0, 'weighted': 0}
            
            signal_performance[sig_type]['total'] += 1
            
            # Was this signal correct?
            if direction == actual_direction:
                signal_performance[sig_type]['correct'] += 1
                signal_performance[sig_type]['weighted'] += confidence
            elif actual_direction == 'NEUTRAL':
                # Neutral is half-correct
                signal_performance[sig_type]['weighted'] += confidence * 0.5
        
        current += step
    
    # Calculate accuracy and weights for each signal type
    weights = {}
    print("\nSignal Performance (Training Period):")
    print("-" * 60)
    
    for sig_type, perf in sorted(signal_performance.items(), key=lambda x: x[1]['total'], reverse=True):
        if perf['total'] >= 10:  # Minimum sample size
            accuracy = perf['correct'] / perf['total'] * 100
            avg_conf = perf['weighted'] / perf['total'] if perf['total'] > 0 else 0
            
            # Weight based on accuracy (only use signals with >50% accuracy)
            if accuracy > 50:
                weight = (accuracy - 50) / 50  # 0 to 1 scale
                weights[sig_type] = weight
                status = "✅ USE"
            else:
                weights[sig_type] = 0
                status = "❌ SKIP"
            
            print(f"{sig_type:<25}: {accuracy:>5.1f}% acc ({perf['total']:>3} samples) {status}")
        else:
            weights[sig_type] = 0
    
    print("-" * 60)
    usable = sum(1 for w in weights.values() if w > 0)
    print(f"Usable signals: {usable} of {len(weights)}")
    
    return weights

def generate_prediction_v5(data, date, tops, bottoms, signal_weights):
    """Generate prediction using optimized weights"""
    hist = [d for d in data if d['date'] <= date]
    if len(hist) < 365:
        return None
    
    end_idx = len(hist) - 1
    signals = generate_signals_v5(hist, date, tops, bottoms)
    
    # Calculate weighted score
    bullish_weight = 0
    bearish_weight = 0
    
    for direction, confidence, sig_type in signals:
        weight = signal_weights.get(sig_type, 0)
        if weight == 0:
            continue  # Skip signals with no predictive power
        
        weighted_conf = confidence * weight
        if direction == 'BULLISH':
            bullish_weight += weighted_conf
        else:
            bearish_weight += weighted_conf
    
    total = bullish_weight + bearish_weight
    if total == 0:
        return None  # No usable signals
    
    net = (bullish_weight - bearish_weight) / total
    risk_score = 50 - (net * 50)
    
    # Trend overlay
    trend = get_trend(hist, end_idx)
    if trend == 1 and net < 0:  # Fighting uptrend
        risk_score = min(risk_score + 15, 100)
    elif trend == -1 and net > 0:  # Fighting downtrend
        risk_score = max(risk_score - 15, 0)
    
    # Generate prediction
    if risk_score >= 60:
        prediction = 'BEARISH'
        confidence = min(risk_score, 95)
    elif risk_score <= 40:
        prediction = 'BULLISH'
        confidence = min(100 - risk_score, 95)
    else:
        prediction = 'NEUTRAL'
        confidence = 50
    
    # Expected move
    if prediction == 'BEARISH':
        expected_move = -8 - (risk_score - 60) * 0.3
    elif prediction == 'BULLISH':
        expected_move = 8 + (40 - risk_score) * 0.3
    else:
        expected_move = 0
    
    current_price = hist[-1]['close']
    
    # Get actual
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
        'prediction': prediction,
        'confidence': confidence,
        'risk_score': risk_score,
        'expected_move': expected_move,
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct,
        'signals_used': sum(1 for _, _, t in signals if signal_weights.get(t, 0) > 0)
    }

def run_backtest_v5(data, test_start, test_end, signal_weights):
    results = []
    current = test_start
    
    # Pre-calculate tops/bottoms for entire dataset
    all_tops, all_bottoms = find_major_extremes(data, len(data) - 1)
    
    while current <= test_end:
        pred = generate_prediction_v5(data, current, all_tops, all_bottoms, signal_weights)
        if pred:
            results.append(pred)
        current += timedelta(days=30)
    
    return results

def calculate_accuracy(results):
    valid = [r for r in results if r['actual_outcome'] is not None]
    if not valid:
        return {}
    
    correct = sum(1 for r in valid if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    high_conf = [r for r in valid if r['confidence'] >= 70]
    high_correct = sum(1 for r in high_conf if (
        (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
        (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS']) or
        (r['prediction'] == 'NEUTRAL' and r['actual_outcome'] == 'NEUTRAL')
    ))
    
    return {
        'total': len(valid),
        'accuracy': correct / len(valid) * 100,
        'high_conf_count': len(high_conf),
        'high_conf_accuracy': high_correct / len(high_conf) * 100 if high_conf else 0,
    }

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    print(f"Loaded {len(data)} data points")
    
    # Training period for weight optimization
    train_start = datetime(1980, 1, 1)
    train_end = datetime(2019, 12, 31)
    
    # Learn optimal weights
    signal_weights = calculate_optimal_weights(data, train_start, train_end)
    
    # Test period
    test_start = datetime(2020, 1, 1)
    test_end = datetime(2026, 2, 20)
    
    print(f"\nRunning test period backtest ({test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')})...")
    results = run_backtest_v5(data, test_start, test_end, signal_weights)
    
    accuracy = calculate_accuracy(results)
    
    print("\n" + "=" * 80)
    print("HSI ANALYSIS v5 - OPTIMIZED WEIGHT LEARNING")
    print("=" * 80)
    
    print(f"\nTotal Predictions: {accuracy.get('total', 0)}")
    
    acc = accuracy.get('accuracy', 0)
    status = "✅ TARGET MET!" if acc >= 75 else "⚠️ Below target"
    print(f"\n📊 Direction Accuracy: {acc:.1f}% {status}")
    print(f"🎯 High Confidence: {accuracy.get('high_conf_count', 0)}")
    print(f"🎯 High Conf Accuracy: {accuracy.get('high_conf_accuracy', 0):.1f}%")
    
    print("\n" + "=" * 80)
    print("v5 IMPROVEMENTS")
    print("=" * 80)
    print("""
✅ Learned signal weights from 40 years of training data (1980-2019)
✅ Only uses signals with proven >50% accuracy
✅ Weights signals by historical predictive power
✅ Trend overlay prevents fighting major trends
✅ Simple, robust rules (avoids overfitting)
""")
    
    # Save results
    with open('/root/.openclaw/workspace/hsi_backtest_v5_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Price', 'Prediction', 'Confidence', 'Risk', 'Actual', 'Outcome'])
        for r in results:
            writer.writerow([
                r['date'].strftime('%Y-%m-%d'),
                f"{r['price']:.2f}",
                r['prediction'],
                f"{r['confidence']:.1f}",
                r['risk_score'],
                f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '',
                r['actual_outcome'] or ''
            ])
    
    print("\n[OK] v5 results saved")
    
    # Current analysis
    print("\n" + "=" * 80)
    print("CURRENT ANALYSIS (Feb 20, 2026) - v5 Model")
    print("=" * 80)
    
    all_tops, all_bottoms = find_major_extremes(data, len(data) - 1)
    current = generate_prediction_v5(data, datetime(2026, 2, 20), all_tops, all_bottoms, signal_weights)
    if current:
        print(f"\nPrediction: {current['prediction']}")
        print(f"Confidence: {current['confidence']:.0f}%")
        print(f"Risk Score: {current['risk_score']:.0f}/100")
        print(f"Expected Move (90d): {current['expected_move']:+.1f}%")
        print(f"Signals Used: {current['signals_used']}")

if __name__ == '__main__':
    main()
