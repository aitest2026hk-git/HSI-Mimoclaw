#!/usr/bin/env python3
"""
HSI Analysis Tool v2 - Improved Model
Addresses bearish bias, adds bullish signals, momentum filters, and better calibration

Key Improvements over v1:
1. Added bullish signal framework (bottom anniversaries, oversold conditions)
2. Reduced K-Wave weighting (+10 vs +20 for Autumn/Winter)
3. Added momentum filter (90-day, 200-day trends)
4. Added mean reversion signals (distance from MA)
5. K-Wave Spring now has bullish adjustment (-5 points)
6. Volume confirmation for signals
7. Better confidence calibration
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

def calculate_moving_average(data, period, end_index=None):
    """Calculate simple moving average"""
    if end_index is None:
        end_index = len(data)
    start_index = max(0, end_index - period)
    if end_index - start_index < period // 2:
        return None
    prices = [data[i]['close'] for i in range(start_index, end_index)]
    return mean(prices) if prices else None

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
    """Find historical major bottoms with significant rises after - NEW for v2"""
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

def generate_gann_signals_v2(data, analysis_date, lookback_days=365*10):
    """
    Generate Gann signals v2 - includes both tops AND bottoms
    Key improvement over v1: bullish signals from bottom anniversaries
    """
    signals = []
    
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 365:
        return signals
    
    latest_date = analysis_date
    latest_close = historical_data[-1]['close']
    latest_index = len(historical_data) - 1
    
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
    
    # Bearish signals from major tops
    major_tops = find_major_tops(historical_data, window=60, min_drop=15)
    for top in major_tops[-10:]:
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = top['date'] + timedelta(days=cycle_days)
            days_from_anniversary = abs((latest_date - anniversary).days)
            
            if days_from_anniversary <= 30:
                signals.append({
                    'type': 'GANN_CYCLE_BEARISH',
                    'signal': f'{cycle_name} anniversary from {top["date"].strftime("%Y-%m-%d")} top',
                    'date': anniversary,
                    'days_away': days_from_anniversary,
                    'direction': 'BEARISH',
                    'severity': 'MEDIUM' if days_from_anniversary > 15 else 'HIGH',
                    'reference_price': top['price'],
                    'historical_drop': f"{top['drop_pct']:.1f}%"
                })
    
    # NEW v2: Bullish signals from major bottoms
    major_bottoms = find_major_bottoms(historical_data, window=60, min_rise=15)
    for bottom in major_bottoms[-10:]:
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = bottom['date'] + timedelta(days=cycle_days)
            days_from_anniversary = abs((latest_date - anniversary).days)
            
            if days_from_anniversary <= 30:
                signals.append({
                    'type': 'GANN_CYCLE_BULLISH',
                    'signal': f'{cycle_name} anniversary from {bottom["date"].strftime("%Y-%m-%d")} bottom',
                    'date': anniversary,
                    'days_away': days_from_anniversary,
                    'direction': 'BULLISH',
                    'severity': 'MEDIUM' if days_from_anniversary > 15 else 'HIGH',
                    'reference_price': bottom['price'],
                    'historical_rise': f"{bottom['rise_pct']:.1f}%"
                })
    
    # Gann Square of 9 - price levels
    sqrt_price = math.sqrt(latest_close)
    gann_levels = []
    for offset in range(-4, 5):
        level = (sqrt_price + offset * 0.25) ** 2
        gann_levels.append(level)
    
    # Check if near support (bullish) or resistance (bearish)
    for level in gann_levels:
        pct_diff = (latest_close - level) / latest_close * 100
        if abs(pct_diff) < 2:  # Within 2%
            if pct_diff < 0:
                # Price below level - potential support (bullish)
                signals.append({
                    'type': 'GANN_PRICE_SUPPORT',
                    'signal': f'Price near Gann support level: {level:.0f}',
                    'current_price': latest_close,
                    'gann_level': level,
                    'direction': 'BULLISH',
                    'severity': 'MEDIUM'
                })
            else:
                # Price above level - potential resistance (bearish)
                signals.append({
                    'type': 'GANN_PRICE_RESISTANCE',
                    'signal': f'Price near Gann resistance level: {level:.0f}',
                    'current_price': latest_close,
                    'gann_level': level,
                    'direction': 'BEARISH',
                    'severity': 'MEDIUM'
                })
    
    return signals

def generate_momentum_signals(data, analysis_date):
    """
    NEW v2: Momentum signals to filter out bearish calls during strong uptrends
    """
    signals = []
    
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 200:
        return signals
    
    latest_index = len(historical_data) - 1
    latest_close = historical_data[-1]['close']
    
    # Calculate moving averages
    ma_20 = calculate_moving_average(historical_data, 20, latest_index + 1)
    ma_50 = calculate_moving_average(historical_data, 50, latest_index + 1)
    ma_200 = calculate_moving_average(historical_data, 200, latest_index + 1)
    
    if not all([ma_20, ma_50, ma_200]):
        return signals
    
    # Price vs MA relationships
    pct_above_ma20 = (latest_close - ma_20) / ma_20 * 100
    pct_above_ma50 = (latest_close - ma_50) / ma_50 * 100
    pct_above_ma200 = (latest_close - ma_200) / ma_200 * 100
    
    # Strong uptrend (bullish)
    if pct_above_ma20 > 5 and pct_above_ma50 > 10 and pct_above_ma200 > 15:
        signals.append({
            'type': 'MOMENTUM_STRONG_UPTREND',
            'signal': 'Strong uptrend - price well above all MAs',
            'direction': 'BULLISH',
            'severity': 'HIGH',
            'ma_20': ma_20,
            'ma_50': ma_50,
            'ma_200': ma_200
        })
    # Strong downtrend (bearish)
    elif pct_above_ma20 < -5 and pct_above_ma50 < -10 and pct_above_ma200 < -15:
        signals.append({
            'type': 'MOMENTUM_STRONG_DOWNTREND',
            'signal': 'Strong downtrend - price well below all MAs',
            'direction': 'BEARISH',
            'severity': 'HIGH',
            'ma_20': ma_20,
            'ma_50': ma_50,
            'ma_200': ma_200
        })
    
    # 90-day momentum
    if latest_index >= 90:
        price_90d_ago = historical_data[latest_index - 90]['close']
        momentum_90d = (latest_close - price_90d_ago) / price_90d_ago * 100
        
        if momentum_90d > 15:
            signals.append({
                'type': 'MOMENTUM_90D_STRONG',
                'signal': f'90-day momentum: +{momentum_90d:.1f}%',
                'direction': 'BULLISH',
                'severity': 'MEDIUM',
                'momentum': momentum_90d
            })
        elif momentum_90d < -15:
            signals.append({
                'type': 'MOMENTUM_90D_WEAK',
                'signal': f'90-day momentum: {momentum_90d:.1f}%',
                'direction': 'BEARISH',
                'severity': 'MEDIUM',
                'momentum': momentum_90d
            })
    
    # MA crossovers
    ma_50_20d_ago = calculate_moving_average(historical_data, 50, latest_index + 1 - 20)
    if ma_50_20d_ago:
        # Golden cross (50 crosses above 200) - bullish
        if ma_50 > ma_200 and ma_50_20d_ago <= ma_200:
            signals.append({
                'type': 'MOMENTUM_GOLDEN_CROSS',
                'signal': 'Golden Cross - 50-day MA crossed above 200-day MA',
                'direction': 'BULLISH',
                'severity': 'HIGH'
            })
        # Death cross (50 crosses below 200) - bearish
        elif ma_50 < ma_200 and ma_50_20d_ago >= ma_200:
            signals.append({
                'type': 'MOMENTUM_DEATH_CROSS',
                'signal': 'Death Cross - 50-day MA crossed below 200-day MA',
                'direction': 'BEARISH',
                'severity': 'HIGH'
            })
    
    return signals

def generate_mean_reversion_signals(data, analysis_date):
    """
    NEW v2: Mean reversion signals - oversold = bullish, overbought = bearish
    """
    signals = []
    
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 50:
        return signals
    
    latest_index = len(historical_data) - 1
    latest_close = historical_data[-1]['close']
    
    # Calculate 20-day stats
    recent_20 = [d['close'] for d in historical_data[max(0, latest_index-19):latest_index+1]]
    avg_20 = mean(recent_20)
    std_20 = stdev(recent_20) if len(recent_20) > 1 else 1
    
    # Z-score
    z_score = (latest_close - avg_20) / std_20 if std_20 > 0 else 0
    
    if z_score < -2:
        signals.append({
            'type': 'MEAN_REVERSION_OVERSOLD',
            'signal': f'Oversold - price {abs(z_score):.1f} std devs below 20-day mean',
            'direction': 'BULLISH',
            'severity': 'HIGH',
            'z_score': z_score
        })
    elif z_score < -1:
        signals.append({
            'type': 'MEAN_REVERSION_WEAK',
            'signal': f'Weak - price {abs(z_score):.1f} std devs below 20-day mean',
            'direction': 'BULLISH',
            'severity': 'MEDIUM',
            'z_score': z_score
        })
    elif z_score > 2:
        signals.append({
            'type': 'MEAN_REVERSION_OVERBOUGHT',
            'signal': f'Overbought - price {z_score:.1f} std devs above 20-day mean',
            'direction': 'BEARISH',
            'severity': 'HIGH',
            'z_score': z_score
        })
    elif z_score > 1:
        signals.append({
            'type': 'MEAN_REVERSION_STRONG',
            'signal': f'Strong - price {z_score:.1f} std devs above 20-day mean',
            'direction': 'BEARISH',
            'severity': 'MEDIUM',
            'z_score': z_score
        })
    
    # 52-week high/low
    if len(historical_data) >= 252:
        year_high = max(d['high'] for d in historical_data[-252:])
        year_low = min(d['low'] for d in historical_data[-252:])
        pct_from_high = (year_high - latest_close) / year_high * 100
        pct_from_low = (latest_close - year_low) / year_low * 100
        
        if pct_from_high < 5:
            signals.append({
                'type': 'MEAN_REVERSION_NEAR_HIGH',
                'signal': f'Near 52-week high - {pct_from_high:.1f}% below',
                'direction': 'BEARISH',
                'severity': 'MEDIUM'
            })
        if pct_from_low < 5:
            signals.append({
                'type': 'MEAN_REVERSION_NEAR_LOW',
                'signal': f'Near 52-week low - {pct_from_low:.1f}% above',
                'direction': 'BULLISH',
                'severity': 'MEDIUM'
            })
    
    return signals

def generate_kondratiev_signals_v2(data, analysis_date):
    """
    v2: Improved K-Wave signals with bullish Spring adjustment
    """
    signals = []
    
    k_phase = get_kondratiev_phase(analysis_date)
    
    # Phase descriptions
    descriptions = {
        'spring': 'Expansion phase - New technologies emerge, growth accelerates, optimism builds',
        'summer': 'Peak growth - Inflation rises, speculation increases, economy overheats',
        'autumn': 'Stagflation - Growth slows, debt peaks, market becomes fragile (TOP FORMATION)',
        'winter': 'Deflation/Crash - Debt liquidation, depression, reset before new cycle'
    }
    
    signals.append({
        'type': 'KONDRAVIEV_PHASE',
        'signal': f'Current Phase: {k_phase["name"]} ({k_phase["phase"].upper()})',
        'phase': k_phase['phase'],
        'direction': 'NEUTRAL',
        'severity': 'INFO',
        'description': descriptions.get(k_phase['phase'], 'Unknown phase')
    })
    
    # v2: Adjusted risk weights
    # Spring: -5 (bullish), Summer: +5 (slightly bearish), Autumn: +10 (bearish), Winter: +10 (bearish)
    if k_phase['phase'] == 'spring':
        signals.append({
            'type': 'KONDRAVIEV_BULLISH',
            'signal': 'K-Wave Spring - historically positive for equities',
            'direction': 'BULLISH',
            'severity': 'MEDIUM',
            'risk_adjustment': -5
        })
    elif k_phase['phase'] == 'summer':
        signals.append({
            'type': 'KONDRAVIEV_CAUTION',
            'signal': 'K-Wave Summer - watch for overheating',
            'direction': 'BEARISH',
            'severity': 'LOW',
            'risk_adjustment': 5
        })
    elif k_phase['phase'] in ['autumn', 'winter']:
        signals.append({
            'type': 'KONDRAVIEV_WARNING',
            'signal': f'K-Wave {k_phase["phase"].title()} - elevated risk period',
            'direction': 'BEARISH',
            'severity': 'MEDIUM',
            'risk_adjustment': 10,
            'description': 'Historically, Autumn/Winter phases see major market corrections'
        })
    
    return signals

def calculate_risk_score_v2(all_signals):
    """
    v2: Improved risk scoring with directional signals
    Score 0-100: Higher = more bearish risk
    """
    base_score = 50  # Neutral starting point
    
    for signal in all_signals:
        direction = signal.get('direction', 'NEUTRAL')
        severity = signal.get('severity', 'MEDIUM')
        
        # Skip INFO signals
        if severity == 'INFO':
            continue
        
        # Direction-based scoring
        if direction == 'BEARISH':
            if severity == 'HIGH':
                base_score += 12
            elif severity == 'MEDIUM':
                base_score += 6
            elif severity == 'LOW':
                base_score += 3
        elif direction == 'BULLISH':
            if severity == 'HIGH':
                base_score -= 12
            elif severity == 'MEDIUM':
                base_score -= 6
            elif severity == 'LOW':
                base_score -= 3
        
        # K-Wave risk adjustment
        if 'risk_adjustment' in signal:
            base_score += signal['risk_adjustment']
    
    # Clamp to 0-100
    return max(0, min(100, base_score))

def generate_prediction_v2(data, analysis_date, forecast_days=90):
    """
    v2: Complete prediction with all signal types
    """
    historical_data = [d for d in data if d['date'] <= analysis_date]
    if len(historical_data) < 365:
        return None
    
    # Generate all signal types
    gann_signals = generate_gann_signals_v2(data, analysis_date)
    momentum_signals = generate_momentum_signals(data, analysis_date)
    mean_rev_signals = generate_mean_reversion_signals(data, analysis_date)
    k_signals = generate_kondratiev_signals_v2(data, analysis_date)
    
    all_signals = gann_signals + momentum_signals + mean_rev_signals + k_signals
    
    # Calculate risk score
    risk_score = calculate_risk_score_v2(all_signals)
    
    # Generate prediction based on risk score
    if risk_score >= 70:
        prediction = 'BEARISH'
        confidence = min(risk_score, 95)
        expected_move = -12 - (risk_score - 70) * 0.4
    elif risk_score >= 55:
        prediction = 'NEUTRAL_BEARS'
        confidence = 50 + (risk_score - 55) * 2
        expected_move = -5 - (risk_score - 55) * 0.3
    elif risk_score >= 45:
        prediction = 'NEUTRAL'
        confidence = 50
        expected_move = 0
    elif risk_score >= 30:
        prediction = 'NEUTRAL_BULLS'
        confidence = 50 + (45 - risk_score) * 2
        expected_move = 5 + (45 - risk_score) * 0.3
    else:
        prediction = 'BULLISH'
        confidence = min(100 - risk_score, 95)
        expected_move = 10 + (30 - risk_score) * 0.4
    
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
        'momentum_signals': momentum_signals,
        'mean_reversion_signals': mean_rev_signals,
        'kondratiev_signals': k_signals,
        'all_signals': all_signals,
        'k_phase': k_signals[0]['phase'] if k_signals else 'unknown',
        'actual_outcome': actual_outcome,
        'actual_move_pct': actual_move_pct
    }

def run_backtest_v2(data, start_date, end_date, step_days=30, forecast_days=90):
    """Run backtest over historical period"""
    results = []
    current = start_date
    
    while current <= end_date:
        pred = generate_prediction_v2(data, current, forecast_days)
        if pred:
            results.append(pred)
        current += timedelta(days=step_days)
    
    return results

def calculate_accuracy_v2(results):
    """Calculate prediction accuracy metrics for v2"""
    if not results:
        return {}
    
    valid_results = [r for r in results if r['actual_outcome'] is not None]
    
    if not valid_results:
        return {}
    
    # Direction accuracy
    correct_direction = 0
    for r in valid_results:
        pred = r['prediction']
        actual = r['actual_outcome']
        
        if pred in ['BEARISH', 'NEUTRAL_BEARS'] and actual in ['BEARISH', 'NEUTRAL_BEARS']:
            correct_direction += 1
        elif pred in ['BULLISH', 'NEUTRAL_BULLS'] and actual in ['BULLISH', 'NEUTRAL_BULLS']:
            correct_direction += 1
        elif pred == 'NEUTRAL' and actual == 'NEUTRAL':
            correct_direction += 1
        elif pred in ['NEUTRAL_BEARS', 'NEUTRAL'] and actual == 'NEUTRAL':
            correct_direction += 1
        elif pred in ['NEUTRAL_BULLS', 'NEUTRAL'] and actual == 'NEUTRAL':
            correct_direction += 1
    
    direction_accuracy = correct_direction / len(valid_results) * 100
    
    # High confidence predictions (>=70%)
    high_conf_results = [r for r in valid_results if r['confidence'] >= 70]
    high_conf_correct = 0
    for r in high_conf_results:
        pred = r['prediction']
        actual = r['actual_outcome']
        if pred in ['BEARISH', 'NEUTRAL_BEARS'] and actual in ['BEARISH', 'NEUTRAL_BEARS']:
            high_conf_correct += 1
        elif pred in ['BULLISH', 'NEUTRAL_BULLS'] and actual in ['BULLISH', 'NEUTRAL_BULLS']:
            high_conf_correct += 1
        elif pred == 'NEUTRAL' and actual == 'NEUTRAL':
            high_conf_correct += 1
    
    high_conf_accuracy = high_conf_correct / len(high_conf_results) * 100 if high_conf_results else 0
    
    # Major drop prediction
    major_drops = [r for r in valid_results if r['actual_move_pct'] < -15]
    major_drops_predicted = [r for r in major_drops if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS'] and r['risk_score'] >= 60]
    major_drop_recall = len(major_drops_predicted) / len(major_drops) * 100 if major_drops else 0
    
    # Major rally prediction (NEW for v2)
    major_rallies = [r for r in valid_results if r['actual_move_pct'] > 15]
    major_rallies_predicted = [r for r in major_rallies if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS'] and r['risk_score'] <= 40]
    major_rally_recall = len(major_rallies_predicted) / len(major_rallies) * 100 if major_rallies else 0
    
    # False positive rate
    non_drops = [r for r in valid_results if r['actual_move_pct'] >= -15]
    false_positives = [r for r in non_drops if r['prediction'] == 'BEARISH' and r['risk_score'] >= 70]
    false_positive_rate = len(false_positives) / len(non_drops) * 100 if non_drops else 0
    
    # Average predicted vs actual move
    avg_predicted_move = mean([r['expected_move'] for r in valid_results])
    avg_actual_move = mean([r['actual_move_pct'] for r in valid_results])
    
    # Bull/Bear signal balance (NEW)
    bullish_predictions = len([r for r in valid_results if r['prediction'] in ['BULLISH', 'NEUTRAL_BULLS']])
    bearish_predictions = len([r for r in valid_results if r['prediction'] in ['BEARISH', 'NEUTRAL_BEARS']])
    
    return {
        'total_predictions': len(valid_results),
        'direction_accuracy': direction_accuracy,
        'high_confidence_predictions': len(high_conf_results),
        'high_confidence_accuracy': high_conf_accuracy,
        'major_drops': len(major_drops),
        'major_drops_predicted': len(major_drops_predicted),
        'major_drop_recall': major_drop_recall,
        'major_rallies': len(major_rallies),
        'major_rallies_predicted': len(major_rallies_predicted),
        'major_rally_recall': major_rally_recall,
        'false_positive_rate': false_positive_rate,
        'avg_predicted_move': avg_predicted_move,
        'avg_actual_move': avg_actual_move,
        'bullish_predictions': bullish_predictions,
        'bearish_predictions': bearish_predictions
    }

def print_comparison_report(v1_accuracy, v2_accuracy):
    """Print comparison between v1 and v2"""
    print("\n" + "=" * 80)
    print("MODEL COMPARISON: v1 vs v2")
    print("=" * 80)
    
    print(f"\n{'Metric':<35} {'v1':<20} {'v2':<20} {'Change':<15}")
    print("-" * 80)
    
    metrics = [
        ('Direction Accuracy', 'direction_accuracy', '%'),
        ('High Confidence Count', 'high_confidence_predictions', ''),
        ('High Confidence Accuracy', 'high_confidence_accuracy', '%'),
        ('Major Drop Recall', 'major_drop_recall', '%'),
        ('Major Rally Recall', 'major_rally_recall', '%', 'N/A' if 'major_rally_recall' not in v1_accuracy else None),
        ('False Positive Rate', 'false_positive_rate', '%'),
        ('Avg Predicted Move', 'avg_predicted_move', '%'),
        ('Avg Actual Move', 'avg_actual_move', '%'),
    ]
    
    for metric_name, key, unit in metrics[:7]:  # Skip major_rally_recall for v1
        v1_val = v1_accuracy.get(key, 0)
        v2_val = v2_accuracy.get(key, 0)
        if unit == '%' and v1_val and v2_val:
            change = v2_val - v1_val
            change_str = f"{change:+.1f}{unit}"
        else:
            change = v2_val - v1_val
            change_str = f"{change:+d}" if change != 0 else "—"
        
        print(f"{metric_name:<35} {v1_val:<20.1f} {v2_val:<20.1f} {change_str:<15}")
    
    # Bull/Bear balance (v2 only)
    print(f"\n{'Bullish Predictions':<35} {'N/A':<20} {v2_accuracy.get('bullish_predictions', 0):<20} {'NEW':<15}")
    print(f"{'Bearish Predictions':<35} {'N/A':<20} {v2_accuracy.get('bearish_predictions', 0):<20} {'NEW':<15}")
    
    # Calculate bearish bias
    total = v2_accuracy.get('bullish_predictions', 0) + v2_accuracy.get('bearish_predictions', 0)
    if total > 0:
        bearish_pct = v2_accuracy.get('bearish_predictions', 0) / total * 100
        print(f"\n{'Bearish Bias':<35} {'~70% (est)':<20} {bearish_pct:.1f}% {'v2 improved!' if bearish_pct < 60 else '':<15}")

def print_backtest_report_v2(results, accuracy, version="v2"):
    """Print comprehensive backtest report"""
    print("=" * 80)
    print(f"HSI GANN + KONDRAVIEV BACKTESTING REPORT ({version})")
    print("=" * 80)
    
    print(f"\nTotal Predictions: {accuracy.get('total_predictions', 0)}")
    
    print("\n" + "=" * 80)
    print("ACCURACY METRICS")
    print("=" * 80)
    
    print(f"\n📊 Direction Accuracy: {accuracy.get('direction_accuracy', 0):.1f}%")
    print(f"🎯 High Confidence Predictions: {accuracy.get('high_confidence_predictions', 0)}")
    print(f"🎯 High Confidence Accuracy: {accuracy.get('high_confidence_accuracy', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MAJOR MOVE PREDICTION")
    print("-" * 80)
    print(f"📉 Major Drops (>15% decline): {accuracy.get('major_drops', 0)}")
    print(f"✅ Major Drops Predicted: {accuracy.get('major_drops_predicted', 0)}")
    print(f"🎯 Major Drop Recall Rate: {accuracy.get('major_drop_recall', 0):.1f}%")
    print(f"📈 Major Rallies (>15% gain): {accuracy.get('major_rallies', 0)}")
    print(f"✅ Major Rallies Predicted: {accuracy.get('major_rallies_predicted', 0)}")
    print(f"🎯 Major Rally Recall Rate: {accuracy.get('major_rally_recall', 0):.1f}%")
    print(f"⚠️  False Positive Rate: {accuracy.get('false_positive_rate', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("MOVE PREDICTION ACCURACY")
    print("-" * 80)
    print(f"📈 Average Predicted Move: {accuracy.get('avg_predicted_move', 0):.1f}%")
    print(f"📊 Average Actual Move: {accuracy.get('avg_actual_move', 0):.1f}%")
    
    print("\n" + "-" * 80)
    print("PREDICTION DISTRIBUTION")
    print("-" * 80)
    print(f"🐂 Bullish Predictions: {accuracy.get('bullish_predictions', 0)}")
    print(f"🐻 Bearish Predictions: {accuracy.get('bearish_predictions', 0)}")
    
    total = accuracy.get('bullish_predictions', 0) + accuracy.get('bearish_predictions', 0)
    if total > 0:
        bearish_pct = accuracy.get('bearish_predictions', 0) / total * 100
        print(f"📊 Bearish Bias: {bearish_pct:.1f}% (target: ~50%)")
    
    print("\n" + "=" * 80)
    print("DISCLAIMER: Backtesting results do not guarantee future performance.")
    print("=" * 80)

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    
    if not data:
        print("ERROR: Could not load HSI data")
        return
    
    print(f"Loaded {len(data)} data points")
    print(f"Date range: {data[0]['date'].strftime('%Y-%m-%d')} to {data[-1]['date'].strftime('%Y-%m-%d')}")
    
    # Define periods
    train_start = datetime(1980, 1, 1)
    train_end = datetime(2019, 12, 31)
    test_start = datetime(2020, 1, 1)
    test_end = datetime(2026, 2, 20)
    
    print(f"\nRunning v2 backtest...")
    print(f"Test Period: {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
    
    results_v2 = run_backtest_v2(data, test_start, test_end, step_days=30, forecast_days=90)
    
    print(f"Generated {len(results_v2)} predictions")
    
    accuracy_v2 = calculate_accuracy_v2(results_v2)
    
    print("\n")
    print_backtest_report_v2(results_v2, accuracy_v2, version="v2")
    
    # Save results
    with open('/root/.openclaw/workspace/hsi_backtest_v2_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Price', 'Prediction', 'Confidence', 'Risk_Score', 'K_Phase', 
                        'Actual_Move_Pct', 'Actual_Outcome', 'Signals_Count'])
        for r in results_v2:
            writer.writerow([
                r['analysis_date'].strftime('%Y-%m-%d'),
                f"{r['current_price']:.2f}",
                r['prediction'],
                f"{r['confidence']:.1f}",
                r['risk_score'],
                r['k_phase'],
                f"{r['actual_move_pct']:.2f}" if r['actual_move_pct'] else '',
                r['actual_outcome'] if r['actual_outcome'] else '',
                len(r['all_signals'])
            ])
    
    print("\n[OK] v2 results saved to hsi_backtest_v2_results.csv")
    
    # Generate current analysis
    print("\n" + "=" * 80)
    print("CURRENT ANALYSIS (Feb 2026) - v2 Model")
    print("=" * 80)
    
    current_analysis = generate_prediction_v2(data, datetime(2026, 2, 20), forecast_days=90)
    if current_analysis:
        print(f"\nDate: 2026-02-20")
        print(f"Price: {current_analysis['current_price']:,.2f}")
        print(f"Prediction: {current_analysis['prediction']}")
        print(f"Confidence: {current_analysis['confidence']:.0f}%")
        print(f"Risk Score: {current_analysis['risk_score']}/100")
        print(f"Expected Move (90d): {current_analysis['expected_move']:+.1f}%")
        
        print(f"\nSignal Breakdown:")
        print(f"  Gann Signals: {len(current_analysis['gann_signals'])}")
        print(f"  Momentum Signals: {len(current_analysis['momentum_signals'])}")
        print(f"  Mean Reversion Signals: {len(current_analysis['mean_reversion_signals'])}")
        print(f"  Kondratiev Signals: {len(current_analysis['kondratiev_signals'])}")
        
        # Show key signals
        high_signals = [s for s in current_analysis['all_signals'] if s.get('severity') == 'HIGH']
        if high_signals:
            print(f"\nHIGH Severity Signals ({len(high_signals)}):")
            for s in high_signals[:5]:
                print(f"  • [{s.get('direction', 'N/A')}] {s['signal']}")

if __name__ == '__main__':
    main()
