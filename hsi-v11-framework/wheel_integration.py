#!/usr/bin/env python3
"""
Wheel of Wheels Integration for Stock Cycling Analyzer
Adds 江恩輪中輪 analysis to the enhanced cycling pipeline.

Usage:
    python3 wheel_integration.py           # Analyze default stocks
    python3 wheel_integration.py HSI 25261 # Analyze specific price
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Import the Wheel of Wheels module
from gann_wheel_of_wheels import (
    wheel_of_wheels_analysis,
    generate_wheel_report,
    multi_wheel_analysis,
    project_turn_dates,
    time_to_degrees,
    price_to_degrees,
    get_position
)

# Import existing modules
from gann_enhanced_module import DEFAULT_PIVOTS

OUTPUT_DIR = Path("/root/.openclaw/workspace/stock_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)


def add_wheel_to_stock_analysis(symbol: str, current_price: float, 
                                 current_date: datetime = None) -> Dict:
    """
    Run Wheel of Wheels analysis for a stock and return structured results
    that can be merged into the main analyzer's output.
    """
    if current_date is None:
        current_date = datetime.now()
    
    pivots = DEFAULT_PIVOTS.get(symbol, DEFAULT_PIVOTS["HSI"])
    
    # Choose wheel size based on price range
    if current_price > 10000:
        wheel_size = 1000  # HSI, major indices
    elif current_price > 1000:
        wheel_size = 100   # Mid-price stocks
    elif current_price > 100:
        wheel_size = 10    # Lower-price stocks
    else:
        wheel_size = 1
    
    result = wheel_of_wheels_analysis(
        symbol=symbol,
        current_price=current_price,
        current_date=current_date,
        pivot_dates=pivots,
        wheel_size=wheel_size
    )
    
    return result


def merge_wheel_into_convergence(convergence: Dict, wheel: Dict) -> Dict:
    """
    Merge Wheel of Wheels score into the existing convergence analysis.
    
    Wheel contributes up to ~60 points to the overall score.
    """
    wheel_score = wheel['total_score']
    # Normalize wheel score to 0-60 range (wheel can go up to ~300)
    wheel_contribution = min(int(wheel_score / 5), 60)
    
    # Add to existing signals
    existing_score = convergence.get('enhanced_gann_score', 0)
    new_score = existing_score + wheel_contribution
    
    # Add wheel signal
    signals = convergence.get('signals', [])
    signals.append((
        "Wheel of Wheels (輪中輪)",
        f"{wheel['signal_strength']} ({wheel_score} pts → +{wheel_contribution})",
        wheel_contribution
    ))
    
    # Update convergence
    convergence['enhanced_gann_score'] = new_score
    convergence['signals'] = signals
    convergence['wheel_analysis'] = {
        'total_score': wheel_score,
        'signal_strength': wheel['signal_strength'],
        'time_degrees': wheel['time_degrees'],
        'price_degrees': wheel['price_degrees'],
        'time_significance': wheel['time_position']['significance'],
        'price_significance': wheel['price_position']['significance'],
        'top_projections': wheel['top_projections']
    }
    
    # Recalculate confidence
    confidence = min(100, int((new_score / 150) * 100))  # Scale to 150 max
    convergence['confidence'] = confidence
    
    return convergence


def generate_wheel_section(wheel: Dict) -> str:
    """Generate a text section for the wheel analysis to insert into reports."""
    lines = []
    lines.append(f"\n🔮 WHEEL OF WHEELS (江恩輪中輪)")
    lines.append(f"   Wheel Size: {wheel['wheel_size']} price units / 360°")
    lines.append(f"   Time on Wheel: {wheel['time_degrees']}° → {wheel['time_position']['significance']} "
                f"(near {wheel['time_position']['nearest_critical']}°)")
    lines.append(f"   Price on Wheel: {wheel['price_degrees']}° → {wheel['price_position']['significance']} "
                f"(near {wheel['price_position']['nearest_critical']}°)")
    lines.append(f"   Combined Score: {wheel['total_score']} ({wheel['signal_strength']})")
    
    if wheel['top_projections']:
        lines.append(f"   Next Wheel Events:")
        for proj in wheel['top_projections'][:3]:
            lines.append(f"     • {proj['projection_date']} ({proj['days_from_now']}d) — {proj['description']}")
    
    lines.append(f"   → {wheel['recommendation'].split(chr(10))[0]}")  # First line only
    
    return "\n".join(lines)


# ============================================================================
# STANDALONE MODE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  江恩輪中輪 WHEEL OF WHEELS — Standalone Analysis")
    print("=" * 70)
    
    if len(sys.argv) >= 3:
        # Custom: symbol price
        symbol = sys.argv[1]
        price = float(sys.argv[2])
        print(f"\nAnalyzing: {symbol} @ {price}")
        result = add_wheel_to_stock_analysis(symbol, price)
        report = generate_wheel_report(result)
        print(report)
    else:
        # Default: HSI + sample stocks
        stocks = {
            "HSI": 25261.0,
            "3690.HK": 150.0,    # Meituan approximate
            "0916.HK": 7.5       # Longyuan approximate
        }
        
        for symbol, price in stocks.items():
            print(f"\n{'─' * 70}")
            print(f"  {symbol} @ {price}")
            print(f"{'─' * 70}")
            
            result = add_wheel_to_stock_analysis(symbol, price)
            
            # Quick summary
            print(f"  Time: {result['time_degrees']}° (near {result['time_position']['nearest_critical']}°, "
                  f"{result['time_position']['significance']})")
            print(f"  Price: {result['price_degrees']}° (near {result['price_position']['nearest_critical']}°, "
                  f"{result['price_position']['significance']})")
            print(f"  Signal: {result['signal_strength']} ({result['total_score']} pts)")
            
            if result['top_projections']:
                print(f"  Next 3 events:")
                for proj in result['top_projections'][:3]:
                    print(f"    {proj['projection_date']} ({proj['days_from_now']}d) — {proj['description']}")
            
            # Save report
            report_path = OUTPUT_DIR / f"{symbol.replace('.', '_')}_wheel_report.txt"
            report = generate_wheel_report(result)
            with open(report_path, 'w') as f:
                f.write(report)
            print(f"  Report saved: {report_path}")
    
    print(f"\n{'=' * 70}")
    print("  Done!")
