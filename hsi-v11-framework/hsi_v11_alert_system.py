#!/usr/bin/env python3
"""
HSI v11 - Automated Alert System
Monitors cycle indicators and sends alerts when thresholds are crossed
Integrates with weekly cron job for automated monitoring
"""

import csv
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Alert configuration
ALERT_CONFIG = {
    'convergence_threshold_high': 2.5,    # 🟢 ACCUMULATE
    'convergence_threshold_low': 1.5,     # 🟡 HOLD / 🔴 REDUCE
    'cycle_phase_change': True,            # Alert on any cycle phase change
    'solar_term_approaching_days': 7,      # Alert N days before solar term
    'price_target_approach_pct': 0.10,     # Alert when within 10% of target
    'sector_deviation_threshold': 0.05,    # Alert if sector deviates >5% from target
}

# Storage for alert history
ALERT_HISTORY_FILE = 'hsi_v11_alert_history.json'
LAST_CHECK_FILE = 'hsi_v11_last_check.json'

def load_json_file(filepath, default=None):
    """Load JSON file or return default"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default if default else {}

def save_json_file(filepath, data):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def read_csv_file(filepath):
    """Read CSV file and return list of dicts"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except:
        return []

def check_convergence_signal():
    """Check signal convergence score and generate alert"""
    alerts = []
    
    data = read_csv_file('hsi_v11_convergence_history.csv')
    if not data:
        return alerts
    
    # Get latest reading
    latest = data[0] if data else {}
    try:
        score = float(latest.get('Total Score', '0').replace(',', ''))
    except:
        score = 0
    
    # Determine signal
    if score >= ALERT_CONFIG['convergence_threshold_high']:
        signal = '🟢 ACCUMULATE'
        priority = 'HIGH'
    elif score >= ALERT_CONFIG['convergence_threshold_low']:
        signal = '🟡 HOLD'
        priority = 'MEDIUM'
    else:
        signal = '🔴 REDUCE'
        priority = 'HIGH'
    
    # Check if signal changed from last check
    last_check = load_json_file(LAST_CHECK_FILE, {})
    last_signal = last_check.get('convergence_signal', '')
    
    if signal != last_signal:
        alerts.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'SIGNAL_CHANGE',
            'priority': priority,
            'title': f'Signal Changed: {last_signal or "N/A"} → {signal}',
            'message': f'Convergence score: {score:.2f}/3.00. Action required: {signal}',
            'action': 'Review portfolio positioning' if signal != '🟡 HOLD' else 'Maintain current position'
        })
    
    return alerts

def check_cycle_phases():
    """Check for cycle phase changes"""
    alerts = []
    
    data = read_csv_file('hsi_v11_cycle_tracker.csv')
    if not data:
        return alerts
    
    last_check = load_json_file(LAST_CHECK_FILE, {})
    last_phases = last_check.get('cycle_phases', {})
    
    for row in data:
        if 'Cycle' not in row or 'Current Phase' not in row:
            continue
        
        cycle_name = row.get('Cycle', '')
        current_phase = row.get('Current Phase', '')
        
        if not cycle_name or not current_phase:
            continue
        
        # Check if phase changed
        if cycle_name in last_phases and last_phases[cycle_name] != current_phase:
            alerts.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'CYCLE_PHASE_CHANGE',
                'priority': 'HIGH',
                'title': f'Cycle Phase Change: {cycle_name}',
                'message': f'Phase changed from "{last_phases[cycle_name]}" to "{current_phase}"',
                'action': 'Review sector allocation and positioning strategy'
            })
    
    return alerts

def check_solar_terms():
    """Check for approaching solar terms"""
    alerts = []
    
    data = read_csv_file('hsi_v11_solar_calendar_2026.csv')
    if not data:
        return alerts
    
    today = datetime.now().date()
    
    for row in data:
        date_str = row.get('Date', '')
        if not date_str or date_str == 'Date':
            continue
        
        try:
            solar_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            continue
        
        days_until = (solar_date - today).days
        
        # Alert if within threshold days and not passed
        if 0 <= days_until <= ALERT_CONFIG['solar_term_approaching_days']:
            solar_term = row.get('Solar Term', '')
            chinese = row.get('Chinese', '')
            action = row.get('Action', '')
            signal = row.get('Signal', '')
            
            if days_until == 0:
                alerts.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'SOLAR_TERM_TODAY',
                    'priority': 'HIGH',
                    'title': f'📅 Solar Term TODAY: {solar_term} ({chinese})',
                    'message': f'Signal: {signal} | Recommended Action: {action}',
                    'action': action
                })
            else:
                alerts.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'SOLAR_TERM_APPROACHING',
                    'priority': 'MEDIUM',
                    'title': f'📅 Solar Term in {days_until} days: {solar_term}',
                    'message': f'Date: {date_str} | Signal: {signal} | Action: {action}',
                    'action': f'Prepare for {action.lower()}'
                })
    
    return alerts

