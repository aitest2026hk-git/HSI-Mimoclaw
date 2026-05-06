#!/usr/bin/env python3
"""
HSI Analysis Tool - Gann Theory + Kondratiev Wave Theory
Analyzes Hang Seng Index for potential peak/big drop predictions
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
    """Parse HSI CSV data (Chinese headers)"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    
    lines = content.strip().split('\n')
    if not lines:
        return data
    
    # Skip header line
    for line in lines[1:]:
        try:
            # Use csv reader to properly handle quoted fields
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
                
            # Parse date (M/D/YYYY format)
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
        except (ValueError, KeyError, IndexError) as e:
            continue
    
    # Sort by date (oldest first)
    data.sort(key=lambda x: x['date'])
    return data

def find_gann_cycles(data):
    """
    Gann Theory Analysis:
    - Time cycles: 90-day, 180-day, 1-year, 2-year, 3-year, 5-year, 7-year, 10-year, 20-year
    - Price squaring: Look for price/time convergence
    - Anniversary dates: Historical turning points
    """
    if len(data) < 365:
        return []
    
    signals = []
    latest_date = data[-1]['date']
    latest_close = data[-1]['close']
    
    # Gann time cycles (in days)
    gann_cycles = {
        '90-day': 90,
        '180-day': 180,
        '1-year': 365,
        '2-year': 730,
        '3-year': 1095,
        '5-year': 1825,
        '7-year': 2555,
        '10-year': 3650,
        '20-year': 7300
    }
    
    # Find historical major tops (local maxima with significant drops after)
    major_tops = []
    window = 60  # 60-day window
    for i in range(window, len(data) - window):
        current_high = data[i]['high']
        is_top = True
        for j in range(i - window, i + window):
            if j != i and data[j]['high'] > current_high:
                is_top = False
                break
        if is_top:
            # Check if drop after top was significant (>15%)
            peak_price = current_high
            min_after = min(data[i:min(i+180, len(data))], key=lambda x: x['low'])['low']
            drop_pct = (peak_price - min_after) / peak_price * 100
            if drop_pct > 15:
                major_tops.append({'date': data[i]['date'], 'price': peak_price, 'drop_pct': drop_pct})
    
    # Check cycle anniversaries from major tops
    for top in major_tops[-10:]:  # Last 10 major tops
        for cycle_name, cycle_days in gann_cycles.items():
            anniversary = top['date'] + timedelta(days=cycle_days)
            days_from_anniversary = abs((latest_date - anniversary).days)
            
            # If we're within 30 days of a cycle anniversary
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
    
    # Gann Square of 9 - Key price levels
    sqrt_price = math.sqrt(latest_close)
    gann_levels = []
    for offset in range(-4, 5):
        level = (sqrt_price + offset * 0.25) ** 2
        gann_levels.append(level)
    
    # Check if current price is near a Gann level
    for level in gann_levels:
        if abs(latest_close - level) / latest_close < 0.02:  # Within 2%
            signals.append({
                'type': 'GANN_PRICE',
                'signal': f'Price near Gann Square of 9 level: {level:.0f}',
                'current_price': latest_close,
                'gann_level': level,
                'severity': 'MEDIUM'
            })
    
    return signals

