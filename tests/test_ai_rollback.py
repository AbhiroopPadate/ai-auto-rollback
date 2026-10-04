import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ai_analyzer

def test_collect_metrics_healthy():
    with patch('ai_analyzer.get_prometheus_metric') as mock_get:
        # Mocking low latency and no errors
        mock_get.side_effect = [0.05, 0.0]
        
        metrics = ai_analyzer.collect_metrics()
        
        assert metrics['current_response_time_seconds'] == 0.05
        assert metrics['error_rate'] == 0.0
        assert metrics['last_known_good_version'] == 'v2'

def test_collect_metrics_degraded():
    with patch('ai_analyzer.get_prometheus_metric') as mock_get:
        # Mocking high latency and no errors
        mock_get.side_effect = [3.05, 0.0]
        
        metrics = ai_analyzer.collect_metrics()
        
        assert metrics['current_response_time_seconds'] == 3.05

@patch('ai_analyzer.AI_API_KEY', None)
def test_analyze_with_ai_mock_keep():
    # If API key is not set, it uses mock logic
    metrics = {
        "current_response_time_seconds": 0.06,
        "baseline_response_time_seconds": 0.05,
        "error_rate": 0.0,
        "last_known_good_version": "v2"
    }
    decision = ai_analyzer.analyze_with_ai(metrics)
    assert decision["decision"] == "KEEP"
    assert decision["confidence"] > 0.8

@patch('ai_analyzer.AI_API_KEY', None)
def test_analyze_with_ai_mock_rollback():
    metrics = {
        "current_response_time_seconds": 3.10,
        "baseline_response_time_seconds": 0.05,
        "error_rate": 0.0,
        "last_known_good_version": "v2"
    }
    decision = ai_analyzer.analyze_with_ai(metrics)
    assert decision["decision"] == "ROLLBACK"
    assert decision["confidence"] > 0.8

@patch('ai_analyzer.requests.post')
@patch('ai_analyzer.AI_API_KEY', 'fake_key')
def test_analyze_with_ai_real_api(mock_post):
    metrics = {
        "current_response_time_seconds": 3.10,
        "baseline_response_time_seconds": 0.05,
        "error_rate": 0.0,
        "last_known_good_version": "v2"
    }
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '```json\n{"decision": "ROLLBACK", "confidence": 0.99, "reason": "High latency"}\n```'}
                    ]
                }
            }
        ]
    }
    mock_post.return_value = mock_response
    
    decision = ai_analyzer.analyze_with_ai(metrics)
    assert decision["decision"] == "ROLLBACK"
    assert decision["confidence"] == 0.99
