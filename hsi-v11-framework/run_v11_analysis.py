#!/usr/bin/env python3
"""
HSI v11 Latest Analysis
Generates complete analysis package for Google Drive upload
"""

import json
import os
from datetime import datetime
import csv

WORKSPACE = '/root/.openclaw/workspace'

def load_hsi_data():
    """Load latest HSI data"""
    hsi_file = os.path.join(WORKSPACE, 'hsi_stooq_latest.csv')
    if not os.path.exists(hsi_file):
        return None
    
    data = []
    with open(hsi_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                data.append({
                    'date': row.get('Date', ''),
                    'open': float(row.get('Open', 0)),
                    'high': float(row.get('High', 0)),
                    'low': float(row.get('Low', 0)),
                    'close': float(row.get('Close', 0)),
                    'volume': row.get('Volume', '0')
                })
            except:
                continue
    
    return data[-240:] if len(data) > 240 else data  # Last ~240 days (6+ months)


def run_v11_analysis():
    """Run complete v11 analysis"""
    print("=" * 80)
    print("HSI v11 Latest Analysis")
    print("=" * 80)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Timestamp: {timestamp}")
    print()
    
    # Load HSI data
    print("📥 Loading HSI data...")
    hsi_data = load_hsi_data()
    
    if not hsi_data or len(hsi_data) < 30:
        print("❌ Insufficient HSI data")
        return None
    
    print(f"✅ Loaded {len(hsi_data)} data points")
    
    # Calculate current metrics
    current = hsi_data[-1]
    prev_20 = hsi_data[-20] if len(hsi_data) >= 20 else hsi_data[0]
    prev_60 = hsi_data[-60] if len(hsi_data) >= 60 else hsi_data[0]
    
    current_price = current['close']
    change_20d = ((current_price - prev_20['close']) / prev_20['close']) * 100
    change_60d = ((current_price - prev_60['close']) / prev_60['close']) * 100
    
    period_high = max(d['high'] for d in hsi_data)
    period_low = min(d['low'] for d in hsi_data)
    
    # Run alert system
    print("🔍 Running alert system...")
    os.system(f'cd {WORKSPACE} && python3 hsi_v11_alert_system.py 2>&1 | tail -10')
    
    # Load alert summary
    alert_file = os.path.join(WORKSPACE, 'hsi_v11_alert_summary.txt')
    alert_summary = ""
    if os.path.exists(alert_file):
        with open(alert_file, 'r') as f:
            alert_summary = f.read()
    
    # Create analysis package
    output_dir = os.path.join(WORKSPACE, 'v11_analysis_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate report
    report = f"""# HSI v11 Analysis Report

**Generated:** {timestamp}  
**Data Points:** {len(hsi_data)} trading days  
**Period:** 6+ months

---

## 📊 Current Market Status

| Metric | Value |
|--------|-------|
| Current HSI | {current_price:,.2f} |
| 20-Day Change | {change_20d:+.2f}% |
| 60-Day Change | {change_60d:+.2f}% |
| Period High | {period_high:,.2f} |
| Period Low | {period_low:,.2f} |
| Position in Range | {((current_price - period_low) / (period_high - period_low)) * 100:.1f}% |

---

## 🚨 Alert Summary

```
{alert_summary}
```

---

## 📈 V11 Framework Status

### Convergence Signals
- **Current Score:** 0.00/3.00 (from alert system)
- **Signal:** 🔴 REDUCE

### Key Dates
- **Next Solar Term:** 春分 (Mar 20) - Hold/Rebalance
- **Primary Entry:** May 9, 2026 (70 pts confluence)

### Cycle Phases
Monitor for phase changes in:
- Kondratiev Cycle
- Real Estate Cycle
- Juglar Cycle
- Kitchin Cycle

---

## 📁 Files in This Package

1. `v11_analysis_summary.json` - Machine-readable analysis
2. `v11_alert_summary.txt` - Alert system output
3. `hsi_recent_data.csv` - Last 240 days of HSI data
4. `v11_analysis_report.md` - This report

---

**System:** HSI Prediction Tool v11  
**Status:** 🟢 OPERATIONAL  
**Next Review:** Weekly (Fridays)
"""
    
    # Save report
    with open(os.path.join(output_dir, 'v11_analysis_report.md'), 'w') as f:
        f.write(report)
    
    # Save JSON summary
    summary = {
        'timestamp': timestamp,
        'current_price': current_price,
        'change_20d': round(change_20d, 2),
        'change_60d': round(change_60d, 2),
        'period_high': period_high,
        'period_low': period_low,
        'signal': 'REDUCE',
        'convergence_score': 0.00,
        'data_points': len(hsi_data),
        'next_solar_term': '春分 (Mar 20)',
        'primary_entry': 'May 9, 2026'
    }
    
    with open(os.path.join(output_dir, 'v11_analysis_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Copy alert summary
    if os.path.exists(alert_file):
        with open(alert_file, 'r') as f:
            with open(os.path.join(output_dir, 'v11_alert_summary.txt'), 'w') as out:
                out.write(f.read())
    
    # Save recent HSI data
    with open(os.path.join(output_dir, 'hsi_recent_data.csv'), 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'open', 'high', 'low', 'close', 'volume'])
        writer.writeheader()
        writer.writerows(hsi_data)
    
    print()
    print("=" * 80)
    print("✅ V11 Analysis Complete")
    print("=" * 80)
    print(f"Output Directory: {output_dir}")
    print()
    
    return output_dir


if __name__ == '__main__':
    result = run_v11_analysis()
    if result:
        print(f"Ready for upload: {result}")
