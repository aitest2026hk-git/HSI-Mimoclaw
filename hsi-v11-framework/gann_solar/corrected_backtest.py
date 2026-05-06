#!/usr/bin/env python3
"""
CORRECTED Backtest: Measure % of PIVOTS captured by windows
NOT: % of windows that captured pivots (wrong!)
"""

from datetime import datetime, timedelta
from typing import List, Tuple

# HSI Major Pivots 2015-2025
HSI_PIVOTS = [
    (datetime(2015, 4, 13), 28586, 'high'),
    (datetime(2015, 7, 8), 23239, 'low'),
    (datetime(2015, 10, 9), 25562, 'high'),
    (datetime(2016, 1, 20), 18278, 'low'),
    (datetime(2016, 11, 9), 24234, 'high'),
    (datetime(2017, 1, 19), 23881, 'low'),
    (datetime(2018, 1, 26), 33484, 'high'),
    (datetime(2018, 10, 31), 24888, 'low'),
    (datetime(2019, 1, 3), 24506, 'low'),
    (datetime(2019, 4, 8), 30280, 'high'),
    (datetime(2019, 11, 8), 26276, 'low'),
    (datetime(2020, 1, 17), 28584, 'high'),
    (datetime(2020, 3, 23), 21139, 'low'),
    (datetime(2021, 2, 18), 31183, 'high'),
    (datetime(2021, 10, 4), 23751, 'low'),
    (datetime(2022, 1, 26), 26174, 'high'),
    (datetime(2022, 10, 24), 14687, 'low'),
    (datetime(2023, 1, 27), 22719, 'high'),
    (datetime(2023, 10, 17), 17396, 'low'),
    (datetime(2024, 1, 30), 15541, 'low'),
    (datetime(2024, 4, 20), 16541, 'low'),
    (datetime(2024, 5, 21), 19705, 'high'),
    (datetime(2024, 8, 5), 16157, 'low'),
    (datetime(2024, 10, 8), 23251, 'high'),
    (datetime(2025, 1, 15), 18906, 'low'),
]

import sys
sys.path.append('/root/.openclaw/workspace/gann_solar')
from solar_term_calculator import get_solar_terms_for_year


def generate_solar_term_windows(years: List[int], window_days: int = 4) -> List[Tuple[datetime, datetime, str, int]]:
    """Generate all solar term windows for given years."""
    windows = []
    
    for year in years:
        terms = get_solar_terms_for_year(year)
        for term in terms:
            start = term['date'] - timedelta(days=window_days)
            end = term['date'] + timedelta(days=window_days)
            windows.append((start, end, term['name_cn'], term['tier']))
    
    return windows


def pivot_in_window(pivot_date: datetime, windows: List[Tuple]) -> Tuple[bool, str, int]:
    """Check if a pivot falls within any solar term window."""
    for start, end, term_name, tier in windows:
        if start <= pivot_date <= end:
            return True, term_name, tier
    return False, None, None


def main():
    years = list(range(2015, 2026))
    
    # Generate all solar term windows (±4 days)
    windows = generate_solar_term_windows(years, window_days=4)
    
    print("=" * 80)
    print("CORRECTED BACKTEST: % of PIVOTS captured by solar term windows")
    print("=" * 80)
    print()
    
    # Test each pivot
    total_pivots = len(HSI_PIVOTS)
    pivots_in_window = 0
    tier1_hits = 0
    tier2_hits = 0
    tier3_hits = 0
    
    print("## PIVOT-BY-PIVOT ANALYSIS")
    print("-" * 80)
    print(f"{'Date':<12} | {'Type':<4} | {'In Window?':<10} | {'Solar Term':<15} | {'Tier'}")
    print("-" * 80)
    
    for pivot_date, price, pivot_type in HSI_PIVOTS:
        in_window, term_name, tier = pivot_in_window(pivot_date, windows)
        
        if in_window:
            pivots_in_window += 1
            status = "✓ YES"
            if tier == 1:
                tier1_hits += 1
            elif tier == 2:
                tier2_hits += 1
            else:
                tier3_hits += 1
        else:
            status = "✗ NO"
            term_name = "-"
            tier = "-"
        
        print(f"{pivot_date.strftime('%Y-%m-%d'):<12} | {pivot_type:<4} | {status:<10} | {str(term_name):<15} | {tier}")
    
    print("-" * 80)
    print()
    
    # Calculate rates
    hit_rate = (pivots_in_window / total_pivots * 100)
    
    print("## CORRECTED ACCURACY RESULTS")
    print("-" * 80)
    print(f"Total Major Pivots Tested: {total_pivots}")
    print(f"Pivots Inside Solar Term Windows: {pivots_in_window}")
    print(f"Pivots Outside Windows: {total_pivots - pivots_in_window}")
    print()
    print(f"OVERALL HIT RATE: {hit_rate:.1f}%")
    print()
    print("By Tier:")
    print(f"  Tier 1 (Equinox/Solstice): {tier1_hits} pivots ({tier1_hits/total_pivots*100:.1f}%)")
    print(f"  Tier 2 (Season Start): {tier2_hits} pivots ({tier2_hits/total_pivots*100:.1f}%)")
    print(f"  Tier 3 (Minor): {tier3_hits} pivots ({tier3_hits/total_pivots*100:.1f}%)")
    print()
    
    # Random chance baseline
    # 24 solar terms × 9 days (±4) = 216 days/year in windows
    # 216 / 365 = 59.2% of days are in windows
    random_expectation = 59.2
    edge = hit_rate - random_expectation
    
    print("## STATISTICAL SIGNIFICANCE")
    print("-" * 80)
    print(f"Random Expectation: {random_expectation:.1f}%")
    print(f"  (24 terms × 9 days / 365 days = 59.2% of year in windows)")
    print()
    print(f"Actual Hit Rate: {hit_rate:.1f}%")
    print(f"Edge Over Random: {edge:+.1f} percentage points")
    print()
    
    if edge > 10:
        print("✓ METHODOLOGY SHOWS PREDICTIVE VALUE")
        print("  Hit rate significantly exceeds random chance")
    elif edge > 0:
        print("△ METHODOLOGY SLIGHTLY BETTER THAN RANDOM")
        print("  Hit rate exceeds random chance, but margin is small")
    else:
        print("✗ METHODOLOGY NOT BETTER THAN RANDOM")
        print("  Hit rate at or below random expectation")
    
    print()
    print("=" * 80)
    
    # Show missed pivots
    print()
    print("## PIVOTS MISSED BY WINDOWS (Outside ±4 days)")
    print("-" * 80)
    for pivot_date, price, pivot_type in HSI_PIVOTS:
        in_window, term_name, tier = pivot_in_window(pivot_date, windows)
        if not in_window:
            # Find nearest solar term
            min_distance = 999
            nearest_term = None
            for year in [pivot_date.year - 1, pivot_date.year, pivot_date.year + 1]:
                terms = get_solar_terms_for_year(year)
                for term in terms:
                    distance = abs((pivot_date - term['date']).days)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_term = term['name_cn']
            
            print(f"{pivot_date.strftime('%Y-%m-%d')} ({pivot_type}): {min_distance} days from nearest term ({nearest_term})")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