def check_sector_allocation():
    """Check for sector allocation deviations"""
    alerts = []
    
    data = read_csv_file('hsi_v11_sector_allocation.csv')
    if not data:
        return alerts
    
    for row in data:
        if 'Sector' not in row or row.get('Sector') == 'Sector':
            continue
        
        try:
            target = float(row.get('Target %', '0').replace('%', ''))
            current = float(row.get('Current %', '0').replace('%', ''))
        except:
            continue
        
        deviation = abs(current - target)
        
        if deviation > ALERT_CONFIG['sector_deviation_threshold'] * 100:
            sector = row.get('Sector', '')
            signal = row.get('Signal', '')
            action_needed = row.get('Action Needed', '')
            
            alerts.append({
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': 'SECTOR_DEVIATION',
                'priority': 'MEDIUM',
                'title': f'⚖️ Sector Deviation: {sector}',
                'message': f'Target: {target:.1f}% | Current: {current:.1f}% | Deviation: {deviation:.1f}%',
                'action': action_needed
            })
    
    return alerts

def check_v10_windows():
    """Check for V10 high-confluence windows"""
    alerts = []
    
    data = read_csv_file('hsi_v11_v10_integration.csv')
    if not data:
        return alerts
    
    today = datetime.now().date()
    
    for row in data:
        window_date = row.get('Window Date', '')
        if not window_date or window_date == 'Window Date':
            continue
        
        try:
            w_date = datetime.strptime(window_date, '%Y-%m-%d').date()
        except:
            continue
        
        days_until = (w_date - today).days
        confluence = row.get('Confluence Pts', '')
        tier = row.get('Tier', '')
        action = row.get('Combined Action', '')
        
        # Alert for high-confluence windows
        if days_until <= 14 and days_until >= 0 and int(confluence.replace(' pts', '') if confluence else 0) >= 70:
            if days_until == 0:
                alerts.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'V10_WINDOW_TODAY',
                    'priority': 'HIGH',
                    'title': f'🎯 V10 High-Confluence Window TODAY!',
                    'message': f'Date: {window_date} | Confluence: {confluence} pts | Tier: {tier}',
                    'action': action
                })
            elif days_until <= 7:
                alerts.append({
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'type': 'V10_WINDOW_APPROACHING',
                    'priority': 'HIGH',
                    'title': f'🎯 V10 Window in {days_until} days ({confluence} pts)',
                    'message': f'Date: {window_date} | Tier: {tier} | Action: {action}',
                    'action': f'Prepare for {action.lower()}'
                })
    
    return alerts

def run_alert_check():
    """Main function to run all alert checks"""
    print("🔍 Running HSI v11 Alert Check...")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    all_alerts = []
    
    # Run all checks
    print("Checking convergence signal...")
    all_alerts.extend(check_convergence_signal())
    
    print("Checking cycle phases...")
    all_alerts.extend(check_cycle_phases())
    
    print("Checking solar terms...")
    all_alerts.extend(check_solar_terms())
    
    print("Checking sector allocation...")
    all_alerts.extend(check_sector_allocation())
    
    print("Checking V10 windows...")
    all_alerts.extend(check_v10_windows())
    
    # Sort by priority
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    all_alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    # Save alert history
    history = load_json_file(ALERT_HISTORY_FILE, {'alerts': []})
    history['alerts'].extend(all_alerts)
    
    # Keep only last 100 alerts
    history['alerts'] = history['alerts'][-100:]
    history['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_json_file(ALERT_HISTORY_FILE, history)
    
    # Update last check file
    last_check = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'convergence_signal': all_alerts[0]['title'] if all_alerts and 'Signal Changed' in all_alerts[0]['title'] else '',
        'cycle_phases': {}  # Would need to track this properly
    }
    save_json_file(LAST_CHECK_FILE, last_check)
    
    # Output results
    print()
    if all_alerts:
        print(f"🚨 {len(all_alerts)} Alert(s) Generated:")
        print("=" * 80)
        for alert in all_alerts:
            print(f"[{alert['priority']}] {alert['title']}")
            print(f"   {alert['message']}")
            print(f"   → Action: {alert['action']}")
            print()
    else:
        print("✅ No alerts - All systems normal")
    
    # Generate alert summary file
    summary_file = 'hsi_v11_alert_summary.txt'
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"HSI v11 Alert Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write("=" * 80 + "\n\n")
        
        if all_alerts:
            f.write(f"Total Alerts: {len(all_alerts)}\n\n")
            for alert in all_alerts:
                f.write(f"[{alert['priority']}] {alert['title']}\n")
                f.write(f"   {alert['message']}\n")
                f.write(f"   → Action: {alert['action']}\n\n")
        else:
            f.write("✅ No alerts - All systems normal\n")
    
    print(f"📄 Alert summary saved: {summary_file}")
    
    return all_alerts

if __name__ == '__main__':
    alerts = run_alert_check()
    
    # Exit code for cron job (1 if high priority alerts, 0 otherwise)
    high_priority = sum(1 for a in alerts if a['priority'] == 'HIGH')
    exit(1 if high_priority > 0 else 0)
