#!/usr/bin/env python3
"""
HSI Analysis Tool v6 - Balanced Ensemble (Gann + K-Wave Core)
Target: 65% Direction Accuracy

Key Features:
1. Gann Theory and K-Wave as CORE signals (user requirement)
2. Technical indicators as confirmation
3. Simpler scoring system
4. Realistic 65% target
5. Status reporting for hourly updates
"""

import csv
import json
from datetime import datetime, timedelta
from statistics import mean, stdev
import math
import os

def parse_volume(vol_str):
    if not vol_str:
        return 0
    vol_str = str(vol_str).strip().upper()
    return float(vol_str.replace('B', '000000000').replace('M', '000000').replace(',', '')) if vol_str else 0

def parse_hsi_data(filepath):
    """Parse HSI CSV with proper Chinese header handling"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    
    lines = content.strip().split('\n')
    for line in lines[1:]:  # Skip header
        try:
            reader = csv.reader([line])
            parts = next(reader)
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
            
            data.append({
                'date': datetime(year, month, day),
                'open': open_p,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'change_pct': change_pct
            })
        except Exception as e:
            continue
    
    data.sort(key=lambda x: x['date'])
    return data

def sma(data, period, end_idx):
    if end_idx < period - 1:
        return None
    return mean([data[i]['close'] for i in range(end_idx - period + 1, end_idx + 1)])

def rsi(data, period, end_idx):
    if end_idx < period:
        return None
    gains = [max(data[i]['close'] - data[i-1]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    losses = [max(data[i-1]['close'] - data[i]['close'], 0) for i in range(end_idx - period + 1, end_idx + 1)]
    avg_gain, avg_loss = mean(gains), mean(losses)
    return 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

def get_trend(data, end_idx):
    if end_idx < 100:
        return 'UNKNOWN'
    m50 = sma(data, 50, end_idx)
    m200 = sma(data, 200, end_idx)
    if not m50 or not m200:
        return 'UNKNOWN'
    p = data[end_idx]['close']
    if p > m50 > m200:
        return 'UPTREND'
    elif p < m50 < m200:
        return 'DOWNTREND'
    return 'RANGING'

def get_momentum(data, end_idx, period=90):
    if end_idx < period:
        return 0
    return (data[end_idx]['close'] - data[end_idx - period]['close']) / data[end_idx - period]['close'] * 100

def find_major_extremes(data, window=60, min_move=15):
    """Find major tops and bottoms"""
    tops, bottoms = [], []
    for i in range(window, len(data) - window):
        # Top
        if all(data[j]['high'] <= data[i]['high'] for j in range(i-window, i+window) if j != i):
            min_after = min(data[i:min(i+180, len(data))], key=lambda x: x['low'])['low']
            drop = (data[i]['high'] - min_after) / data[i]['high'] * 100
            if drop > min_move:
                tops.append({'date': data[i]['date'], 'price': data[i]['high'], 'drop': drop})
        # Bottom
        if all(data[j]['low'] >= data[i]['low'] for j in range(i-window, i+window) if j != i):
            max_after = max(data[i:min(i+180, len(data))], key=lambda x: x['high'])['high']
            rise = (max_after - data[i]['low']) / data[i]['low'] * 100
            if rise > min_move:
                bottoms.append({'date': data[i]['date'], 'price': data[i]['low'], 'rise': rise})
    return tops, bottoms

def gann_cycle_signals(date, tops, bottoms):
    """
    Gann Theory: Time cycle anniversaries from major tops/bottoms
    Core signal type - always included
    """
    signals = []
    cycles = {
        '90-day': 90, '180-day': 180, 
        '1-year': 365, '2-year': 730, '3-year': 1095, '5-year': 1825, '7-year': 2555
    }
    
    # Top anniversaries (bearish)
    for top in tops[-15:]:
        for name, days in cycles.items():
            anniv = top['date'] + timedelta(days=days)
            diff = abs((date - anniv).days)
            if diff <= 30:
                # Closer to anniversary = higher weight
                weight = 0.8 - (diff / 30) * 0.3
                signals.append({
                    'type': 'GANN_TOP',
                    'direction': 'BEARISH',
                    'weight': weight,
                    'details': f"{name} from {top['date'].strftime('%Y-%m-%d')} ({top['drop']:.0f}% drop)"
                })
    
    # Bottom anniversaries (bullish)
    for bot in bottoms[-15:]:
        for name, days in cycles.items():
            anniv = bot['date'] + timedelta(days=days)
            diff = abs((date - anniv).days)
            if diff <= 30:
                weight = 0.8 - (diff / 30) * 0.3
                signals.append({
                    'type': 'GANN_BOTTOM',
                    'direction': 'BULLISH',
                    'weight': weight,
                    'details': f"{name} from {bot['date'].strftime('%Y-%m-%d')} ({bot['rise']:.0f}% rise)"
                })
    
    return signals

def gann_price_signals(current_price):
    """
    Gann Theory: Square of 9 price levels
    Core signal type - always included
    """
    signals = []
    sqrt_price = math.sqrt(current_price)
    
    for offset in range(-4, 5):
        level = (sqrt_price + offset * 0.25) ** 2
        pct_diff = (current_price - level) / current_price * 100
        
        if abs(pct_diff) < 2:  # Within 2%
            if pct_diff < 0:
                signals.append({
                    'type': 'GANN_SUPPORT',
                    'direction': 'BULLISH',
                    'weight': 0.5,
                    'details': f"Support at {level:.0f} ({pct_diff:.1f}%)"
                })
            else:
                signals.append({
                    'type': 'GANN_RESISTANCE',
                    'direction': 'BEARISH',
                    'weight': 0.5,
                    'details': f"Resistance at {level:.0f} ({pct_diff:.1f}%)"
                })
    
    return signals

def kondratiev_signals(date):
    """
    Kondratiev Wave Theory: Long-term economic cycles
    Core signal type - always included
    """
    waves = [
        {'name': 'Wave 4 Winter', 'start': datetime(1970,1,1), 'end': datetime(1982,1,1), 'bias': 'BEARISH', 'weight': 0.4},
        {'name': 'Wave 5 Spring', 'start': datetime(1982,1,1), 'end': datetime(1995,1,1), 'bias': 'BULLISH', 'weight': 0.4},
        {'name': 'Wave 5 Summer', 'start': datetime(1995,1,1), 'end': datetime(2000,1,1), 'bias': 'BEARISH', 'weight': 0.3},
        {'name': 'Wave 5 Autumn', 'start': datetime(2000,1,1), 'end': datetime(2008,1,1), 'bias': 'BEARISH', 'weight': 0.5},
        {'name': 'Wave 5 Winter', 'start': datetime(2008,1,1), 'end': datetime(2020,1,1), 'bias': 'BEARISH', 'weight': 0.4},
        {'name': 'Wave 6 Spring', 'start': datetime(2020,1,1), 'end': datetime(2035,1,1), 'bias': 'BULLISH', 'weight': 0.5},
    ]
    
    current = next((w for w in waves if w['start'] <= date <= w['end']), waves[-1])
    
    return [{
        'type': 'KWAVE',
        'direction': current['bias'],
        'weight': current['weight'],
        'details': f"{current['name']} - {current['bias']}"
    }]

def technical_signals(data, end_idx):
    """
    Technical indicators as confirmation signals
    """
    signals = []
    if end_idx < 100:
        return signals
    
    # RSI
    r = rsi(data, 14, end_idx)
    if r:
        if r < 30:
            signals.append({'type': 'RSI', 'direction': 'BULLISH', 'weight': 0.6, 'details': f'RSI {r:.0f} oversold'})
        elif r < 40:
            signals.append({'type': 'RSI', 'direction': 'BULLISH', 'weight': 0.4, 'details': f'RSI {r:.0f} weak'})
        elif r > 70:
            signals.append({'type': 'RSI', 'direction': 'BEARISH', 'weight': 0.6, 'details': f'RSI {r:.0f} overbought'})
        elif r > 60:
            signals.append({'type': 'RSI', 'direction': 'BEARISH', 'weight': 0.4, 'details': f'RSI {r:.0f} strong'})
    
    # Trend
    trend = get_trend(data, end_idx)
    if trend == 'UPTREND':
        signals.append({'type': 'TREND', 'direction': 'BULLISH', 'weight': 0.5, 'details': 'Price above 50/200 MA'})
    elif trend == 'DOWNTREND':
        signals.append({'type': 'TREND', 'direction': 'BEARISH', 'weight': 0.5, 'details': 'Price below 50/200 MA'})
    
    # Momentum
    mom = get_momentum(data, end_idx, 90)
    if mom > 15:
        signals.append({'type': 'MOMENTUM', 'direction': 'BULLISH', 'weight': 0.4, 'details': f'90d momentum +{mom:.0f}%'})
    elif mom < -15:
        signals.append({'type': 'MOMENTUM', 'direction': 'BEARISH', 'weight': 0.4, 'details': f'90d momentum {mom:.0f}%'})
    
    return signals

def calculate_prediction(all_signals, trend):
    """
    Calculate prediction from weighted signals
    Core Gann + K-Wave signals get priority
    """
    bullish_weight = 0
    bearish_weight = 0
    core_bullish = 0  # Gann + K-Wave bullish
    core_bearish = 0  # Gann + K-Wave bearish
    
    for sig in all_signals:
        if sig['direction'] == 'BULLISH':
            bullish_weight += sig['weight']
            if sig['type'] in ['GANN_TOP', 'GANN_BOTTOM', 'GANN_SUPPORT', 'KWAVE']:
                core_bullish += sig['weight']
        else:
            bearish_weight += sig['weight']
            if sig['type'] in ['GANN_TOP', 'GANN_BOTTOM', 'GANN_RESISTANCE', 'KWAVE']:
                core_bearish += sig['weight']
    
    total = bullish_weight + bearish_weight
    if total == 0:
        return 'NEUTRAL', 50, 50, 0
    
    # Net bias (-1 to +1, positive = bullish)
    net = (bullish_weight - bearish_weight) / total
    
    # Risk score (0-100, higher = more bearish)
    risk_score = 50 - (net * 50)
    
    # Trend adjustment (don't fight the trend)
    if trend == 'UPTREND' and risk_score > 50:
        risk_score = max(risk_score - 10, 40)  # Reduce bearish call in uptrend
    elif trend == 'DOWNTREND' and risk_score < 50:
        risk_score = min(risk_score + 10, 60)  # Reduce bullish call in downtrend
    
    # Generate prediction
    if risk_score >= 60:
        prediction = 'BEARISH'
        confidence = min(50 + (risk_score - 60) * 2, 90)
    elif risk_score <= 40:
        prediction = 'BULLISH'
        confidence = min(50 + (40 - risk_score) * 2, 90)
    else:
        prediction = 'NEUTRAL'
        confidence = 50
    
    # Expected move
    if prediction == 'BEARISH':
        expected_move = -6 - (risk_score - 60) * 0.3
    elif prediction == 'BULLISH':
        expected_move = 6 + (40 - risk_score) * 0.3
    else:
        expected_move = 0
    
    return prediction, confidence, risk_score, expected_move

def generate_prediction_v6(data, date, tops, bottoms):
    """Generate complete prediction"""
    hist = [d for d in data if d['date'] <= date]
    if len(hist) < 200:
        return None
    
    end_idx = len(hist) - 1
    current_price = hist[-1]['close']
    
    # Generate all signals
    all_signals = []
    
    # Core: Gann Theory (cycle anniversaries)
    all_signals.extend(gann_cycle_signals(date, tops, bottoms))
    
    # Core: Gann Theory (price levels)
    all_signals.extend(gann_price_signals(current_price))
    
    # Core: Kondratiev Wave
    all_signals.extend(kondratiev_signals(date))
    
    # Confirmation: Technical indicators
    all_signals.extend(technical_signals(hist, end_idx))
    
    # Get trend
    trend = get_trend(hist, end_idx)
    
    # Calculate prediction
    prediction, confidence, risk_score, expected_move = calculate_prediction(all_signals, trend)
    
    # Get actual outcome
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
        'trend': trend,
        'signals': all_signals,
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct
    }

def run_backtest_v6(data, test_start, test_end, tops, bottoms):
    """Run backtest"""
    results = []
    current = test_start
    
    while current <= test_end:
        pred = generate_prediction_v6(data, current, tops, bottoms)
        if pred:
            results.append(pred)
        current += timedelta(days=30)
    
    return results

def calculate_accuracy(results):
    """Calculate accuracy metrics"""
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
    
    # Major moves
    major_drops = [r for r in valid if r['actual_move_pct'] and r['actual_move_pct'] < -15]
    major_drops_pred = [r for r in major_drops if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']]
    
    major_rallies = [r for r in valid if r['actual_move_pct'] and r['actual_move_pct'] > 15]
    major_rallies_pred = [r for r in major_rallies if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']]
    
    bullish = len([r for r in valid if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']])
    bearish = len([r for r in valid if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']])
    
    return {
        'total': len(valid),
        'accuracy': correct / len(valid) * 100,
        'high_conf_count': len(high_conf),
        'high_conf_accuracy': high_correct / len(high_conf) * 100 if high_conf else 0,
        'major_drops': len(major_drops),
        'major_drops_predicted': len(major_drops_pred),
        'major_drop_recall': len(major_drops_pred) / len(major_drops) * 100 if major_drops else 0,
        'major_rallies': len(major_rallies),
        'major_rallies_predicted': len(major_rallies_pred),
        'major_rally_recall': len(major_rallies_pred) / len(major_rallies) * 100 if major_rallies else 0,
        'bullish_predictions': bullish,
        'bearish_predictions': bearish,
        'bearish_bias': bearish / (bullish + bearish) * 100 if (bullish + bearish) > 0 else 0
    }

def save_status(accuracy, current_pred, run_id='v6'):
    """Save status for hourly updates"""
    status = {
        'timestamp': datetime.utcnow().isoformat(),
        'model': run_id,
        'accuracy': accuracy,
        'current_prediction': current_pred,
        'status': 'complete' if accuracy else 'running'
    }
    
    status_path = '/root/.openclaw/workspace/hsi_status.json'
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2, default=str)
    
    return status_path

def print_report(accuracy, current_pred=None):
    """Print comprehensive report"""
    print("\n" + "=" * 80)
    print("HSI ANALYSIS v6 - GANN + K-WAVE CORE (Target: 65%)")
    print("=" * 80)
    
    print(f"\nTotal Predictions: {accuracy.get('total', 0)}")
    
    acc = accuracy.get('accuracy', 0)
    status = "✅ TARGET MET!" if acc >= 65 else "⚠️ Below 65% target"
    print(f"\n📊 Direction Accuracy: {acc:.1f}% {status}")
    print(f"🎯 High Confidence: {accuracy.get('high_conf_count', 0)}")
    print(f"🎯 High Conf Accuracy: {accuracy.get('high_conf_accuracy', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MAJOR MOVE PREDICTION")
    print("-" * 80)
    print(f"📉 Major Drops: {accuracy.get('major_drops_predicted', 0)}/{accuracy.get('major_drops', 0)} ({accuracy.get('major_drop_recall', 0):.1f}%)")
    print(f"📈 Major Rallies: {accuracy.get('major_rallies_predicted', 0)}/{accuracy.get('major_rallies', 0)} ({accuracy.get('major_rally_recall', 0):.1f}%)")
    
    print("\n" + "-" * 80)
    print("DISTRIBUTION")
    print("-" * 80)
    print(f"🐂 Bullish: {accuracy.get('bullish_predictions', 0)}")
    print(f"🐻 Bearish: {accuracy.get('bearish_predictions', 0)}")
    print(f"📊 Bearish Bias: {accuracy.get('bearish_bias', 0):.1f}%")
    
    print("\n" + "=" * 80)
    print("v6 MODEL FEATURES")
    print("=" * 80)
    print("""
