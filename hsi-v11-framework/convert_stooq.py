import csv
from datetime import datetime

# Read Stooq data
stooq_rows = []
with open('/root/.openclaw/workspace/hsi_stooq_full.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Parse date
        date_str = row['Date']
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            # Format as M/D/YYYY
            formatted_date = f"{dt.month}/{dt.day}/{dt.year}"
            
            # Get values (handle missing volume)
            open_p = row['Open']
            high_p = row['High']
            low_p = row['Low']
            close_p = row['Close']
            volume = row.get('Volume', '0') or '0'
            
            # Calculate change %
            stooq_rows.append({
                'date': formatted_date,
                'close': close_p,
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'volume': volume
            })
        except Exception as e:
            print(f"Skip row {date_str}: {e}")

print(f"Processed {len(stooq_rows)} rows")

# Calculate % change
for i in range(1, len(stooq_rows)):
    try:
        prev_close = float(stooq_rows[i-1]['close'].replace(',', ''))
        curr_close = float(stooq_rows[i]['close'].replace(',', ''))
        change_pct = ((curr_close - prev_close) / prev_close) * 100
        stooq_rows[i]['change_pct'] = f"{change_pct:.2f}%"
    except:
        stooq_rows[i]['change_pct'] = ''

# First row has no change
stooq_rows[0]['change_pct'] = ''

# Write in hsi.csv format: 日期，收市，開市，高，低，成交量，升跌（%）
with open('/root/.openclaw/workspace/hsi_new.csv', 'w', newline='', encoding='utf-8') as f:
    f.write("日期，收市，開市，高，低，成交量，升跌（%）\n")
    for row in stooq_rows:
        volume = row['volume']
        # Format volume with B/M suffix if needed
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

print(f"Written {len(stooq_rows)} rows to hsi_new.csv")
print(f"Date range: {stooq_rows[0]['date']} to {stooq_rows[-1]['date']}")
