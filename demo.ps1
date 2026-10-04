# Demo script to demonstrate AI Automatic Rollback
Write-Host "=========================================="
Write-Host "🚀 AI DevOps Automatic Rollback Demo"
Write-Host "=========================================="

# Set the AI API Key (Set this in your terminal before running, or configure it here)
# $env:AI_API_KEY="your-gemini-key"

# Ensure both images exist before we begin
Write-Host "`n[1/5] Building Docker images for v2 (Healthy) and v3 (Degraded)..."
# Check out v2 tag to build the healthy image
git checkout v2
docker build -t ai-auto-rollback-web:v2 .

# Return to main (which contains v3 with AI capability)
git checkout main
$env:APP_VERSION="v3"
docker build -t ai-auto-rollback-web:v3 .

Write-Host "`n[2/5] Deploying Degraded Version 3..."
docker-compose up -d --no-build --force-recreate web
Start-Sleep -Seconds 5

$health = Invoke-RestMethod http://localhost:5000/health
Write-Host "Deployed Version: $($health.version)"

Write-Host "`n[3/5] Starting load generation to populate Prometheus metrics..."
$locustJob = Start-Job -ScriptBlock { 
    a:\ai-auto-rollback\venv\Scripts\locust.exe --headless -u 10 -r 2 -t 15s --host http://localhost:5000
}
# Wait a bit for metrics to accumulate
Write-Host "Simulating traffic and waiting 15 seconds for metrics to accumulate..."
for ($i=15; $i -gt 0; $i--) {
    Write-Host -NoNewline "$i "
    Start-Sleep -Seconds 1
}
Write-Host ""

Write-Host "`n[4/5] Running AI Analyzer to check deployment health..."
a:\ai-auto-rollback\venv\Scripts\python.exe ai_analyzer.py

Write-Host "`n[5/5] Verification"
$health = Invoke-RestMethod http://localhost:5000/health
Write-Host "Currently running version: $($health.version)"

$time = Measure-Command { Invoke-RestMethod http://localhost:5000/api/data } | Select-Object -ExpandProperty TotalSeconds
Write-Host "Current /api/data latency: $($time) seconds"

if ($health.version -eq "v2") {
    Write-Host "`n✅ DEMO SUCCESS: Automatically rolled back to a healthy state!" -ForegroundColor Green
} else {
    Write-Host "`n❌ DEMO FAILED: Application is still running degraded version." -ForegroundColor Red
}
