#!/usr/bin/env python3
"""
Filtered Backtester - Test confidence threshold impact
Tests different minimum score thresholds to optimize hit rate
"""

import json
from datetime import datetime
from typing import List, Tuple
from pathlib import Path
import sys

sys.path.insert(0, '/root/.openclaw/workspace')
from gann_enhanced_module import analyze_turn_windows, DEFAULT_PIVOTS

# ============================================================================
# HISTORICAL PIVOTS (Same as v2.0 backtest)
# ============================================================================

HSI_PIVOTS = [
    (datetime(2020, 1, 17), 28584, 'high'), (datetime(2020, 3, 23), 21139, 'low'),
    (datetime(2020, 6, 9), 25221, 'high'), (datetime(2020, 11, 9), 26801, 'high'),
    (datetime(2021, 2, 18), 31183, 'high'), (datetime(2021, 5, 13), 28369, 'low'),
    (datetime(2021, 10, 4), 23751, 'low'), (datetime(2022, 1, 26), 26174, 'high'),
    (datetime(2022, 3, 15), 18235, 'low'), (datetime(2022, 6, 17), 22399, 'high'),
    (datetime(2022, 10, 24), 14687, 'low'), (datetime(2023, 1, 27), 22719, 'high'),
    (datetime(2023, 5, 8), 21095, 'high'), (datetime(2023, 8, 11), 19096, 'low'),
    (datetime(2023, 10, 17), 17396, 'low'), (datetime(2024, 1, 30), 15541, 'low'),
    (datetime(2024, 4, 20), 16541, 'low'), (datetime(2024, 5, 21), 19705, 'high'),
    (datetime(2024, 8, 5), 16157, 'low'), (datetime(2024, 10, 8), 23251, 'high'),
    (datetime(2025, 1, 15), 18906, 'low'),
]

# ============================================================================
# FILTERED BACKTEST
# ============================================================================

class FilteredBacktester:
    def __init__(self, pivots: List[Tuple], min_score: int = 60):
        self.pivots = [{'date': p[0], 'price': p[1], 'type': p[2]} for p in pivots]
        self.pivot_dates = [p['date'] for p in self.pivots]
        self.min_score = min_score
    
    def get_filtered_predictions(self, year: int) -> List[dict]:
        hist = [p for p in self.pivot_dates if p.year < year]
        if len(hist) < 3:
            hist = DEFAULT_PIVOTS.get('HSI', [])[:5]
        
        windows = analyze_turn_windows(hist, year, tolerance_days=4)
        
        # FILTER: Only keep windows with score >= min_score
        filtered = [w for w in windows if w['score'] >= self.min_score]
        return filtered
    
    def find_matches(self, preds: List[dict], year: int) -> List[dict]:
        actuals = [p for p in self.pivots if p['date'].year == year]
        matches = []
        
        for p in preds:
            pred_date = datetime.strptime(p['date_str'], '%Y-%m-%d')
            for a in actuals:
                diff = abs((a['date'] - pred_date).days)
                if diff <= 8:
                    matches.append({
                        'predicted': p['date_str'],
                        'actual': a['date'].strftime('%Y-%m-%d'),
                        'price': a['price'],
                        'type': a['type'],
                        'days_diff': diff,
                        'score': p['score'],
                        'hit': diff <= 4
                    })
        return matches
    
    def run(self, start: int = 2020, end: int = 2025) -> dict:
        yearly = []
        all_preds = []
        all_matches = []
        
        for y in range(start, end + 1):
            preds = self.get_filtered_predictions(y)
            matches = self.find_matches(preds, y)
            
            hits4 = sum(1 for m in matches if m['hit'])
            hits8 = sum(1 for m in matches if m['days_diff'] <= 8)
            
            yearly.append({
                'year': y,
                'windows': len(preds),
                'hits_4d': hits4,
                'hits_8d': hits8,
                'rate_4d': round(hits4/len(preds)*100, 1) if preds else 0,
                'rate_8d': round(hits8/len(preds)*100, 1) if preds else 0,
                'avg_score': round(sum(m['score'] for m in matches)/len(matches), 1) if matches else 0
            })
            all_preds.extend(preds)
            all_matches.extend(matches)
        
        total_wins = sum(y['windows'] for y in yearly)
        total_h4 = sum(y['hits_4d'] for y in yearly)
        total_h8 = sum(y['hits_8d'] for y in yearly)
        
        # Unique pivots predicted
        unique_predicted = len(set(m['actual'] for m in all_matches))
        
        return {
            'min_score': self.min_score,
            'period': f'{start}-{end}',
            'total_pivots': len(self.pivots),
            'total_windows': total_wins,
            'total_matches': len(all_matches),
            'unique_pivots_predicted': unique_predicted,
            'pivot_coverage': round(unique_predicted/len(self.pivots)*100, 1),
            'hit_rate_4d': round(total_h4/total_wins*100, 1) if total_wins else 0,
            'hit_rate_8d': round(total_h8/total_wins*100, 1) if total_wins else 0,
            'yearly': yearly,
            'best_year': max(yearly, key=lambda x: x['rate_8d'])['year'],
            'worst_year': min(yearly, key=lambda x: x['rate_8d'])['year']
        }

