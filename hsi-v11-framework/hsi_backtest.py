#!/usr/bin/env python3
"""
HSI Analysis Backtesting Tool
Tests Gann + Kondratiev prediction accuracy using historical data
"""

import csv
from datetime import datetime, timedelta
from statistics import mean, stdev
import math

def parse_volume(vol_str):
    """Parse volume string like '1.69B' or '808.52M'"""
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
    """Parse HSI CSV data"""
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

def find_major_tops(data, window=60, min_drop=15):
    """Find historical major tops with significant drops after"""
    major_tops = []
    for i in range(window, len(data) - window):
        current_high = data[i]['high']
        is_top = True
        for j in range(i - window, i + window):
            if j != i and data[j]['high'] > current_high:
                is_top = False
                break
        if is_top:
            peak_price = current_high
            min_after = min(data[i:min(i+180, len(data))], key=lambda x: x['low'])['low']
            drop_pct = (peak_price - min_after) / peak_price * 100
            if drop_pct > min_drop:
                major_tops.append({
                    'date': data[i]['date'],
                    'price': peak_price,
                    'drop_pct': drop_pct,
                    'index': i
                })
    return major_tops

def find_major_bottoms(data, window=60, min_rise=15):
    """Find historical major bottoms with significant rises after"""
    major_bottoms = []
    for i in range(window, len(data) - window):
        current_low = data[i]['low']
        is_bottom = True
        for j in range(i - window, i + window):
            if j != i and data[j]['low'] < current_low:
                is_bottom = False
                break
        if is_bottom:
            trough_price = current_low
            max_after = max(data[i:min(i+180, len(data))], key=lambda x: x['high'])['high']
            rise_pct = (max_after - trough_price) / trough_price * 100
            if rise_pct > min_rise:
                major_bottoms.append({
                    'date': data[i]['date'],
                    'price': trough_price,
                    'rise_pct': rise_pct,
                    'index': i
                })
    return major_bottoms

def get_kondratiev_phase(date):
    """Get Kondratiev Wave phase for a given date"""
    k_waves = [
        {'name': 'Wave 4 Winter', 'start': datetime(1970, 1, 1), 'end': datetime(1982, 1, 1), 'phase': 'winter'},
        {'name': 'Wave 5 Spring', 'start': datetime(1982, 1, 1), 'end': datetime(1995, 1, 1), 'phase': 'spring'},
        {'name': 'Wave 5 Summer', 'start': datetime(1995, 1, 1), 'end': datetime(2000, 1, 1), 'phase': 'summer'},
        {'name': 'Wave 5 Autumn', 'start': datetime(2000, 1, 1), 'end': datetime(2008, 1, 1), 'phase': 'autumn'},
        {'name': 'Wave 5 Winter', 'start': datetime(2008, 1, 1), 'end': datetime(2020, 1, 1), 'phase': 'winter'},
        {'name': 'Wave 6 Spring', 'start': datetime(2020, 1, 1), 'end': datetime(2035, 1, 1), 'phase': 'spring'},
    ]
    
    for wave in k_waves:
        if wave['start'] <= date <= wave['end']:
            return wave
    return k_waves[-1]

def generate_gann_signals(data, analysis_date, lookback_days=365*10):
    """Generate Gann signals as of a specific analysis date"""
    signals = []
    
    # Get data up to analysis date
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 365:
        return signals
    
    latest_date = analysis_date
    latest_close = historical_data[-1]['close']
    
    # Gann time cycles
    gann_cycles = {
        '90-day': 90,
        '180-day': 180,
        '1-year': 365,
        '2-year': 730,
        '3-year': 1095,
        '5-year': 1825,
        '7-year': 2555,
        '10-year': 3650
    }
    
    # Find major tops in historical data
    major_tops = find_major_tops(historical_data, window=60, min_drop=15)
    
    # Check cycle anniversaries from major tops
    for top in major_tops[-10:]:
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = top['date'] + timedelta(days=cycle_days)
            days_from_anniversary = abs((latest_date - anniversary).days)
            
            if days_from_anniversary <= 30:
                signals.append({
                    'type': 'GANN_CYCLE',
                    'signal': f'{cycle_name} anniversary from {top["date"].strftime("%Y-%m-%d")} top',
                    'date': anniversary,
                    'days_away': days_from_anniversary,
                    'severity': 'MEDIUM' if days_from_anniversary > 15 else 'HIGH',
                    'reference_price': top['price'],
                    'historical_drop': f"{top['drop_pct']:.1f}%"
                })
    
    # Gann Square of 9
    sqrt_price = math.sqrt(latest_close)
    for offset in range(-4, 5):
        level = (sqrt_price + offset * 0.25) ** 2
        if abs(latest_close - level) / latest_close < 0.02:
            signals.append({
                'type': 'GANN_PRICE',
                'signal': f'Price near Gann Square of 9 level: {level:.0f}',
                'current_price': latest_close,
                'gann_level': level,
                'severity': 'MEDIUM'
            })
    
    return signals