def find_kondratiev_signals(data):
    """
    Kondratiev Wave Theory Analysis:
    - Long waves of 50-60 years
    - Phases: Spring (expansion), Summer (inflation/peak), Autumn (stagflation/top), Winter (deflation/crash)
    """
    signals = []
    latest_date = data[-1]['date']
    latest_close = data[-1]['close']
    
    # Kondratiev Wave phases (approximate dates for global economy)
    k_waves = [
        {'name': 'Wave 4 Winter', 'start': datetime(1970, 1, 1), 'end': datetime(1982, 1, 1), 'phase': 'winter'},
        {'name': 'Wave 5 Spring', 'start': datetime(1982, 1, 1), 'end': datetime(1995, 1, 1), 'phase': 'spring'},
        {'name': 'Wave 5 Summer', 'start': datetime(1995, 1, 1), 'end': datetime(2000, 1, 1), 'phase': 'summer'},
        {'name': 'Wave 5 Autumn', 'start': datetime(2000, 1, 1), 'end': datetime(2008, 1, 1), 'phase': 'autumn'},
        {'name': 'Wave 5 Winter', 'start': datetime(2008, 1, 1), 'end': datetime(2020, 1, 1), 'phase': 'winter'},
        {'name': 'Wave 6 Spring', 'start': datetime(2020, 1, 1), 'end': datetime(2035, 1, 1), 'phase': 'spring'},
    ]
    
    # Find current K-Wave phase
    current_wave = None
    for wave in k_waves:
        if wave['start'] <= latest_date <= wave['end']:
            current_wave = wave
            break
    
    if current_wave is None:
        current_wave = k_waves[-1]
    
    signals.append({
        'type': 'KONDRAVIEV_PHASE',
        'signal': f'Current Phase: {current_wave["name"]} ({current_wave["phase"].upper()})',
        'phase': current_wave['phase'],
        'severity': 'INFO',
        'description': get_phase_description(current_wave['phase'])
    })
    
    # Analyze HSI performance in current phase
    phase_start = current_wave['start']
    phase_data = [d for d in data if d['date'] >= phase_start]
    
    if len(phase_data) > 100:
        start_price = phase_data[0]['close']
        current_price = phase_data[-1]['close']
        phase_return = (current_price - start_price) / start_price * 100
        
        returns = [d['change_pct'] for d in phase_data[1:]]
        avg_return = mean(returns) if returns else 0
        vol = stdev(returns) if len(returns) > 1 else 0
        
        signals.append({
            'type': 'KONDRAVIEV_STATS',
            'signal': f'{current_wave["name"]} Performance',
            'phase_return': f'{phase_return:.1f}%',
            'avg_daily_return': f'{avg_return:.3f}%',
            'volatility': f'{vol:.2f}%',
            'severity': 'INFO'
        })
    
    # K-Wave transition warning
    if current_wave['phase'] in ['autumn', 'winter']:
        signals.append({
            'type': 'KONDRAVIEV_WARNING',
            'signal': 'ELEVATED RISK: K-Wave suggests defensive positioning',
            'phase': current_wave['phase'],
            'severity': 'HIGH',
            'description': 'Historically, Autumn/Winter phases see major market corrections'
        })
    
    return signals

def get_phase_description(phase):
    descriptions = {
        'spring': 'Expansion phase - New technologies emerge, growth accelerates, optimism builds',
        'summer': 'Peak growth - Inflation rises, speculation increases, economy overheats',
        'autumn': 'Stagflation - Growth slows, debt peaks, market becomes fragile (TOP FORMATION)',
        'winter': 'Deflation/Crash - Debt liquidation, depression, reset before new cycle'
    }
    return descriptions.get(phase, 'Unknown phase')

def find_technical_signals(data):
    """Additional technical analysis signals"""
    signals = []
    if len(data) < 200:
        return signals
    
    latest = data[-1]
    latest_close = latest['close']
    
    # Moving averages
    ma_50 = mean([d['close'] for d in data[-50:]])
    ma_200 = mean([d['close'] for d in data[-200:]])
    
    if latest_close > ma_50 * 1.15:
        signals.append({
            'type': 'TECHNICAL',
            'signal': 'Price extended >15% above 50-day MA - potential pullback',
            'current_price': latest_close,
            'ma_50': ma_50,
            'severity': 'MEDIUM'
        })
    
    if latest_close < ma_200 * 0.85:
        signals.append({
            'type': 'TECHNICAL',
            'signal': 'Price >15% below 200-day MA - oversold bounce possible',
            'current_price': latest_close,
            'ma_200': ma_200,
            'severity': 'MEDIUM'
        })
    
    recent_20 = data[-20:]
    recent_high = max(d['high'] for d in recent_20)
    recent_low = min(d['low'] for d in recent_20)
    
    if latest_close >= recent_high * 0.99:
        signals.append({
            'type': 'TECHNICAL',
            'signal': 'Price near 20-day high - watch for breakout or reversal',
            'current_price': latest_close,
            'recent_high': recent_high,
            'severity': 'LOW'
        })
    
    recent_volumes = [d['volume'] for d in recent_20 if d['volume'] > 0]
    if recent_volumes:
        avg_volume = mean(recent_volumes)
        if latest['volume'] > avg_volume * 2:
            signals.append({
                'type': 'TECHNICAL',
                'signal': 'Volume spike detected - significant move likely',
                'current_volume': latest['volume'],
                'avg_volume': avg_volume,
                'severity': 'MEDIUM'
            })
    
    return signals

def analyze_peak_drop_risk(data):
    """Combined analysis for 'peak of big drop' prediction"""
    gann_signals = find_gann_cycles(data)
    k_signals = find_kondratiev_signals(data)
    tech_signals = find_technical_signals(data)
    
    all_signals = gann_signals + k_signals + tech_signals
    
    high_count = sum(1 for s in all_signals if s.get('severity') == 'HIGH')
    medium_count = sum(1 for s in all_signals if s.get('severity') == 'MEDIUM')
    
    if high_count >= 3:
        risk_level = 'VERY HIGH'
        risk_score = 85 + high_count * 3
    elif high_count >= 1 or medium_count >= 3:
        risk_level = 'HIGH'
        risk_score = 65 + high_count * 5 + medium_count * 3
    elif medium_count >= 1:
        risk_level = 'MODERATE'
        risk_score = 40 + medium_count * 5
    else:
        risk_level = 'LOW'
        risk_score = 20
    
    return {
        'risk_level': risk_level,
        'risk_score': min(risk_score, 100),
        'signals': all_signals,
        'gann_signals': gann_signals,
        'kondratiev_signals': k_signals,
        'technical_signals': tech_signals
    }

