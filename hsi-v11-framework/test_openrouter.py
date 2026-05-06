#!/usr/bin/env python3
"""
Quick csagent analysis with better error handling
"""

import json
import urllib.request
import ssl
from datetime import datetime

CONFIG = {
    'openrouter': {
        'api_key': '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',
        'base_url': 'https://openrouter.ai/api/v1',
        'model': 'google/gemini-2.0-flash-001'
    }
}

def analyze_stock(symbol, name, price, change_20d, change_60d):
    """Quick analysis via OpenRouter"""
    prompt = f"""Analyze {name} ({symbol}):
Price: {price}, 20d: {change_20d:+.1f}%, 60d: {change_60d:+.1f}%
Using Cai Sen methodology (volume-price analysis), give JSON:
{{"signal":"BUY/HOLD/SELL","confidence":0-100,"comment":"brief"}}
"""
    
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    url = f"{CONFIG['openrouter']['base_url']}/chat/completions"
    data = {
        "model": CONFIG['openrouter']['model'],
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    headers = {
        "Authorization": f"Bearer {CONFIG['openrouter']['api_key']}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
            result = json.loads(resp.read().decode())
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {e}"
    return "No response"

# Test with Tencent
print("Testing OpenRouter API with Tencent (0700.HK)...")
result = analyze_stock('0700.HK', 'Tencent', 518.0, -2.1, -5.8)
print(f"Result: {result}")
