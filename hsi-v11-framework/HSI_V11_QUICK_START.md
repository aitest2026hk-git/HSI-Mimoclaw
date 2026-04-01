# 🚀 HSI v11 - Quick Start Guide

**For:** boss  
**Created:** 2026-02-26  
**Status:** Ready to Use

---

## ⚡ 60-Second Overview

**What:** Complete HSI prediction system combining:
- Zhou Jintao's Kondratiev Cycle Theory (long-term)
- Gann Theory (time/price geometry)
- 24 Solar Terms (seasonal timing)

**Current Signal:** 🟢 ACCUMULATE (Long-term), 🟡 WAIT until May 9 (Short-term)

**Target:** 25,000 HSI by 2030 (from ~19,000 now = ~32% upside)

---

## 📁 Essential Files (Start Here)

| Priority | File | What It Does |
|----------|------|--------------|
| 🔴 **1** | `HSI_V11_IMPLEMENTATION_COMPLETE.md` | Full implementation status |
| 🔴 **2** | `hsi_v11_constituents_watchlist_updated.csv` | **Live prices for 21 stocks** |
| 🟡 **3** | `HSI_v11_Complete_Tracker.csv` | Excel workbook (all tracking sheets) |
| 🟡 **4** | `memory/hsi-v11-dashboard.md` | One-page reference dashboard |
| 🟢 **5** | `HSI_Prediction_v11_Framework.html` | Print to PDF for offline reading |

---

## 🎯 The Strategy (Simple Version)

### Long-Term (V11 - Zhou Jintao)
- **What:** We're at start of 10-year Recovery phase (2026-2030)
- **Action:** Accumulate quality stocks 2026-2026
- **Target:** 25,000 HSI by 2030
- **Sectors:** Overweight Technology, Properties, Industrials

### Short-Term (V10 - Gann/Solar)
- **What:** Wait for high-confluence timing windows
- **Primary Entry:** May 9, 2026 (70 points solar confluence)
- **Secondary Entry:** Oct 6, 2026 (90 points - Very High)
- **Max Position:** Dec 21, 2026 (冬至 turning point)

### Combined
- **Use V11** to decide WHAT to buy (sector allocation)
- **Use V10** to decide WHEN to buy (timing windows)
- **No conflict** - they complement each other!

---

## 💼 Your Portfolio (May 9 Entry)

### Target Allocation (75% invested, 25% cash)

```
🚀 OVERWEIGHT (35%):
   Technology    15%  → Tencent, Alibaba, Xiaomi, SMIC
   Properties    10%  → Sun Hung Kai, CK Asset, CR Land
   Industrials   10%  → CRRC, Goldwind, MTR

✅ NEUTRAL (40%):
   Financials    25%  → HSBC, AIA, Bank of China, CCB
   Consumer      15%  → Mengniu, Nongfu Spring, CR Beer

⚠️ UNDERWEIGHT (15%):
   Utilities     10%  → CLP, HK Electric, Town Gas
   Energy         5%  → CNOOC

🛡️ CASH RESERVE (10%):
   Cash/Gold     10%  → Dry powder for opportunities
```

### Top 10 Stocks to Buy (May 9)

| # | Stock | Code | Sector | Target % | Current Price | Buy Zone |
|---|-------|------|--------|----------|---------------|----------|
| 1 | Tencent | 0700.HK | Technology | 5% | HKD 518.00 | 440-492 |
| 2 | HSBC | 0005.HK | Financials | 8% | HKD 145.50 | 131-138 |
| 3 | AIA | 1299.HK | Financials | 7% | HKD 86.00 | 77-82 |
| 4 | Alibaba | 9988.HK | Technology | 4% | HKD 145.20 | 123-138 |
| 5 | Sun Hung Kai | 0016.HK | Properties | 4% | HKD 139.60 | 123-133 |
| 6 | Xiaomi | 1810.HK | Technology | 3% | HKD 35.60 | 30-34 |
| 7 | CK Asset | 1113.HK | Properties | 3% | HKD 47.52 | 42-45 |
| 8 | Bank of China | 3988.HK | Financials | 5% | HKD 4.66 | 4.2-4.4 |
| 9 | CCB | 0939.HK | Financials | 5% | HKD 8.05 | 7.2-7.6 |
| 10 | CLP | 0002.HK | Utilities | 4% | HKD 74.60 | 69-72 |

**Full list:** See `hsi_v11_constituents_watchlist_updated.csv`

---

## 📅 Key Dates 2026

| Date | Event | Signal | Action |
|------|-------|--------|--------|
| **Feb 4** | 立春 (Lichun) | 🟢 | ✅ Done - Research phase started |
| **Mar 20** | 春分 (Chunfen) | 🟡 | Hold/Rebalance |
| **Apr 20** | 谷雨 (Guyu) | 🟢 | Accumulate quality |
| **May 5** | 立夏 (Lixia) | 🟢 | Risk-on (4 days before entry) |
| **May 9** | **V10 Window** | 🟢 | **🎯 PRIMARY ENTRY (70 pts)** |
| **Jun 21** | 夏至 (Xiazhi) | 🔴 | Take partial profits if hot |
| **Oct 6** | V10 Window | 🟢 | Add position (90 pts - Very High) |
| **Dec 21** | 冬至 (Dongzhi) | 🟢🔺 | **Maximum position** |

