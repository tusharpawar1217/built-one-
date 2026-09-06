#!/bin/bash
# Setup script for Sarkari AI development environment

set -e

echo "🚀 Setting up Sarkari AI development environment..."

# Check prerequisites
echo "✓ Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

echo "✓ Prerequisites check passed"

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before continuing"
    echo "   Required: GOOGLE_API_KEY, S3 credentials"
    exit 0
fi

# Start infrastructure services
echo "🐳 Starting infrastructure services (Postgres, Redis, Qdrant)..."
docker-compose up -d postgres redis qdrant

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Setup RAG service
echo "🔧 Setting up RAG service..."
cd services/rag-service

if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "  Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

echo "  Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "  Downloading ML models (this may take a while)..."
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
python -c "from FlagEmbedding import FlagReranker; FlagReranker('BAAI/bge-reranker-base')"

cd ../..

# Setup frontend
echo "🎨 Setting up frontend..."
cd frontend

echo "  Installing Node dependencies..."
npm install

cd ..

echo "✅ Setup complete!"
echo ""
echo "📚 Next steps:"
echo "  1. Ensure .env file has your GOOGLE_API_KEY and S3 credentials"
echo "  2. Start the RAG service: cd services/rag-service && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  3. Start the frontend: cd frontend && npm run dev"
echo "  4. Open http://localhost:5173 in your browser"
echo ""
echo "📖 See README.md for more information"
