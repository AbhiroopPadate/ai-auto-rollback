from flask import Flask, jsonify
import time
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI DevOps Automatic Rollback Demo</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f9;
                color: #333;
                text-align: center;
                padding: 50px;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                display: inline-block;
            }
            h1 {
                color: #2c3e50;
            }
            .status {
                color: #27ae60;
                font-weight: bold;
            }
            .version {
                color: #7f8c8d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>AI DevOps Automatic Rollback Demo</h1>
            <p class="version">Version: v1</p>
            <p>Status: <span class="status">Healthy</span></p>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": "v1"
    })

@app.route('/api/data')
def api_data():
    return jsonify({
        "success": True,
        "data": [
            {"id": 101, "item": "CPU Usage", "value": "45%"},
            {"id": 102, "item": "Memory Usage", "value": "60%"}
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