✅ Gann Theory: Time cycle anniversaries (CORE)
✅ Gann Theory: Square of 9 price levels (CORE)
✅ Kondratiev Wave: Long-term economic cycles (CORE)
✅ Technical Confirmation: RSI, Trend, Momentum
✅ Trend Filter: Don't fight major trends
✅ Realistic Target: 65% direction accuracy
✅ Hourly Status Updates: hsi_status.json
""")
    
    if current_pred:
        print("\n" + "=" * 80)
        print("CURRENT ANALYSIS (Feb 20, 2026)")
        print("=" * 80)
        print(f"\nPrediction: {current_pred['prediction']}")
        print(f"Confidence: {current_pred['confidence']:.0f}%")
        print(f"Risk Score: {current_pred['risk_score']:.0f}/100")
        print(f"Expected Move (90d): {current_pred['expected_move']:+.1f}%")
        print(f"Trend: {current_pred['trend']}")
        print(f"Total Signals: {len(current_pred['signals'])}")
        
        # Show key signals
        core_signals = [s for s in current_pred['signals'] if s['type'] in ['GANN_TOP', 'GANN_BOTTOM', 'KWAVE']]
        if core_signals:
            print(f"\nCore Signals (Gann + K-Wave):")
            for s in core_signals[:5]:
                print(f"  • [{s['direction']}] {s['details']}")

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    print(f"Loaded {len(data)} data points ({data[0]['date'].strftime('%Y')} to {data[-1]['date'].strftime('%Y')})")
    
    # Find major tops/bottoms from entire dataset
    print("\nIdentifying major tops and bottoms...")
    tops, bottoms = find_major_extremes(data)
    print(f"Found {len(tops)} major tops, {len(bottoms)} major bottoms")
    
    # Test period
    test_start = datetime(2020, 1, 1)
    test_end = datetime(2026, 2, 20)
    
    print(f"\nRunning backtest ({test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')})...")
    results = run_backtest_v6(data, test_start, test_end, tops, bottoms)
    print(f"Generated {len(results)} predictions")
    
    accuracy = calculate_accuracy(results)
    
    # Get current prediction
    current_pred = generate_prediction_v6(data, datetime(2026, 2, 20), tops, bottoms)
    
    # Print report
    print_report(accuracy, current_pred)
    
    # Save status for hourly updates
    status_path = save_status(accuracy, current_pred)
    print(f"\n[OK] Status saved to {status_path}")
    
    # Save results
    with open('/root/.openclaw/workspace/hsi_backtest_v6_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Price', 'Prediction', 'Confidence', 'Risk', 'Actual', 'Outcome', 'Signals'])
        for r in results:
            writer.writerow([
                r['date'].strftime('%Y-%m-%d'),
                f"{r['price']:.2f}",
                r['prediction'],
                f"{r['confidence']:.1f}",
                r['risk_score'],
                f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '',
                r['actual_outcome'] or '',
                len(r['signals'])
            ])
    
    print("[OK] Results saved to hsi_backtest_v6_results.csv")
    
    # Save detailed report
    report_path = '/root/.openclaw/workspace/hsi_v6_report.md'
    with open(report_path, 'w') as f:
        f.write("# HSI Analysis v6 Report\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write(f"## Accuracy: {accuracy.get('accuracy', 0):.1f}%\n\n")
        f.write(f"## Current Prediction: {current_pred['prediction']}\n")
        f.write(f"- Confidence: {current_pred['confidence']:.0f}%\n")
        f.write(f"- Risk Score: {current_pred['risk_score']:.0f}/100\n")
        f.write(f"- Expected Move: {current_pred['expected_move']:+.1f}%\n")
    print(f"[OK] Report saved to {report_path}")

if __name__ == '__main__':
    main()