def print_report(data, analysis):
    """Print formatted analysis report"""
    latest = data[-1]
    
    print("=" * 70)
    print("HSI HANG SENG INDEX - GANN + KONDRAVIEV WAVE ANALYSIS")
    print("=" * 70)
    print(f"\nAnalysis Date: {latest['date'].strftime('%Y-%m-%d')}")
    print(f"Current Close: {latest['close']:,.2f}")
    print(f"Daily Change: {latest['change_pct']:+.2f}%")
    print(f"Data Range: {data[0]['date'].strftime('%Y-%m-%d')} to {latest['date'].strftime('%Y-%m-%d')}")
    print(f"Total Data Points: {len(data):,}")
    
    print("\n" + "=" * 70)
    print("RISK ASSESSMENT: PEAK OF BIG DROP")
    print("=" * 70)
    print(f"\n*** RISK LEVEL: {analysis['risk_level']}")
    print(f"*** RISK SCORE: {analysis['risk_score']}/100")
    
    print("\n" + "-" * 70)
    print("KONDRAVIEV WAVE ANALYSIS (Long-term 50-60 year cycles)")
    print("-" * 70)
    for signal in analysis['kondratiev_signals']:
        print(f"\n[{signal['severity']}] {signal['type']}")
        print(f"  -> {signal['signal']}")
        if 'description' in signal:
            print(f"  -> {signal['description']}")
        for k, v in signal.items():
            if k not in ['type', 'signal', 'severity', 'description']:
                print(f"  -> {k}: {v}")
    
    print("\n" + "-" * 70)
    print("GANN THEORY ANALYSIS (Time cycles, Price squaring)")
    print("-" * 70)
    if analysis['gann_signals']:
        for signal in analysis['gann_signals']:
            print(f"\n[{signal['severity']}] {signal['type']}")
            print(f"  -> {signal['signal']}")
            for k, v in signal.items():
                if k not in ['type', 'signal', 'severity']:
                    print(f"  -> {k}: {v}")
    else:
        print("\nNo major Gann cycle signals at this time")
    
    print("\n" + "-" * 70)
    print("TECHNICAL SIGNALS")
    print("-" * 70)
    if analysis['technical_signals']:
        for signal in analysis['technical_signals']:
            print(f"\n[{signal['severity']}] {signal['signal']}")
    else:
        print("\nNo significant technical signals")
    
    print("\n" + "=" * 70)
    print("SUMMARY & RECOMMENDATION")
    print("=" * 70)
    
    if analysis['risk_level'] in ['VERY HIGH', 'HIGH']:
        print("""
*** WARNING: Multiple indicators suggest elevated risk of significant correction

Key Concerns:
- Kondratiev Wave phase suggests caution
- Gann time cycles may be converging
- Technical indicators show overextension

Consider:
- Reducing exposure to high-risk positions
- Setting stop-losses on existing positions
- Building cash reserves for potential buying opportunities
- Avoiding new leveraged long positions
""")
    elif analysis['risk_level'] == 'MODERATE':
        print("""
*** MODERATE RISK: Mixed signals, maintain balanced approach

- Stay diversified
- Monitor key support/resistance levels
- Be prepared to adjust if risk signals increase
""")
    else:
        print("""
*** LOW RISK: No major warning signals at this time

- Normal market conditions
- Continue with standard risk management
- Monitor for changing conditions
""")
    
    print("\n" + "=" * 70)
    print("DISCLAIMER: This analysis is for educational purposes only.")
    print("Not financial advice. Always do your own research.")
    print("=" * 70)

def main():
    print("Loading HSI data...")
    data = parse_hsi_data('/root/.openclaw/workspace/hsi.csv')
    
    if not data:
        print("ERROR: Could not load HSI data")
        return
    
    print(f"Loaded {len(data)} data points")
    print("Running analysis...\n")
    
    analysis = analyze_peak_drop_risk(data)
    print_report(data, analysis)
    
    # Save processed data
    with open('/root/.openclaw/workspace/hsi_processed.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change %'])
        for d in data:
            writer.writerow([
                d['date'].strftime('%m/%d/%Y'),
                f"{d['open']:.2f}",
                f"{d['high']:.2f}",
                f"{d['low']:.2f}",
                f"{d['close']:.2f}",
                f"{d['volume']:.0f}",
                f"{d['change_pct']:.2f}%"
            ])
    
    print("\n[OK] Processed data saved to hsi_processed.csv")

if __name__ == '__main__':
    main()