# ============================================================================
# COMPARE THRESHOLDS
# ============================================================================

def compare_thresholds():
    """Compare different minimum score thresholds."""
    thresholds = [0, 30, 50, 60, 70]
    results = []
    
    print("\n" + "=" * 80)
    print("🔬 CONFIDENCE THRESHOLD COMPARISON")
    print("Testing: HSI 2020-2025 | Different minimum score thresholds")
    print("=" * 80)
    
    for thresh in thresholds:
        print(f"\nRunning threshold: {thresh}+ points...")
        bt = FilteredBacktester(HSI_PIVOTS, min_score=thresh)
        res = bt.run(2020, 2025)
        results.append(res)
        
        print(f"\n📊 Threshold: {thresh}+")
        print(f"  Total Windows: {res['total_windows']}")
        print(f"  Hit Rate (±4d): {res['hit_rate_4d']}%")
        print(f"  Hit Rate (±8d): {res['hit_rate_8d']}%")
        print(f"  Pivots Covered: {res['unique_pivots_predicted']}/{res['total_pivots']} ({res['pivot_coverage']}%)")
        print(f"  Best Year: {res['best_year']}")
    
    # Comparison table
    print("\n" + "=" * 80)
    print("📈 COMPARISON TABLE")
    print("=" * 80)
    print(f"{'Threshold':<12} {'Windows':<10} {'Hit ±4d':<10} {'Hit ±8d':<10} {'Pivots':<12} {'Coverage':<10}")
    print("-" * 80)
    for r in results:
        thresh = f"{r['min_score']}+" if r['min_score'] > 0 else "None (0+)"
        print(f"{thresh:<12} {r['total_windows']:<10} {r['hit_rate_4d']:<10} {r['hit_rate_8d']:<10} {r['unique_pivots_predicted']}/{r['total_pivots']:<8} {r['pivot_coverage']}%")
    print("=" * 80)
    
    # Recommendation
    print("\n✅ RECOMMENDATION")
    best = max(results, key=lambda x: x['hit_rate_8d'] if x['total_windows'] >= 20 else 0)
    print(f"  Best threshold: {best['min_score']}+ points")
    print(f"  Hit rate: {best['hit_rate_8d']}%")
    print(f"  Signals: {best['total_windows']} windows over 6 years")
    print(f"  Trade-off: Higher accuracy but fewer signals")
    
    return results

# ============================================================================
# YEAR BY YEAR WITH 60+ THRESHOLD
# ============================================================================

def detailed_60_threshold():
    """Show detailed year-by-year breakdown with 60+ threshold."""
    print("\n" + "=" * 80)
    print("📅 DETAILED YEAR-BY-YEAR (60+ POINTS THRESHOLD)")
    print("=" * 80)
    
    bt = FilteredBacktester(HSI_PIVOTS, min_score=60)
    res = bt.run(2020, 2025)
    
    print(f"\n{'Year':<6} {'Windows':<10} {'Hits ±4d':<12} {'Hits ±8d':<12} {'Rate 4d':<10} {'Rate 8d':<10} {'Avg Score':<10}")
    print("-" * 80)
    for y in res['yearly']:
        print(f"{y['year']:<6} {y['windows']:<10} {y['hits_4d']:<12} {y['hits_8d']:<12} {y['rate_4d']:<10} {y['rate_8d']:<10} {y['avg_score']:<10}")
    print("-" * 80)
    print(f"{'TOTAL':<6} {res['total_windows']:<10} {sum(y['hits_4d'] for y in res['yearly']):<12} {sum(y['hits_8d'] for y in res['yearly']):<12} {res['hit_rate_4d']:<10} {res['hit_rate_8d']:<10}")
    print("=" * 80)
    
    return res

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Compare all thresholds
    results = compare_thresholds()
    
    # Detailed 60+ breakdown
    res_60 = detailed_60_threshold()
    
    # Save results
    outdir = Path("/root/.openclaw/workspace/backtest_results")
    outdir.mkdir(exist_ok=True)
    
    with open(outdir / "threshold_comparison.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(outdir / "threshold_60plus_detailed.json", 'w') as f:
        json.dump(res_60, f, indent=2)
    
    print(f"\n✅ Results saved to {outdir}")
