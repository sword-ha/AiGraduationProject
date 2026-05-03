$base = "c:\Users\eidh7\Desktop\grad\api_services"

$services = @(
    @{ name = "ID Verification  (8001)"; dir = "$base\id_verification";  port = 8001 },
    @{ name = "Personality      (8002)"; dir = "$base\personality";       port = 8002 },
    @{ name = "CV Generator     (8003)"; dir = "$base\cv_generator";      port = 8003 },
    @{ name = "Chatbot          (8004)"; dir = "$base\chatbot";           port = 8004 },
    @{ name = "Post Generator   (8005)"; dir = "$base\post_generator";    port = 8005 }
)

foreach ($svc in $services) {
    Write-Host "Starting $($svc.name)..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$($svc.dir)'; uvicorn main:app --port $($svc.port) --log-level info"
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "All services started!" -ForegroundColor Green
Write-Host "Swagger UI links:" -ForegroundColor Yellow
Write-Host "  http://localhost:8001/docs  (ID Verification)"
Write-Host "  http://localhost:8002/docs  (Personality)"
Write-Host "  http://localhost:8003/docs  (CV Generator)"
Write-Host "  http://localhost:8004/docs  (Chatbot)"
Write-Host "  http://localhost:8005/docs  (Post Generator)"