---

## 🔧 Automation Commands

### Update Prices (Weekly)
```bash
cd /root/.openclaw/workspace
python3 fetch_realtime_prices_simple.py
```

### Check Alerts (Daily)
```bash
cd /root/.openclaw/workspace
python3 hsi_v11_alert_system.py
```

### View Alert Summary
```bash
cat hsi_v11_alert_summary.txt
```

---

## 📊 Monitoring Dashboard

### Check These Weekly:
1. **Convergence Score** (Target: >2.5 = 🟢 ACCUMULATE)
   - File: `hsi_v11_convergence_history.csv`
   
2. **Sector Allocation** (Deviation <5%)
   - File: `hsi_v11_sector_allocation.csv`

3. **Next Solar Term** (Action 7 days before)
   - File: `hsi_v11_solar_calendar_2026.csv`

4. **Next V10 Window** (Prepare 14 days before)
   - File: `hsi_v11_v10_integration.csv`

---

## 🚨 Alert System

### You'll Get Alerts For:
- 🟢🟡🔴 Signal changes (convergence score)
- Cycle phase changes (Kondratiev, Real Estate, etc.)
- Solar terms approaching (7 days before)
- Sector allocation drift (>5% from target)
- V10 windows (14 days and 7 days before)

### Alert Files:
- **Current:** `hsi_v11_alert_summary.txt`
- **History:** `hsi_v11_alert_history.json`

---

## 📱 Quick Reference Commands

```bash
# View current prices
cat hsi_v11_constituents_watchlist_updated.csv

# View alerts
cat hsi_v11_alert_summary.txt

# View dashboard
cat memory/hsi-v11-dashboard.md

# Update prices
python3 fetch_realtime_prices_simple.py

# Check alerts
python3 hsi_v11_alert_system.py
```

---

## 🎯 May 9 Execution Checklist

### Pre-Market (8:00-9:00 AM HKT)
```
□ Run price fetcher: python3 fetch_realtime_prices_simple.py
□ Run alert check: python3 hsi_v11_alert_system.py
□ Confirm V10 confluence ≥70 pts
□ Confirm V11 convergence ≥2.5
□ Verify cash position (75% ready)
```

### Market Open (9:30 AM HKT)
```
□ Review buy zones for each stock
□ Place limit orders at or below buy zone
□ Set stop losses (-12% portfolio, -15% individual)
□ Log all entries in dashboard
```

### Post-Market (4:00-5:00 PM HKT)
```
□ Confirm all orders filled
□ Update sector allocation tracker
□ Update convergence history
□ Schedule next weekly review
```

---

## 🆘 Troubleshooting

### Price Fetcher Fails
```bash
# Check internet connection
ping google.com

# Try again with verbose output
python3 fetch_realtime_prices_simple.py 2>&1 | tee price_fetch.log

# Manual price entry OK - just update CSV directly
```

### Alerts Not Working
```bash
# Check Python version
python3 --version

# Run with debug output
python3 hsi_v11_alert_system.py 2>&1 | tee alerts.log

# Check alert history
cat hsi_v11_alert_history.json | python3 -m json.tool
```

### Excel File Issues
```bash
# CSV bundle can be opened in any spreadsheet app
# If formatting issues: Data → Text to Columns → Comma delimiter
# Or import each section to separate sheets manually
```

---

## 📞 Support

**Documentation:**
- Full Framework: `memory/hsi-prediction-v11-framework.md`
- Implementation: `HSI_V11_IMPLEMENTATION_COMPLETE.md`
- Deliverables: `HSI_V11_DELIVERABLES_SUMMARY.md`

**Quick Help:**
- Just ask: "What's the current signal?"
- Or: "Show me the May 9 checklist"
- Or: "Update the prices"

---

## ✅ Status Check

```
╔══════════════════════════════════════════════════════════════════╗
║  SYSTEM STATUS: 🟢 FULLY OPERATIONAL                             ║
╠══════════════════════════════════════════════════════════════════╣
║  Price Fetcher:     ✅ Working (21/21 stocks)                    ║
║  Alert System:      ✅ Working (5 monitors active)               ║
║  Tracking Sheets:   ✅ Generated (7 CSVs)                        ║
║  Excel Workbook:    ✅ Generated (combined)                      ║
║  PDF Export:        ✅ Ready (HTML file)                         ║
║  Documentation:     ✅ Complete (5 files)                        ║
╠══════════════════════════════════════════════════════════════════╣
║  Next Action:       May 9, 2026 (Primary Entry)                  ║
║  Days Until:      [Calculate from current date]                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

**You're all set, boss!** 🚀

**Remember:** 
- Long-term: 🟢 ACCUMULATE (2026-2030 Recovery phase)
- Short-term: 🟡 WAIT until May 9 (V10 timing)
- Combined: Use V11 for WHAT, V10 for WHEN

**See you on May 9!** 🎯

---

**cyclingAi** | 2026-02-26
