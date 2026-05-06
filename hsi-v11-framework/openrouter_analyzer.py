#!/usr/bin/env python3
"""
OpenRouter LLM Integration for 蔡森 (Cai Sen) Analysis

Provides:
- analyze_chart_image: Send chart images to vision-capable LLM
- analyze_ohlc_data: Text-based analysis of OHLC data
- combine_signals: Merge algorithmic and LLM analysis
"""

import json
import os
import urllib.request
import ssl
from typing import Dict, Optional, Union
from datetime import datetime

# Load configuration
def load_config() -> Dict:
    """Load API configuration from caisen_config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'caisen_config.json')
    if not os.path.exists(config_path):
        config_path = '/root/.openclaw/workspace/caisen_config.json'
    
    with open(config_path, 'r') as f:
        return json.load(f)


def call_openrouter(messages: list, model: str = None, max_tokens: int = 1000) -> Dict:
    """Make API call to OpenRouter"""
    config = load_config()
    openrouter_config = config.get('openrouter', config)
    api_key = openrouter_config.get('api_key')
    base_url = openrouter_config.get('base_url', 'https://openrouter.ai/api/v1')
    if not model:
        model = openrouter_config.get('default_model', 'nvidia/nemotron-3-nano-30b-a3b:free')
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    url = f"{base_url}/chat/completions"
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/caisen-trading",
        "X-Title": "CaiSen Trading Analysis"
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60, context=ssl_context) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result
    
    except Exception as e:
        return {
            'error': str(e),
            'choices': [{'message': {'content': f"API Error: {e}"}}]
        }


def analyze_chart_image(image_path: str, stock_symbol: str = "0700.HK") -> Dict:
    """
    Analyze a chart image using vision-capable LLM
    
    Args:
        image_path: Path to chart image (PNG/JPG)
        stock_symbol: Stock symbol for context
    
    Returns:
        Dict with LLM analysis including pattern detection, entry/exit levels, confidence
    """
    config = load_config()
    
    # Check if image exists
    if not os.path.exists(image_path):
        return {
            'error': f'Image not found: {image_path}',
            'signal': 'HOLD',
            'confidence': 0
        }
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    # Encode to base64
    import base64
    image_base64 = base64.b64encode(image_data).decode('utf-8')
    
    # Determine MIME type
    mime_type = 'image/png' if image_path.lower().endswith('.png') else 'image/jpeg'
    
    # Build prompt
    system_prompt = """You are an expert technical analyst specializing in 蔡森 (Cai Sen)'s volume-price methodology.

蔡森's Core Principles:
- 量在價先 (Volume precedes price) - Watch volume first
- 小賠大賺 (Small losses, big gains) - Cut losses quickly, let profits run
- 嚴守停損 (Strict stop-loss) - Never violate your stop
- 隨勢而為 (Follow the trend) - Trade with the trend

蔡森's 12 Key Patterns:
1. W-bottom (雙重底) - Two lows at similar level, bullish reversal
2. 破底翻 (Spring) - False breakdown below support, then reversal
3. M-top (雙重頂) - Two peaks at similar level, bearish reversal
4. 假突破 (False Breakout) - Breakout fails and reverses
5. 頭肩頂 (Head & Shoulders Top) - Three peaks, head highest, bearish
6. 頭肩底 (Head & Shoulders Bottom) - Three troughs, head lowest, bullish
7. 收斂三角形頭部 (Descending Triangle) - Flat support, declining resistance
8. 收斂三角形底部 (Ascending Triangle) - Flat resistance, rising support
9. 上飄旗形 (Bearish Flag) - Sharp decline then upward consolidation
10. 下飄旗形 (Bullish Flag) - Sharp rally then downward consolidation
11. 問題量 (Problem Volume) - Volume-price divergence warning
12. 時間波 (Time Waves) - Cyclical timing patterns

Analyze this chart and provide structured output in JSON format."""

    user_prompt = f"""Analyze this {stock_symbol} stock chart.

