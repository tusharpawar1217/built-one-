#!/bin/bash
# Start all services in development mode

set -e

echo "🚀 Starting Sarkari AI in development mode..."

# Start infrastructure
echo "🐳 Starting infrastructure services..."
docker-compose up -d postgres redis qdrant

# Wait for services
sleep 5

# Start RAG service in background
echo "🔧 Starting RAG service..."
cd services/rag-service
source venv/bin/activate || . venv/Scripts/activate
uvicorn app.main:app --reload --port 8000 &
RAG_PID=$!
cd ../..

# Start frontend in background
echo "🎨 Starting frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "Services:"
echo "  - RAG API: http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "  - Qdrant: http://localhost:6333"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to stop all services
trap "echo ''; echo '🛑 Stopping services...'; kill $RAG_PID $FRONTEND_PID 2>/dev/null; docker-compose stop; exit" INT

# Wait for user to stop
wait
