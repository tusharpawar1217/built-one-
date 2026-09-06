# Start all services in development mode (Windows PowerShell)

Write-Host "🚀 Starting Sarkari AI in development mode..." -ForegroundColor Cyan

# Start infrastructure
Write-Host "🐳 Starting infrastructure services..." -ForegroundColor Cyan
docker-compose up -d postgres redis qdrant

# Wait for services
Start-Sleep -Seconds 5

# Start RAG service in new window
Write-Host "🔧 Starting RAG service..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd services\rag-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000"

# Start frontend in new window
Write-Host "🎨 Starting frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "✅ All services started!" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
Write-Host "  - RAG API: http://localhost:8000"
Write-Host "  - Frontend: http://localhost:5173"
Write-Host "  - Qdrant: http://localhost:6333"
Write-Host ""
Write-Host "Close the terminal windows to stop services" -ForegroundColor Yellow
