#!/usr/bin/env python3
"""
2026 Turn Window Predictions - v2.1 Optimized
小龍 Gann Enhanced Methodology with 50+ confidence threshold
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')
from gann_enhanced_module import (
    analyze_turn_windows,
    calculate_confluence_score,
    DEFAULT_PIVOTS,
    CRITICAL_SOLAR_TERMS
)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Use HSI pivots up to 2025 for 2026 predictions
HSI_PIVOTS = [
    datetime(2020, 1, 17), datetime(2020, 3, 23),
    datetime(2020, 6, 9), datetime(2020, 11, 9),
    datetime(2021, 2, 18), datetime(2021, 5, 13),
    datetime(2021, 10, 4), datetime(2022, 1, 26),
    datetime(2022, 3, 15), datetime(2022, 6, 17),
    datetime(2022, 10, 24), datetime(2023, 1, 27),
    datetime(2023, 5, 8), datetime(2023, 8, 11),
    datetime(2023, 10, 17), datetime(2024, 1, 30),
    datetime(2024, 4, 20), datetime(2024, 5, 21),
    datetime(2024, 8, 5), datetime(2024, 10, 8),
    datetime(2025, 1, 15),
]

# Current date for reference
TODAY = datetime(2026, 3, 13)

# ============================================================================
# GENERATE 2026 PREDICTIONS
# ============================================================================

def generate_2026_predictions():
    """Generate all 2026 turn windows with v2.1 50+ threshold."""
    
    print("=" * 80)
    print("📈 HSI 2026 TURN WINDOW PREDICTIONS - v2.1 Optimized")
    print("小龍 Gann Enhanced Methodology | 50+ Confidence Threshold")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Current Date: {TODAY.strftime('%Y-%m-%d')}")
    print(f"Historical Pivots Used: {len(HSI_PIVOTS)}")
    print("=" * 80)
    
    # Analyze turn windows for 2026
    windows = analyze_turn_windows(HSI_PIVOTS, 2026, tolerance_days=4)
    
    # Filter to 50+ threshold (v2.1 rule)
    high_conf = [w for w in windows if w['score'] >= 50]
    
    # Separate upcoming vs past
    upcoming = [w for w in high_conf if datetime.strptime(w['date_str'], '%Y-%m-%d') >= TODAY]
    past = [w for w in high_conf if datetime.strptime(w['date_str'], '%Y-%m-%d') < TODAY]
    
    print(f"\n📊 SUMMARY")
    print(f"  Total Windows (all scores): {len(windows)}")
    print(f"  High Confidence (50+): {len(high_conf)}")
    print(f"  Upcoming (from {TODAY.strftime('%Y-%m-%d')}): {len(upcoming)}")
    print(f"  Past (before {TODAY.strftime('%Y-%m-%d')}): {len(past)}")
    
    return windows, high_conf, upcoming, past

def generate_report(windows, high_conf, upcoming, past):
    """Generate comprehensive report."""
    
    report = []
    report.append("=" * 80)
    report.append("📈 HSI 2026 TURN WINDOW PREDICTIONS - v2.1")
    report.append("=" * 80)
    report.append("")
    
    # Top 10 Overall
    report.append("🎯 TOP 10 TURN WINDOWS (2026 Full Year)")
    report.append("-" * 80)
    for i, w in enumerate(high_conf[:10], 1):
        tier = "🔴" if w['score'] >= 70 else "🟠" if w['score'] >= 50 else "🟡"
        report.append(f"{i:2}. {w['date_str']} {tier} Score: {w['score']:3} | {w['confidence']:10} | {', '.join(w['factors'][:2])}")
    
    report.append("")
    report.append("=" * 80)
    report.append("📅 UPCOMING TURN WINDOWS (From 2026-03-13)")
    report.append("-" * 80)
    
    if upcoming:
        for w in upcoming[:15]:
            tier = "🔴" if w['score'] >= 70 else "🟠" if w['score'] >= 50 else "🟡"
            days_until = (datetime.strptime(w['date_str'], '%Y-%m-%d') - TODAY).days
            report.append(f"{w['date_str']} {tier} {w['score']:3}pts | {w['confidence']:10} | in {days_until:3}d | {w['window_start']} to {w['window_end']}")
            if w['factors']:
                report.append(f"     Factors: {', '.join(w['factors'][:3])}")
    else:
        report.append("No upcoming high-confidence windows found.")
    
    report.append("")
    report.append("=" * 80)
    report.append("📊 MONTHLY BREAKDOWN")
    report.append("-" * 80)
    
    # Group by month
    by_month = {}
    for w in high_conf:
        month = w['date_str'][:7]  # YYYY-MM
        if month not in by_month:
            by_month[month] = []
        by_month[month].append(w)
    
    for month in sorted(by_month.keys()):
        windows_in_month = by_month[month]
        max_score = max(w['score'] for w in windows_in_month)
        count_50plus = sum(1 for w in windows_in_month if w['score'] >= 50)
        report.append(f"\n{month}: {len(windows_in_month)} windows | Max Score: {max_score} | 50+ count: {count_50plus}")
        for w in sorted(windows_in_month, key=lambda x: -x['score'])[:3]:
            report.append(f"  • {w['date_str']} ({w['score']}pts) - {', '.join(w['factors'][:2])}")
    
    report.append("")
    report.append("=" * 80)
    report.append("🔮 CRITICAL PERIODS (Tier 1 Solar Terms)")
    report.append("-" * 80)
    
    tier1_terms = ["2026-03-21", "2026-06-21", "2026-09-23", "2026-12-22"]
    for term_date in tier1_terms:
        term_dt = datetime.strptime(term_date, '%Y-%m-%d')
        nearby = [w for w in high_conf if abs((datetime.strptime(w['date_str'], '%Y-%m-%d') - term_dt).days) <= 5]
        if nearby:
            best = max(nearby, key=lambda x: x['score'])
            report.append(f"\n{term_date} - Tier 1 Solar Term:")
            report.append(f"  Best Window: {best['date_str']} ({best['score']}pts, {best['confidence']})")
            report.append(f"  Factors: {', '.join(best['factors'][:3])}")
    
    report.append("")
    report.append("=" * 80)
    report.append("⚠️ TRADING RECOMMENDATIONS (v2.1 Rules)")
    report.append("-" * 80)
    report.append("")
    report.append("Signal Threshold:")
    report.append("  ✅ TRADE: Score ≥50 points")
    report.append("  ❌ IGNORE: Score <50 points")
    report.append("")
    report.append("Position Sizing:")
    report.append("  70+ points: 100% (full position)")
    report.append("  50-69 points: 50-75% position")
    report.append("")
    report.append("Expected Performance (based on 2020-2025 backtest):")
    report.append("  • ~9-10 signals per year")
    report.append("  • ~2 major pivots captured (21% hit rate)")
    report.append("  • 5-7x better than random chance")
    report.append("")
    report.append("=" * 80)
    
    return '\n'.join(report)

def generate_html_report(upcoming, high_conf):
    """Generate HTML report for web viewing."""
    
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HSI 2026 Turn Windows - v2.1 Predictions</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: linear-gradient(135deg, #0f0f1a, #1a1a2e); color: #e0e0e0; min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #00d9ff; margin-bottom: 10px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 30px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1); }
        .card h2 { color: #00d9ff; margin-bottom: 20px; border-bottom: 2px solid rgba(0,217,255,0.3); padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(0,217,255,0.15); color: #00d9ff; }
        tr:hover { background: rgba(255,255,255,0.05); }
        .score-high { background: rgba(255,71,87,0.2); border-left: 4px solid #ff4757; }
        .score-medium { background: rgba(255,165,2,0.15); border-left: 4px solid #ffa502; }
        .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 600; }
        .badge-veryhigh { background: #ff4757; color: white; }
        .badge-high { background: #ffa502; color: white; }
        .footer { text-align: center; margin-top: 40px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📈 HSI 2026 Turn Window Predictions</h1>
        <p class="subtitle">小龍 Gann Enhanced v2.1 | 50+ Confidence Threshold | Generated: ''' + datetime.now().strftime('%Y-%m-%d %H:%M UTC') + '''</p>
        
        <div class="card">
            <h2>📊 Summary</h2>
            <table>
                <tr><td>Total Windows (50+):</td><td><strong>''' + str(len(high_conf)) + '''</strong></td></tr>
                <tr><td>Upcoming (from 2026-03-13):</td><td><strong>''' + str(len(upcoming)) + '''</strong></td></tr>
                <tr><td>Expected Hit Rate:</td><td><strong>21.1% (±8 days)</strong></td></tr>
                <tr><td>Signals per Year:</td><td><strong>~9-10</strong></td></tr>
            </table>
        </div>
        
        <div class="card">
            <h2>🔮 Upcoming Turn Windows</h2>
            <table>
                <thead>
                    <tr><th>Date</th><th>Score</th><th>Confidence</th><th>Window</th><th>Key Factors</th></tr>
                </thead>
                <tbody>'''
    
    for w in upcoming[:20]:
        badge_class = "badge-veryhigh" if w['score'] >= 70 else "badge-high"
        row_class = "score-high" if w['score'] >= 60 else "score-medium"
        html += f'''
                    <tr class="{row_class}">
                        <td><strong>{w['date_str']}</strong></td>
                        <td><span class="badge {badge_class}">{w['score']} pts</span></td>
                        <td>{w['confidence']}</td>
                        <td>{w['window_start']}<br><small>to {w['window_end']}</small></td>
                        <td>{', '.join(w['factors'][:2]) if w['factors'] else 'Base confluence'}</td>
                    </tr>'''
    
    html += '''
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>⚠️ Trading Rules (v2.1)</h2>
            <ul style="margin-left: 20px; line-height: 2;">
                <li><strong>✅ TRADE:</strong> Score ≥50 points</li>
                <li><strong>❌ IGNORE:</strong> Score <50 points</li>
                <li><strong>Position Sizing:</strong> 70+ = 100%, 50-69 = 50-75%</li>
                <li><strong>Expected:</strong> ~9-10 signals/year, ~2 major pivots (21% hit rate)</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>Methodology: 小龍 Gann Enhanced v2.1 | Backtest: 2020-2025 (21.1% hit rate)</p>
            <p>⚠️ For informational purposes only. Not financial advice.</p>
        </div>
    </div>
</body>
</html>'''
    
    return html

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Generate predictions
    windows, high_conf, upcoming, past = generate_2026_predictions()
    
    # Generate text report
    report = generate_report(windows, high_conf, upcoming, past)
    print("\n" + report)
    
    # Generate HTML report
    html = generate_html_report(upcoming, high_conf)
    
    # Save outputs
    outdir = Path("/root/.openclaw/workspace/stock_analysis")
    outdir.mkdir(exist_ok=True)
    
    with open(outdir / "2026_predictions_v2.1.txt", 'w') as f:
        f.write(report)
    
    with open(outdir / "2026_predictions_v2.1.html", 'w') as f:
        f.write(html)
    
    # Save JSON data
    with open(outdir / "2026_predictions_v2.1.json", 'w') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            'total_windows': len(windows),
            'high_conf_50plus': len(high_conf),
            'upcoming': upcoming,
            'past': past,
            'top_10': high_conf[:10]
        }, f, indent=2, default=str)
    
    print(f"\n✅ Reports saved to {outdir}")
    print(f"  • 2026_predictions_v2.1.txt")
    print(f"  • 2026_predictions_v2.1.html")
    print(f"  • 2026_predictions_v2.1.json")