Provide your analysis in the following JSON format:

{{
    "patterns_detected": [
        {{
            "name": "Pattern name from 蔡森's 12 patterns",
            "confidence": 0.0-1.0,
            "description": "What you see on the chart"
        }}
    ],
    "trend_direction": "uptrend|downtrend|sideways",
    "trend_strength": "strong|moderate|weak",
    "volume_analysis": {{
        "recent_trend": "increasing|decreasing|flat",
        "divergence": true|false,
        "notes": "Volume observations"
    }},
    "key_levels": {{
        "support": [price1, price2],
        "resistance": [price1, price2]
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "entry_price": price,
        "stop_loss": price,
        "target_price": price,
        "risk_reward_ratio": ratio,
        "time_horizon_days": number
    }},
    "reasoning": "Detailed explanation of your analysis",
    "caisen_principles_applied": ["List which 蔡森 principles apply"]
}}

Be specific with price levels. Use 蔡森's methodology for pattern recognition and target calculation."""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image_base64}"
                    }
                }
            ]
        }
    ]
    
    # Call API with vision model
    result = call_openrouter(messages, model='google/gemini-2.0-flash-001', max_tokens=1500)
    
    if 'error' in result:
        return {
            'error': result.get('error', 'Unknown API error'),
            'signal': 'HOLD',
            'confidence': 0
        }
    
    # Parse response
    try:
        content = result['choices'][0]['message']['content']
        
        # Try to extract JSON from response
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            analysis = json.loads(json_str)
        else:
            # Fallback: return raw content
            analysis = {
                'raw_analysis': content,
                'signal': {'direction': 'HOLD', 'confidence': 0.5}
            }
        
        analysis['model_used'] = 'google/gemini-2.0-flash-001'
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['image_analyzed'] = image_path
        
        return analysis
    
    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse LLM response: {e}',
            'raw_content': result['choices'][0]['message']['content'] if 'choices' in result else None,
            'signal': 'HOLD',
            'confidence': 0
        }


