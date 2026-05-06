#!/usr/bin/env python3
"""
HSI Cycle Indicator Tracking Spreadsheet Generator
Creates an Excel file for monitoring all cycle indicators from V11 framework
"""

import csv
from datetime import datetime, timedelta

def create_spreadsheet():
    # Create CSV files for each tracking sheet
    
    # Sheet 1: Dashboard Summary
    dashboard_data = [
        ["HSI PREDICTION v11 - CYCLE INDICATOR TRACKER"],
        [f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"],
        [""],
        ["CURRENT SIGNAL: 🟢 ACCUMULATE"],
        ["Convergence Score: 2.85/3.00"],
        [""],
        ["POSITION MANAGEMENT"],
        ["Current Position", "75%"],
        ["Cash Reserve", "25%"],
        ["Stop Loss", "-12%"],
        ["Next Rebalance", "2026-Q2"],
        [""],
        ["HSI PRICE TARGETS"],
        ["Current (2026)", "18,000-22,000"],
        ["2030 Target", "25,000"],
        ["2040+ Target", "30,000-35,000"],
    ]
    
    with open('hsi_v11_dashboard.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(dashboard_data)
    
    # Sheet 2: Cycle Phase Tracker
    cycle_data = [
        ["CYCLE PHASE TRACKER"],
        [""],
        ["Cycle", "Duration", "Current Phase", "Years in Phase", "Next Turning Point", "Status", "Weight"],
        ["Kondratiev (5th Wave)", "50-60 years", "Depression → Recovery", "11 (2015-2026)", "2025-2026", "🟢 On Track", "30%"],
        ["Real Estate (China)", "~20 years", "Late Decline → Recovery", "7 (2019-2026)", "2026-2027", "🟡 Watching", "20%"],
        ["Juglar (Investment)", "~9 years", "Mid-Recovery", "3 (2023-2026)", "2028-2029", "🟢 On Track", "15%"],
        ["Kitchin (Inventory)", "~18 months", "Expansion", "9 months", "2026 Q3-Q4", "🟢 On Track", "10%"],
        [""],
        ["TRACKING INDICATORS"],
        ["Cycle", "Indicator", "Frequency", "Current Reading", "Threshold", "Status", "Last Check", "Next Check"],
        ["Kondratiev", "AI Investment Growth YoY", "Quarterly", ">20%", "Strong", "🟢", "2026-Q1", "2026-Q2"],
        ["Real Estate", "HK Property Transactions", "Monthly", "+15% QoQ", "Stabilizing", "🟡", "2026-Feb", "2026-Mar"],
        ["Juglar", "Fixed Asset Investment", "Quarterly", ">5%", "Moderate", "🟢", "2026-Q1", "2026-Q2"],
        ["Kitchin", "Inventory/Sales Ratio", "Monthly", "<1.5", "Healthy", "🟢", "2026-Feb", "2026-Mar"],
    ]
    
    with open('hsi_v11_cycle_tracker.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(cycle_data)
    
    # Sheet 3: Sector Allocation Tracker
    sector_data = [
        ["SECTOR ALLOCATION TRACKER"],
        [""],
        ["Sector", "Target %", "Current %", "Deviation", "Signal", "Key Stocks", "Last Rebalance", "Action Needed"],
        ["Technology", "15%", "12%", "-3%", "🚀 OVERWEIGHT", "Tencent, Alibaba, Xiaomi, SMIC", "2026-01-15", "Add +3%"],
        ["Financials", "25%", "28%", "+3%", "✅ NEUTRAL", "HSBC, AIA, BOC, CCB", "2026-01-15", "Hold"],
        ["Properties", "10%", "8%", "-2%", "🚀 OVERWEIGHT", "SHK, CK Asset, CR Land", "2026-01-15", "Add +2%"],
        ["Utilities", "10%", "11%", "+1%", "⚠️ UNDERWEIGHT", "CLP, HK Electric, Town Gas", "2026-01-15", "Reduce -1%"],
        ["Consumer Staples", "15%", "14%", "-1%", "✅ NEUTRAL", "Mengniu, Nongfu, CR Beer", "2026-01-15", "Add +1%"],
        ["Industrials", "10%", "9%", "-1%", "🚀 OVERWEIGHT", "CRRC, Goldwind, MTR", "2026-01-15", "Add +1%"],
        ["Energy", "5%", "6%", "+1%", "⚠️ UNDERWEIGHT", "CNOOC", "2026-01-15", "Reduce -1%"],
        ["Cash/Gold", "10%", "12%", "+2%", "🛡️ RESERVE", "Liquidity buffer", "2026-01-15", "Deploy -2%"],
        [""],
        ["TOTAL", "100%", "100%", "0%", "", "", "", ""],
    ]
    
    with open('hsi_v11_sector_allocation.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sector_data)
    
    # Sheet 4: Solar Term Calendar 2026
    solar_data = [
        ["2026 SOLAR TERM CALENDAR"],
        [""],
        ["Season", "Solar Term", "Chinese", "Date", "Signal", "Action", "Sector Focus", "Completed", "Notes"],
        ["Spring", "Lichun", "立春", "2026-02-04", "🟢", "Increase exposure", "Technology, Industrials", "✅", ""],
        ["Spring", "Yushui", "雨水", "2026-02-19", "🟢", "Liquidity improves", "Financials", "⏳", ""],
        ["Spring", "Jingzhe", "惊蛰", "2026-03-05", "🟢", "Tech stocks activate", "Technology", "⏳", ""],
        ["Spring", "Chunfen", "春分", "2026-03-20", "🟡", "Hold/Rebalance", "Balanced", "⏳", ""],
        ["Spring", "Qingming", "清明", "2026-04-05", "🟡", "Caution/Trim winners", "Take profits", "⏳", ""],
        ["Spring", "Guyu", "谷雨", "2026-04-20", "🟢", "Accumulate quality", "Properties, Financials", "⏳", ""],
        ["Summer", "Lixia", "立夏", "2026-05-05", "🟢", "Risk-on", "Growth sectors", "⏳", ""],
        ["Summer", "Xiaoman", "小满", "2026-05-21", "🟡", "Near peak/Partial profits", "Take some profits", "⏳", ""],
        ["Summer", "Mangzhong", "芒种", "2026-06-05", "🟡", "Harvest time/Reduce", "Reduce cyclicals", "⏳", ""],
        ["Summer", "Xiazhi", "夏至", "2026-06-21", "🔴", "Peak/Maximum caution", "Defensive shift", "⏳", "Key date"],
        ["Summer", "Xiaoshu", "小暑", "2026-07-07", "🔴", "Start correction", "Defensive", "⏳", ""],
        ["Summer", "Dashu", "大暑", "2026-07-23", "🔴", "Correction phase", "Hold cash", "⏳", ""],
        ["Autumn", "Liqiu", "立秋", "2026-08-07", "🟡", "Harvest/Reduce risk", "Further reduction", "⏳", ""],
        ["Autumn", "Chushu", "处暑", "2026-08-23", "🟡", "Exit positions", "More reduction", "⏳", ""],
        ["Autumn", "Bailu", "白露", "2026-09-07", "🟡", "Defense mode", "Utilities, Staples", "⏳", ""],
        ["Autumn", "Qiufen", "秋分", "2026-09-23", "🟡", "Rebalance", "Balanced", "⏳", ""],
        ["Autumn", "Hanlu", "寒露", "2026-10-08", "🟡", "Caution/Increase cash", "More cash", "⏳", ""],
        ["Autumn", "Shuangjiang", "霜降", "2026-10-23", "🟢", "Low approaching/Prepare", "Prepare to buy", "⏳", ""],
        ["Winter", "Lidong", "立冬", "2026-11-07", "🟢", "Accumulation starts", "Begin buying", "⏳", ""],
        ["Winter", "Xiaoxue", "小雪", "2026-11-22", "🟢", "Gradual build", "Quality stocks", "⏳", ""],
        ["Winter", "Daxue", "大雪", "2026-12-07", "🟢", "Deep value", "Aggressive accumulation", "⏳", ""],
        ["Winter", "Dongzhi", "冬至", "2026-12-21", "🟢🔺", "Turning point/MAX position", "All growth sectors", "⏳", "KEY DATE"],
        ["Winter", "Xiaohan", "小寒", "2027-01-05", "🟢", "Hold positions", "Maintain", "⏳", ""],
        ["Winter", "Dahan", "大寒", "2027-01-20", "🟢", "Prepare for spring", "Final adjustments", "⏳", ""],
    ]
    
    with open('hsi_v11_solar_calendar_2026.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(solar_data)
    
    # Sheet 5: Signal Convergence History
    convergence_data = [
        ["SIGNAL CONVERGENCE HISTORY"],
        [""],
        ["Date", "Kondratiev", "Real Estate", "Juglar", "Kitchin", "Gann Time", "Gann Price", "Solar", "Total Score", "Signal", "Action Taken"],
        ["2026-02-26", "0.90", "0.60", "0.70", "0.75", "0.80", "0.60", "0.70", "2.85", "🟢 ACCUMULATE", "Initiate position"],
        ["2026-01-26", "0.85", "0.50", "0.65", "0.70", "0.75", "0.55", "0.60", "2.65", "🟢 ACCUMULATE", "Prepare"],
        ["2025-12-26", "0.80", "0.45", "0.60", "0.65", "0.70", "0.50", "0.50", "2.45", "🟡 HOLD", "Wait"],
        ["2025-11-26", "0.75", "0.40", "0.55", "0.60", "0.65", "0.45", "0.40", "2.20", "🟡 HOLD", "Wait"],
        ["2025-10-26", "0.70", "0.35", "0.50", "0.55", "0.60", "0.40", "0.35", "1.95", "🟡 HOLD", "Wait"],
        ["", "", "", "", "", "", "", "", "", "", ""],
        ["Threshold Guide:", ">2.5 = ACCUMULATE", "1.5-2.5 = HOLD", "<1.5 = REDUCE", "", "", "", "", "", "", ""],
    ]
    
    with open('hsi_v11_convergence_history.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(convergence_data)
    
    # Sheet 6: V10 Integration (May 9 Window)
    v10_data = [
        ["V10 INTEGRATION - HIGH CONFLUENCE WINDOWS 2026"],
        [""],
        ["Window Date", "Confluence Pts", "Tier", "Solar Term", "Days from Window", "V11 Phase", "Combined Action"],
        ["2026-05-09", "70", "High", "立夏 (May 5)", "+4 days", "Recovery Start", "🟢 BEGIN ACCUMULATION"],
        ["2026-06-25", "75", "High", "夏至 (Jun 21)", "+4 days", "Recovery Start", "🟡 Take partial profits"],
        ["2026-08-07", "65", "Medium-High", "立秋 (Aug 7)", "0 days", "Recovery", "🟡 Monitor/Reduce"],
        ["2026-10-06", "90", "Very High", "霜降 (Oct 23)", "-17 days", "Recovery", "🟢 Strong buy opportunity"],
        ["2026-12-21", "75", "High", "冬至 (Dec 21)", "0 days", "Recovery", "🟢 MAXIMUM POSITION"],
        [""],
        ["STRATEGY"],
        ["Use V11 for WHAT to buy (sector allocation)"],
        ["Use V10 for WHEN to enter (timing windows)"],
        ["Primary Entry: May 9, 2026 (70 pts + V11 Recovery confirmation)"],
        ["Secondary Entry: Oct 6, 2026 (90 pts - Very High confluence)"],
        ["Max Position: Dec 21, 2026 (冬至 turning point)"],
    ]
    
    with open('hsi_v11_v10_integration.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(v10_data)
    
    # Sheet 7: HSI Constituents Watchlist
    constituents_data = [
        ["HSI CONSTITUENTS WATCHLIST"],
        [""],
        ["Stock Code", "Name", "Sector", "Target Weight", "Current Price", "Buy Zone", "Stop Loss", "2030 Target", "Rating"],
        ["0700.HK", "Tencent", "Technology", "5%", "TBD", "TBD", "-15%", "TBD", "🚀 Strong Buy"],
        ["9988.HK", "Alibaba", "Technology", "4%", "TBD", "TBD", "-15%", "TBD", "🚀 Strong Buy"],
        ["1810.HK", "Xiaomi", "Technology", "3%", "TBD", "TBD", "-15%", "TBD", "🚀 Buy"],
        ["0981.HK", "SMIC", "Technology", "3%", "TBD", "TBD", "-20%", "TBD", "🚀 Buy"],
        ["0005.HK", "HSBC", "Financials", "8%", "TBD", "TBD", "-10%", "TBD", "✅ Hold"],
        ["1299.HK", "AIA", "Financials", "7%", "TBD", "TBD", "-12%", "TBD", "✅ Hold"],
        ["3988.HK", "Bank of China", "Financials", "5%", "TBD", "TBD", "-10%", "TBD", "✅ Hold"],
        ["0939.HK", "CCB", "Financials", "5%", "TBD", "TBD", "-10%", "TBD", "✅ Hold"],
        ["0016.HK", "Sun Hung Kai", "Properties", "4%", "TBD", "TBD", "-12%", "TBD", "🚀 Buy"],
        ["1113.HK", "CK Asset", "Properties", "3%", "TBD", "TBD", "-12%", "TBD", "🚀 Buy"],
        ["1109.HK", "CR Land", "Properties", "3%", "TBD", "TBD", "-12%", "TBD", "🚀 Buy"],
        ["0002.HK", "CLP", "Utilities", "4%", "TBD", "TBD", "-8%", "TBD", "⚠️ Hold"],
        ["2638.HK", "HK Electric", "Utilities", "3%", "TBD", "TBD", "-8%", "TBD", "⚠️ Hold"],
        ["0003.HK", "Town Gas", "Utilities", "3%", "TBD", "TBD", "-8%", "TBD", "⚠️ Hold"],
        ["2319.HK", "Mengniu", "Consumer", "5%", "TBD", "TBD", "-12%", "TBD", "✅ Hold"],
        ["9633.HK", "Nongfu Spring", "Consumer", "5%", "TBD", "TBD", "-15%", "TBD", "✅ Hold"],
        ["0291.HK", "CR Beer", "Consumer", "5%", "TBD", "TBD", "-12%", "TBD", "✅ Hold"],
        ["1766.HK", "CRRC", "Industrials", "4%", "TBD", "TBD", "-12%", "TBD", "🚀 Buy"],
        ["2208.HK", "Goldwind", "Industrials", "3%", "TBD", "TBD", "-15%", "TBD", "🚀 Buy"],
        ["0066.HK", "MTR", "Industrials", "3%", "TBD", "TBD", "-10%", "TBD", "🚀 Buy"],
        ["0883.HK", "CNOOC", "Energy", "5%", "TBD", "TBD", "-15%", "TBD", "⚠️ Hold"],
    ]
    
    with open('hsi_v11_constituents_watchlist.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(constituents_data)
    
    print("✅ Created 7 CSV tracking files:")
    print("   1. hsi_v11_dashboard.csv")
    print("   2. hsi_v11_cycle_tracker.csv")
    print("   3. hsi_v11_sector_allocation.csv")
    print("   4. hsi_v11_solar_calendar_2026.csv")
    print("   5. hsi_v11_convergence_history.csv")
    print("   6. hsi_v11_v10_integration.csv")
    print("   7. hsi_v11_constituents_watchlist.csv")
    print("\n📊 Open these in Excel/Google Sheets for full tracking functionality!")

if __name__ == '__main__':
    create_spreadsheet()
