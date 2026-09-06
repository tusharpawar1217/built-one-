# Setup script for Sarkari AI development environment (Windows PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up Sarkari AI development environment..." -ForegroundColor Cyan

# Check prerequisites
Write-Host "✓ Checking prerequisites..." -ForegroundColor Green

try {
    python --version | Out-Null
} catch {
    Write-Host "❌ Python 3 is required but not installed" -ForegroundColor Red
    exit 1
}

try {
    node --version | Out-Null
} catch {
    Write-Host "❌ Node.js is required but not installed" -ForegroundColor Red
    exit 1
}

try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker is required but not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Prerequisites check passed" -ForegroundColor Green

# Create environment file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env file with your API keys before continuing" -ForegroundColor Yellow
    Write-Host "   Required: GOOGLE_API_KEY, S3 credentials" -ForegroundColor Yellow
    exit 0
}

# Start infrastructure services
Write-Host "🐳 Starting infrastructure services (Postgres, Redis, Qdrant)..." -ForegroundColor Cyan
docker-compose up -d postgres redis qdrant

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Setup RAG service
Write-Host "🔧 Setting up RAG service..." -ForegroundColor Cyan
Set-Location services\rag-service

if (-not (Test-Path venv)) {
    Write-Host "  Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "  Activating virtual environment..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

Write-Host "  Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "  Downloading ML models (this may take a while)..." -ForegroundColor Yellow
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
python -c "from FlagEmbedding import FlagReranker; FlagReranker('BAAI/bge-reranker-base')"

Set-Location ..\..

# Setup frontend
Write-Host "🎨 Setting up frontend..." -ForegroundColor Cyan
Set-Location frontend

Write-Host "  Installing Node dependencies..." -ForegroundColor Yellow
npm install

Set-Location ..

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Next steps:" -ForegroundColor Cyan
Write-Host "  1. Ensure .env file has your GOOGLE_API_KEY and S3 credentials"
Write-Host "  2. Start the RAG service: cd services\rag-service; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload"
Write-Host "  3. Start the frontend: cd frontend; npm run dev"
Write-Host "  4. Open http://localhost:5173 in your browser"
Write-Host ""
Write-Host "📖 See README.md for more information" -ForegroundColor Cyan
