import os
import json
import subprocess
import requests
import time

PROMETHEUS_URL = "http://localhost:9090"
LAST_KNOWN_GOOD_VERSION = "v2"
AI_API_KEY = os.environ.get("AI_API_KEY")
BASELINE_LATENCY = 0.050  # 50 ms baseline

def get_prometheus_metric(query):
    try:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        data = response.json()
        if data["status"] == "success" and data["data"]["result"]:
            return float(data["data"]["result"][0]["value"][1])
        return None
    except Exception as e:
        print(f"Error fetching metric {query}: {e}")
        return None

def collect_metrics():
    # Get current average latency for /api/data over the last 1 minute
    latency_query = 'rate(flask_http_request_duration_seconds_sum{path="/api/data"}[1m]) / rate(flask_http_request_duration_seconds_count{path="/api/data"}[1m])'
    current_latency = get_prometheus_metric(latency_query)
    
    # Get error rate (5xx errors)
    error_query = 'sum(rate(flask_http_request_total{status=~"5.."}[1m]))'
    error_rate = get_prometheus_metric(error_query) or 0.0

    return {
        "current_response_time_seconds": current_latency,
        "baseline_response_time_seconds": BASELINE_LATENCY,
        "error_rate": error_rate,
        "last_known_good_version": LAST_KNOWN_GOOD_VERSION
    }

def analyze_with_ai(metrics):
    if not AI_API_KEY:
        print("Warning: AI_API_KEY environment variable not set. Using mocked AI response.")
        # Mock logic for tests and when key is not provided
        if metrics.get("current_response_time_seconds") and metrics["current_response_time_seconds"] > 1.0:
            return {
                "decision": "ROLLBACK",
                "confidence": 0.98,
                "reason": f"Latency of {metrics['current_response_time_seconds']:.2f}s severely exceeds baseline."
            }
        return {
            "decision": "KEEP",
            "confidence": 0.95,
            "reason": "Metrics are within healthy bounds."
        }

    prompt = f"""
You are an AI DevOps analyzer determining if an automatic rollback is necessary.
You must strictly return ONLY a JSON response in the exact format shown below, with no markdown formatting or extra text.
Format: {{"decision": "KEEP"|"ROLLBACK", "confidence": <float>, "reason": "<string>"}}

Here is the current deployment health data:
Current Response Time: {metrics.get('current_response_time_seconds', 'Unknown')} seconds
Baseline Response Time: {metrics.get('baseline_response_time_seconds')} seconds
Error Rate: {metrics.get('error_rate')} errors/sec
Last Known Good Version: {metrics.get('last_known_good_version')}

Analyze this data. A rollback should only be triggered if response times have severely degraded (e.g., > 10x baseline) or error rates are high.
Do not invent metrics.
"""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={AI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Parse Gemini response
        response_json = response.json()
        raw_text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        
        # Strip markdown if present
        if raw_text.startswith("```json"):
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
        return json.loads(raw_text)
    except Exception as e:
        print(f"Failed to query AI: {e}")
        return {"decision": "KEEP", "confidence": 0.0, "reason": "Error contacting AI API"}

def execute_rollback():
    print(f"Executing rollback to {LAST_KNOWN_GOOD_VERSION}...")
    try:
        # We assume docker images for different versions exist.
        # Overriding the APP_VERSION env var forces docker-compose to use the v2 image.
        env = os.environ.copy()
        env["APP_VERSION"] = LAST_KNOWN_GOOD_VERSION
        subprocess.run(["docker-compose", "up", "-d", "--no-build", "--force-recreate", "web"], env=env, check=True)
        print("Rollback executed successfully!")
        
        # Wait a moment for container to start
        time.sleep(2)
        health_resp = requests.get("http://localhost:5000/health")
        print(f"Health check after rollback: {health_resp.json()}")
    except Exception as e:
        print(f"Rollback failed: {e}")

if __name__ == "__main__":
    print("Collecting metrics...")
    metrics = collect_metrics()
    print(f"Metrics: {json.dumps(metrics, indent=2)}")
    
    print("Asking AI for decision...")
    decision_data = analyze_with_ai(metrics)
    print(f"AI Decision: {json.dumps(decision_data, indent=2)}")
    
    if decision_data.get("decision") == "ROLLBACK" and decision_data.get("confidence", 0) > 0.8:
        execute_rollback()
    else:
        print("Keeping current deployment.")
