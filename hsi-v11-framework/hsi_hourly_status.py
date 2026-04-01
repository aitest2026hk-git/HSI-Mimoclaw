#!/usr/bin/env python3
"""
HSI Hourly Status Reporter
Generates status updates every hour with current analysis state
"""

import json
from datetime import datetime, timezone

def generate_status_report():
    """Generate hourly status report"""
    
    # Load last status
    try:
        with open('/root/.openclaw/workspace/hsi_status.json', 'r') as f:
            status = json.load(f)
    except:
        status = {'status': 'initializing', 'timestamp': datetime.now(timezone.utc).isoformat()}
    
    # Load latest report
    try:
        with open('/root/.openclaw/workspace/hsi_v6_report.md', 'r') as f:
            report = f.read()
    except:
        report = "No report available yet"
    
    # Create status message
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    
    status_text = f"""
# 📊 HSI Analysis - Hourly Status Update

**Time:** {now}

## Current Status: {status.get('status', 'unknown').upper()}

### Model Performance
- **Version:** v6 (Gann + K-Wave Core)
- **Target Accuracy:** 65%
- **Achieved:** {status.get('accuracy', {}).get('accuracy', 'N/A')}%

### Current Prediction (Feb 20, 2026)
- **Direction:** {status.get('current_prediction', {}).get('prediction', 'N/A')}
- **Confidence:** {status.get('current_prediction', {}).get('confidence', 'N/A')}%
- **Risk Score:** {status.get('current_prediction', {}).get('risk_score', 'N/A')}/100
- **Expected Move (90d):** {status.get('current_prediction', {}).get('expected_move', 'N/A')}%

### Next Steps
- [ ] Review v6 model accuracy
- [ ] Optimize signal weights if needed
- [ ] Generate updated forecast
- [ ] Monitor key support/resistance levels

---
*Next update in 1 hour*
"""
    
    # Save status update
    status_path = '/root/.openclaw/workspace/hourly_status.md'
    with open(status_path, 'w') as f:
        f.write(status_text)
    
    print(status_text)
    return status_path

if __name__ == '__main__':
    generate_status_report()
