# Cron Jobs & Reminder Settings

**Last Updated:** April 9, 2026 15:15 CST

---

## Active Cron Jobs

### 1. HSI Put Option Review (One-Shot)
- **Job ID:** `c2fce042-28e3-464b-92af-2326ed943366`
- **Name:** HSI Put Option Review
- **Schedule:** 2026-04-20 09:00 CST (one-time)
- **Session:** main
- **Auto-delete:** Yes
- **Message:**
```
⏰ REMINDER: HSI Put Option (strike 24,800, expiry end of April) — today is April 20,
the user's reassessment date. Check HSI level, oil price, Iran ceasefire status, and
put option premium. Advise whether to cut loss or hold for the Apr 19-25 VERY HIGH
cycle window. The put was entered at 0.40, last seen at 0.06 (-85% loss). Key: if
HSI >25,500 and oil <$100, recommend cutting. If ceasefire collapsed or oil spiked,
recommend holding.
```

### 2. Active Tasks Reminder (Recurring)
- **Job ID:** `4b890064-e76a-4f37-8e46-4fd4c5c118be`
- **Name:** Active Tasks Reminder (every 30 min)
- **Schedule:** Every 30 minutes
- **Session:** main
- **Auto-delete:** No
- **Message:**
```
⏰ TASK REMINDER — Active items: (1) HSI Put Option: strike 24,800, current 0.06,
decision date Apr 20. Watch: HSI level, oil price ($90 support, $105 danger), Iran
ceasefire status, Hormuz tanker traffic. (2) General market watch: oil below $100 =
bullish, above $110 = danger. (3) Next cycle window: Apr 19-25 VERY HIGH (116).
Keep cash ready.
```

---

## How to Restore (if needed)

To recreate these cron jobs, run the following in a session:

### Restore Job 1 (Apr 20 reminder):
```
Set a one-shot cron for 2026-04-20 09:00 CST to remind about HSI put option
(strike 24800, expiry end of April, entry 0.40, last 0.06)
```

### Restore Job 2 (30-min reminder):
```
Set a recurring cron every 30 minutes to remind about active tasks:
HSI put option watch, oil price levels, cycle window countdown
```

---

## Reference: Key Watch Levels

| Asset | Bullish Trigger | Bearish Trigger |
|-------|----------------|-----------------|
| Oil | <$90 | >$110 (>$120 = catastrophe) |
| HSI | >26,500 | <25,000 |
| Gold | <$4,500 (correction) | >$5,200 (crisis) |
| VIX | <18 | >30 |

---

*HSI-Mimoclaw Workspace — Settings Backup*