def analyze_ohlc_data(data_dict: Dict, stock_symbol: str = "0700.HK") -> Dict:
    """
    Analyze OHLC data using text-based LLM
    
    Args:
        data_dict: Dict with 'dates', 'open', 'high', 'low', 'close', 'volume' lists
        stock_symbol: Stock symbol
    
    Returns:
        Dict with LLM analysis
    """
    # Prepare recent data (last 60 days)
    n = min(60, len(data_dict['close']))
    
    recent_data = []
    for i in range(-n, 0):
        recent_data.append({
            'date': data_dict['dates'][i],
            'open': data_dict['open'][i],
            'high': data_dict['high'][i],
            'low': data_dict['low'][i],
            'close': data_dict['close'][i],
            'volume': data_dict['volume'][i]
        })
    
    # Calculate summary statistics
    current_price = data_dict['close'][-1]
    price_20d_ago = data_dict['close'][-20] if len(data_dict['close']) >= 20 else data_dict['close'][0]
    price_change_pct = ((current_price - price_20d_ago) / price_20d_ago) * 100
    
    avg_vol_recent = sum(data_dict['volume'][-10:]) / 10
    avg_vol_older = sum(data_dict['volume'][-30:-10]) / 20 if len(data_dict['volume']) >= 30 else avg_vol_recent
    vol_change_pct = ((avg_vol_recent - avg_vol_older) / avg_vol_older) * 100 if avg_vol_older > 0 else 0
    
    high_60d = max(data_dict['high'][-60:])
    low_60d = min(data_dict['low'][-60:])
    
    # Build prompt with data summary
    system_prompt = """You are an expert technical analyst specializing in 蔡森 (Cai Sen)'s volume-price methodology.

Key Principles:
- 量在價先 (Volume precedes price)
- 小賠大賺 (Small losses, big gains)
- 嚴守停損 (Strict stop-loss)
- 隨勢而為 (Follow the trend)

Focus on volume-price relationships and the 12 蔡森 patterns."""

    user_prompt = f"""Analyze {stock_symbol} based on the following OHLCV data summary:

**Current Price**: HKD {current_price:.2f}
**60-Day Range**: HKD {low_60d:.2f} - HKD {high_60d:.2f}
**20-Day Change**: {price_change_pct:+.1f}%
**Volume Trend**: {vol_change_pct:+.1f}% (recent vs older)

**Recent Data (last 10 days)**:
{json.dumps(recent_data[-10:], indent=2)}

**Full Recent Data (last 60 days)**:
{json.dumps(recent_data, indent=2)}

Provide analysis in JSON format:

{{
    "trend_analysis": {{
        "direction": "uptrend|downtrend|sideways",
        "strength": "strong|moderate|weak",
        "evidence": "Explanation"
    }},
    "volume_analysis": {{
        "trend": "increasing|decreasing|flat",
        "confirming_price": true|false,
        "divergence_detected": true|false,
        "notes": "Volume observations"
    }},
    "patterns_detected": [
        {{
            "name": "Pattern name",
            "confidence": 0.0-1.0,
            "evidence": "Why you think this pattern exists"
        }}
    ],
    "key_levels": {{
        "immediate_support": price,
        "strong_support": price,
        "immediate_resistance": price,
        "strong_resistance": price
    }},
    "signal": {{
        "direction": "BUY|SELL|HOLD",
        "confidence": 0.0-1.0,
        "reasoning": "Why this signal"
    }},
    "caisen_principles": ["Which principles apply"],
    "risk_factors": ["Key risks to consider"]
}}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    result = call_openrouter(messages, model='google/gemini-2.0-flash-001', max_tokens=1500)
    
    if 'error' in result:
        return {
            'error': result.get('error'),
            'signal': 'HOLD',
            'confidence': 0
        }
    
    try:
        content = result['choices'][0]['message']['content']
        
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            analysis = json.loads(json_str)
        else:
            analysis = {
                'raw_analysis': content,
                'signal': {'direction': 'HOLD', 'confidence': 0.5}
            }
        
        analysis['model_used'] = 'google/gemini-2.0-flash-001'
        analysis['timestamp'] = datetime.now().isoformat()
        analysis['data_points_analyzed'] = n
        
        return analysis
    
    except json.JSONDecodeError as e:
        return {
            'error': f'Failed to parse LLM response: {e}',
            'raw_content': result['choices'][0]['message']['content'] if 'choices' in result else None,
            'signal': 'HOLD',
            'confidence': 0
        }


def combine_signals(algorithmic_detection: Dict, llm_analysis: Dict) -> Dict:
    """
    Combine algorithmic pattern detection with LLM analysis
    
    Args:
        algorithmic_detection: Results from caisen_patterns.scan_all_patterns()
        llm_analysis: Results from analyze_chart_image() or analyze_ohlc_data()
    
    Returns:
        Combined analysis with final signal
    """
    combined = {
        'timestamp': datetime.now().isoformat(),
        'algorithmic_analysis': algorithmic_detection,
        'llm_analysis': llm_analysis,
        'combined_signal': {}
    }
    
    # Extract algorithmic signal
    algo_signal = algorithmic_detection.get('overall_signal', {})
    algo_direction = algo_signal.get('direction', 'HOLD')
    algo_confidence = algo_signal.get('confidence', 0.5)
    
    # Extract LLM signal
    llm_signal = llm_analysis.get('signal', {})
    llm_direction = llm_signal.get('direction', 'HOLD')
    llm_confidence = llm_signal.get('confidence', 0.5)
    
    # Combine signals
    # Weight: 60% algorithmic (objective), 40% LLM (subjective reasoning)
    direction_scores = {'BUY': 1, 'HOLD': 0, 'SELL': -1}
    
    algo_score = direction_scores.get(algo_direction, 0) * algo_confidence
    llm_score = direction_scores.get(llm_direction, 0) * llm_confidence
    
    weighted_score = (algo_score * 0.6 + llm_score * 0.4)
    
    if weighted_score > 0.3:
        final_direction = 'BUY'
    elif weighted_score < -0.3:
        final_direction = 'SELL'
    else:
        final_direction = 'HOLD'
    
    final_confidence = (algo_confidence * 0.6 + llm_confidence * 0.4)
    
    # Get entry/exit levels
    entry_price = None
    stop_loss = None
    target_price = None
    
    # Prefer algorithmic levels if available
    if algorithmic_detection.get('patterns_detected'):
        best_pattern = max(algorithmic_detection['patterns_detected'], 
                          key=lambda x: x.get('confidence', 0))
        entry_price = best_pattern.get('entry_price')
        stop_loss = best_pattern.get('stop_loss')
        target_price = best_pattern.get('target_price')
    elif llm_signal:
        entry_price = llm_signal.get('entry_price')
        stop_loss = llm_signal.get('stop_loss')
        target_price = llm_signal.get('target_price')
    
    # Calculate risk/reward
    if entry_price and stop_loss and target_price:
        risk = abs(entry_price - stop_loss)
        reward = abs(target_price - entry_price)
        risk_reward = reward / risk if risk > 0 else 0
    else:
        risk_reward = 0
    
    combined['combined_signal'] = {
        'direction': final_direction,
        'confidence': round(final_confidence, 2),
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'target_price': target_price,
        'risk_reward_ratio': round(risk_reward, 2),
        'algorithmic_signal': algo_direction,
        'algorithmic_confidence': algo_confidence,
        'llm_signal': llm_direction,
        'llm_confidence': llm_confidence,
        'agreement': algo_direction == llm_direction,
        'reasoning': generate_combined_reasoning(algorithmic_detection, llm_analysis, final_direction)
    }
    
    return combined


def generate_combined_reasoning(algo: Dict, llm: Dict, final_direction: str) -> str:
    """Generate human-readable reasoning for combined signal"""
    parts = []
    
    # Algorithmic patterns
    patterns = algo.get('patterns_detected', [])
    if patterns:
        pattern_names = [p['pattern'] for p in patterns[:3]]
        parts.append(f"Algorithmic detection found: {', '.join(pattern_names)}.")
    
    # Volume analysis
    vol_analysis = algo.get('volume_analysis', {})
    if vol_analysis.get('interpretation'):
        parts.append(f"Volume analysis: {vol_analysis['interpretation']}.")
    
    # LLM reasoning
    if 'reasoning' in llm:
        parts.append(f"LLM analysis: {llm['reasoning'][:200]}...")
    
    # Agreement/disagreement
    algo_sig = algo.get('overall_signal', {}).get('direction', 'HOLD')
    llm_sig = llm.get('signal', {}).get('direction', 'HOLD')
    
    if algo_sig == llm_sig:
        parts.append(f"Both algorithmic and LLM analysis agree on {final_direction}.")
    else:
        parts.append(f"Algorithmic ({algo_sig}) and LLM ({llm_sig}) signals differ; weighted average used.")
    
    return " ".join(parts)


def test_api_key() -> Dict:
    """Test if API key is working"""
    messages = [
        {"role": "user", "content": "Hello, this is a test message. Please respond with 'API working' if you receive this."}
    ]
    
    result = call_openrouter(messages, max_tokens=50)
    
    if 'error' in result:
        return {
            'status': 'failed',
            'error': result['error']
        }
    
    response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    return {
        'status': 'success',
        'response': response_text,
        'model_used': result.get('model', 'unknown')
    }


if __name__ == '__main__':
    print("🧪 Testing OpenRouter API...")
    print()
    
    # Test API key
    test_result = test_api_key()
    print(f"API Test: {test_result['status'].upper()}")
    if test_result['status'] == 'success':
        print(f"Response: {test_result['response']}")
        print(f"Model: {test_result['model_used']}")
    else:
        print(f"Error: {test_result.get('error', 'Unknown error')}")
    
    print()
    print("✅ OpenRouter analyzer module loaded successfully")