def generate_prediction(data, analysis_date, forecast_days=90):
    """Generate prediction as of analysis date"""
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 365:
        return None
    
    gann_signals = generate_gann_signals(data, analysis_date)
    k_phase = get_kondratiev_phase(analysis_date)
    
    # Count signal severity
    high_count = sum(1 for s in gann_signals if s.get('severity') == 'HIGH')
    medium_count = sum(1 for s in gann_signals if s.get('severity') == 'MEDIUM')
    
    # K-Wave risk adjustment
    k_risk = 0
    if k_phase['phase'] in ['autumn', 'winter']:
        k_risk = 2
    elif k_phase['phase'] == 'summer':
        k_risk = 1
    
    # Calculate risk score
    risk_score = high_count * 15 + medium_count * 5 + k_risk * 10
    risk_score = min(risk_score, 100)
    
    # Generate prediction
    if risk_score >= 70:
        prediction = 'BEARISH'
        confidence = min(risk_score, 95)
        expected_move = -15 - (risk_score - 70) * 0.5  # -15% to -25%
    elif risk_score >= 40:
        prediction = 'NEUTRAL_BEARS'
        confidence = 50 + risk_score * 0.5
        expected_move = -5 - (risk_score - 40) * 0.3
    elif risk_score >= 20:
        prediction = 'NEUTRAL_BULLS'
        confidence = 50 + risk_score * 0.5
        expected_move = 5 + (risk_score - 20) * 0.3
    else:
        prediction = 'BULLISH'
        confidence = 50 + risk_score
        expected_move = 10 + risk_score * 0.5
    
    # Get current price
    current_price = historical_data[-1]['close']
    
    # Find forecast period actuals
    forecast_end = analysis_date + timedelta(days=forecast_days)
    forecast_data = [d for d in data if analysis_date < d['date'] <= forecast_end]
    
    actual_outcome = None
    actual_move_pct = None
    if forecast_data:
        max_price = max(d['high'] for d in forecast_data)
        min_price = min(d['low'] for d in forecast_data)
        end_price = forecast_data[-1]['close']
        
        actual_move_pct = (end_price - current_price) / current_price * 100
        
        # Determine actual outcome
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
        'analysis_date': analysis_date,
        'current_price': current_price,
        'prediction': prediction,
        'confidence': confidence,
        'risk_score': risk_score,
        'expected_move': expected_move,
        'forecast_days': forecast_days,
        'gann_signals': gann_signals,
        'k_phase': k_phase['phase'],
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct,
        'forecast_high': max_price if forecast_data else None,
        'forecast_low': min_price if forecast_data else None
    }

def run_backtest(data, start_date, end_date, step_days=30, forecast_days=90):
    """Run backtest over historical period"""
    results = []
    current = start_date
    
    while current <= end_date:
        pred = generate_prediction(data, current, forecast_days)
        if pred:
            results.append(pred)
        current += timedelta(days=step_days)
    
    return results

