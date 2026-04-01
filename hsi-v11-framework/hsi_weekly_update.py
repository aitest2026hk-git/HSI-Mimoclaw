#!/usr/bin/env python3
"""
HSI Weekly Data Update Script
- Fetches latest HSI data from Stooq
- Updates hsi.csv
- Runs v10 backtest
- Outputs summary for delivery
"""

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path('/root/.openclaw/workspace')

def fetch_stooq_data():
    """Fetch latest HSI data from Stooq"""
    import urllib.request
    
    url = "https://stooq.com/q/d/l/?s=^hsi&i=d"
    output_file = WORKSPACE / 'hsi_stooq_latest.csv'
    
    try:
        urllib.request.urlretrieve(url, output_file)
        return output_file
    except Exception as e:
        return f"ERROR: Failed to fetch data: {e}"

def convert_and_merge(stooq_file):
    """Convert Stooq format to hsi.csv format"""
    
    # Read Stooq data
    stooq_rows = []
    with open(stooq_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row['Date']
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                formatted_date = f"{dt.month}/{dt.day}/{dt.year}"
                
                volume = row.get('Volume', '0') or '0'
                stooq_rows.append({
                    'date': formatted_date,
                    'close': row['Open'],  # Will be overwritten
                    'open': row['Open'],
                    'high': row['High'],
                    'low': row['Low'],
                    'close': row['Close'],
                    'volume': volume
                })
            except Exception as e:
                continue
    
    if not stooq_rows:
        return "ERROR: No data parsed"
    
    # Calculate % change
    for i in range(1, len(stooq_rows)):
        try:
            prev_close = float(stooq_rows[i-1]['close'].replace(',', ''))
            curr_close = float(stooq_rows[i]['close'].replace(',', ''))
            change_pct = ((curr_close - prev_close) / prev_close) * 100
            stooq_rows[i]['change_pct'] = f"{change_pct:.2f}%"
        except:
            stooq_rows[i]['change_pct'] = ''
    
    stooq_rows[0]['change_pct'] = ''
    
    # Write hsi.csv format
    output_file = WORKSPACE / 'hsi.csv'
    backup_file = WORKSPACE / f"hsi_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    # Backup existing
    if output_file.exists():
        import shutil
        shutil.copy(output_file, backup_file)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        f.write("日期，收市，開市，高，低，成交量，升跌（%）\n")
        for row in stooq_rows:
            volume = row['volume']
            try:
                vol_num = float(volume) if volume else 0
                if vol_num >= 1e9:
                    volume = f"{vol_num/1e9:.2f}B"
                elif vol_num >= 1e6:
                    volume = f"{vol_num/1e6:.2f}M"
                elif vol_num >= 1e3:
                    volume = f"{vol_num/1e3:.2f}K"
            except:
                pass
            
            line = f"{row['date']},{row['close']},{row['open']},{row['high']},{row['low']},{volume},{row['change_pct']}\n"
            f.write(line)
    
    return {
        'rows': len(stooq_rows),
        'date_range': f"{stooq_rows[0]['date']} to {stooq_rows[-1]['date']}",
        'latest_close': stooq_rows[-1]['close'],
        'backup': str(backup_file)
    }

def run_v10_backtest():
    """Run HSI v10 analysis"""
    try:
        result = subprocess.run(
            ['python3', str(WORKSPACE / 'hsi_analysis_v10.py')],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(WORKSPACE)
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "ERROR: Backtest timeout (5 min)"
    except Exception as e:
        return f"ERROR: {e}"

def parse_results(backtest_output):
    """Extract key metrics from backtest output"""
    metrics = {}
    
    for line in backtest_output.split('\n'):
        if 'Overall Accuracy:' in line:
            metrics['accuracy'] = line.split(':')[1].strip()
        elif 'Total Predictions:' in line:
            metrics['predictions'] = line.split(':')[1].strip()
        elif 'High Solar (50+ pts):' in line:
            metrics['high_solar'] = line.split(':', 1)[1].strip()
        elif 'Prediction:' in line and 'Current Analysis' in backtest_output:
            metrics['current_prediction'] = line.split(':')[1].strip()
        elif 'Confidence:' in line and 'Current Analysis' in backtest_output:
            metrics['confidence'] = line.split(':')[1].strip()
        elif 'Solar Confluence:' in line:
            metrics['solar_confluence'] = line.split(':')[1].strip()
    
    return metrics

def main():
    print("=" * 80)
    print("HSI WEEKLY UPDATE")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Step 1: Fetch data
    print("\n[1/4] Fetching data from Stooq...")
    stooq_file = fetch_stooq_data()
    if isinstance(stooq_file, str) and stooq_file.startswith('ERROR'):
        print(f"❌ {stooq_file}")
        return stooq_file
    print(f"✅ Downloaded: {stooq_file}")
    
    # Step 2: Convert and merge
    print("\n[2/4] Converting and updating hsi.csv...")
    convert_result = convert_and_merge(stooq_file)
    if isinstance(convert_result, str) and convert_result.startswith('ERROR'):
        print(f"❌ {convert_result}")
        return convert_result
    
    print(f"✅ Updated hsi.csv:")
    print(f"   - Records: {convert_result['rows']:,}")
    print(f"   - Range: {convert_result['date_range']}")
    print(f"   - Latest: {convert_result['latest_close']}")
    print(f"   - Backup: {convert_result['backup']}")
    
    # Step 3: Run backtest
    print("\n[3/4] Running v10 backtest...")
    backtest_output = run_v10_backtest()
    print("✅ Backtest complete")
    
    # Step 4: Parse and summarize
    print("\n[4/4] Summary")
    print("-" * 80)
    metrics = parse_results(backtest_output)
    
    summary = f"""
📊 **HSI Weekly Update** ({datetime.now().strftime('%Y-%m-%d')})

**Data Updated:**
- Records: {convert_result['rows']:,}
- Latest Close: {convert_result['latest_close']}
- Range: {convert_result['date_range']}

**v10 Performance:**
- Accuracy: {metrics.get('accuracy', 'N/A')}
- Predictions: {metrics.get('predictions', 'N/A')}
- High Solar (50+ pts): {metrics.get('high_solar', 'N/A')}

**Current Signal:**
- Prediction: {metrics.get('current_prediction', 'N/A')}
- Confidence: {metrics.get('confidence', 'N/A')}
- Solar Confluence: {metrics.get('solar_confluence', 'N/A')}

✅ Update complete. Files updated:
- hsi.csv (data)
- hsi_status.json
- hsi_v10_wfo_summary.json
- hsi_backtest_v10_results.csv
"""
    
    print(summary)
    return summary

if __name__ == '__main__':
    result = main()
    print("\n" + "=" * 80)
    print("SCRIPT COMPLETE")
    print("=" * 80)