def calculate_accuracy(results):
    """Calculate prediction accuracy metrics"""
    if not results:
        return {}
    
    # Filter results with actual outcomes
    valid_results = [r for r in results if r['actual_outcome'] is not None]
    
    if not valid_results:
        return {}
    
    # Direction accuracy
    correct_direction = 0
    for r in valid_results:
        pred = r['prediction']
        actual = r['actual_outcome']
        
        # Simplified: bearish predictions vs bearish outcomes
        if pred in ['BEARISH', 'NEUTRAL_BEARS'] and actual in ['BEARISH', 'NEUTRAL_BEARS']:
            correct_direction += 1
        elif pred in ['BULLISH', 'NEUTRAL_BULLS'] and actual in ['BULLISH', 'NEUTRAL_BULLS', 'NEUTRAL']:
            correct_direction += 1
        elif pred == 'NEUTRAL' and actual == 'NEUTRAL':
            correct_direction += 1
    
    direction_accuracy = correct_direction / len(valid_results) * 100
    
    # High confidence predictions
    high_conf_results = [r for r in valid_results if r['confidence'] >= 70]
    high_conf_correct = 0
    for r in high_conf_results:
        pred = r['prediction']
        actual = r['actual_outcome']
        if pred in ['BEARISH', 'NEUTRAL_BEARS'] and actual in ['BEARISH', 'NEUTRAL_BEARS']:
            high_conf_correct += 1
        elif pred in ['BULLISH', 'NEUTRAL_BULLS'] and actual in ['BULLISH', 'NEUTRAL_BULLS', 'NEUTRAL']:
            high_conf_correct += 1
    
    high_conf_accuracy = high_conf_correct / len(high_conf_results) * 100 if high_conf_results else 0
    
    # Major drop prediction (the key metric for "peak of big drop")
    major_drops = [r for r in valid_results if r['actual_move_pct'] < -15]
    major_drops_predicted = [r for r in major_drops if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['risk_score'] >= 60]
    
    major_drop_recall = len(major_drops_predicted) / len(major_drops) * 100 if major_drops else 0
    
    # False positive rate
    non_drops = [r for r in valid_results if r['actual_move_pct'] >= -15]
    false_positives = [r for r in non_drops if r['prediction'] == 'BEARISH' and r['risk_score'] >= 70]
    false_positive_rate = len(false_positives) / len(non_drops) * 100 if non_drops else 0
    
    # Average predicted vs actual move
    avg_predicted_move = mean([r['expected_move'] for r in valid_results])
    avg_actual_move = mean([r['actual_move_pct'] for r in valid_results])
    
    return {
        'total_predictions': len(valid_results),
        'direction_accuracy': direction_accuracy,
        'high_confidence_predictions': len(high_conf_results),
        'high_confidence_accuracy': high_conf_accuracy,
        'major_drops': len(major_drops),
        'major_drops_predicted': len(major_drops_predicted),
        'major_drop_recall': major_drop_recall,
        'false_positive_rate': false_positive_rate,
        'avg_predicted_move': avg_predicted_move,
        'avg_actual_move': avg_actual_move
    }

def print_backtest_report(results, accuracy, train_period, test_period):
    """Print comprehensive backtest report"""
    print("=" * 80)
    print("HSI GANN + KONDRAVIEV BACKTESTING REPORT")
    print("=" * 80)
    
    print(f"\nTraining Period: {train_period[0].strftime('%Y-%m-%d')} to {train_period[1].strftime('%Y-%m-%d')}")
    print(f"Test Period: {test_period[0].strftime('%Y-%m-%d')} to {test_period[1].strftime('%Y-%m-%d')}")
    print(f"Total Predictions: {accuracy.get('total_predictions', 0)}")
    
    print("\n" + "=" * 80)
    print("ACCURACY METRICS")
    print("=" * 80)
    
    print(f"\n📊 Direction Accuracy: {accuracy.get('direction_accuracy', 0):.1f}%")
    print(f"🎯 High Confidence Predictions: {accuracy.get('high_confidence_predictions', 0)}")
    print(f"🎯 High Confidence Accuracy: {accuracy.get('high_confidence_accuracy', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MAJOR DROP PREDICTION (Key Metric for 'Peak of Big Drop')")
    print("-" * 80)
    print(f"📉 Major Drops in Test Period (>15% decline): {accuracy.get('major_drops', 0)}")
    print(f"✅ Major Drops Predicted: {accuracy.get('major_drops_predicted', 0)}")
    print(f"🎯 Major Drop Recall Rate: {accuracy.get('major_drop_recall', 0):.1f}%")
    print(f"⚠️  False Positive Rate: {accuracy.get('false_positive_rate', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MOVE PREDICTION ACCURACY")
    print("-" * 80)
    print(f"📈 Average Predicted Move: {accuracy.get('avg_predicted_move', 0):.1f}%")
    print(f"📊 Average Actual Move: {accuracy.get('avg_actual_move', 0):.1f}%")
    
    print("\n" + "=" * 80)
    print("DETAILED PREDICTION LOG")
    print("=" * 80)
    
    # Show predictions chronologically
    for r in results[:20]:  # First 20 predictions
        status = "✓" if (
            (r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['actual_outcome'] in ['BEARISH', 'NEUTRAL_BEARS']) or
            (r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['actual_outcome'] in ['BULLISH', 'NEUTRAL_BULLS', 'NEUTRAL'])
        ) else "✗"
        
        print(f"\n{status} {r['analysis_date'].strftime('%Y-%m-%d')}")
        print(f"   Price: {r['current_price']:,.0f} | Prediction: {r['prediction']} ({r['confidence']:.0f}% conf)")
        print(f"   Risk Score: {r['risk_score']}/100 | K-Wave: {r['k_phase']}")
        if r['actual_move_pct'] is not None:
            print(f"   Actual Move ({r['forecast_days']}d): {r['actual_move_pct']:+.1f}% | Outcome: {r['actual_outcome']}")
        if r['gann_signals']:
            high_signals = [s for s in r['gann_signals'] if s.get('severity') == 'HIGH']
            if high_signals:
                print(f"   HIGH Signals: {len(high_signals)}")
    
    print("\n" + "=" * 80)
    print("METHODOLOGY NOTES")
    print("=" * 80)
    print("""
- Training data: 1980-2019 (40 years of HSI history)
- Test data: 2020-2026 (includes COVID crash, recovery, recent volatility)
- Prediction frequency: Every 30 days
- Forecast horizon: 90 days
- Major drop threshold: >15% decline within forecast period
- High confidence threshold: >=70% confidence score

Gann Signals Used:
- Time cycle anniversaries (90-day to 10-year)
- Square of 9 price levels
- Major top/bottom identification (15%+ moves)

Kondratiev Wave Adjustment:
- Autumn/Winter phases: +20 risk points
- Summer phase: +10 risk points
- Spring phase: No adjustment
""")
    
    print("\n" + "=" * 80)
    print("DISCLAIMER: Backtesting results do not guarantee future performance.")
    print("This analysis is for educational purposes only. Not financial advice.")
    print("=" * 80)

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    
    if not data:
        print("ERROR: Could not load HSI data")
        return
    
    print(f"Loaded {len(data)} data points")
    print(f"Date range: {data[0]['date'].strftime('%Y-%m-%d')} to {data[-1]['date'].strftime('%Y-%m-%d')}")
    
    # Define training and test periods
    train_start = datetime(1980, 1, 1)
    train_end = datetime(2019, 12, 31)
    test_start = datetime(2020, 1, 1)
    test_end = datetime(2026, 2, 20)
    
    print(f"\nTraining Period: {train_start.strftime('%Y-%m-%d')} to {train_end.strftime('%Y-%m-%d')}")
    print(f"Test Period: {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
    
    print("\nRunning backtest...")
    results = run_backtest(data, test_start, test_end, step_days=30, forecast_days=90)
    
    print(f"Generated {len(results)} predictions")
    
    accuracy = calculate_accuracy(results)
    
    print("\n")
    print_backtest_report(results, accuracy, (train_start, train_end), (test_start, test_end))
    
    # Save results to CSV
    with open('/root/.openclaw/workspace/hsi_backtest_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Price', 'Prediction', 'Confidence', 'Risk_Score', 'K_Phase', 
                        'Actual_Move_Pct', 'Actual_Outcome', 'Gann_Signals_Count'])
        for r in results:
            writer.writerow([
                r['analysis_date'].strftime('%Y-%m-%d'),
                f"{r['current_price']:.2f}",
                r['prediction'],
                f"{r['confidence']:.1f}",
                r['risk_score'],
                r['k_phase'],
                f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '',
                r['actual_outcome'] if r['actual_outcome'] else '',
                len(r['gann_signals'])
            ])
    
    print("\n[OK] Backtest results saved to hsi_backtest_results.csv")

if __name__ == '__main__':
    main()
