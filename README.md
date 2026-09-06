# Sarkari AI - Intelligent Exam Prep Assistant

> **Status:** ✅ MVP Complete | 🚀 Ready for Beta Testing

RAG + Agent-based AI assistant for competitive exam aspirants preparing for UPSC, MPSC, SSC, Banking, and Railways exams in India.

## 🎯 Problem Statement

Students preparing for government exams struggle with:
- Scattered PDFs (syllabi, past papers, notifications)
- Scanned circulars in Hindi/Marathi with poor OCR
- Complex eligibility criteria across multiple documents
- No centralized way to query study material
- Expensive test series (₹500-5000/year)

**Sarkari AI Solution:** Upload PDFs once → Ask unlimited questions → Get answers with page citations → Generate practice quizzes

## ✨ What Makes This Different?

1. **Built for Indic Languages:** OCR support for Hindi/Marathi scanned government circulars
2. **Cost-Optimized:** Gemini Flash-8B keeps costs near-zero (10x cheaper than GPT-4)
3. **Page-Level Citations:** Every answer cites exact page numbers for verification
4. **Smart Query Routing:** LangGraph automatically classifies and routes queries
5. **Proven Market:** Test series market already exists at ₹500-5000/year

## Tech Stack

### Backend Services
- **FastAPI (ML/RAG Service)**: PDF processing, OCR, embeddings, retrieval, LLM orchestration
- **Spring Boot (Core Service)**: Authentication, billing, user management, document metadata
- **PostgreSQL**: User data, document metadata, usage tracking
- **Redis**: Rate limiting, caching
- **Qdrant**: Vector database for semantic search
- **S3-compatible storage**: PDF storage (Backblaze B2)

### ML Pipeline
- **PDF Parsing**: PyMuPDF + ChandraOCR (PaddleOCR + EasyOCR ensemble)
- **Embeddings**: bge-m3 (multilingual: English/Hindi/Marathi)
- **Retrieval**: Hybrid dense+sparse with RRF fusion
- **Reranker**: bge-reranker-base
- **Orchestration**: LangGraph (query routing, multi-page reasoning)
- **LLM**: Gemini 1.5 Flash / Flash-8B (cost-optimized)

### Frontend
- **React**: Upload interface, chat UI, PDF viewer with citations
- **TanStack Query**: API state management
- **Tailwind CSS**: Styling

## Features (MVP - MPSC Focus)

### Phase 1 (Current)
- ✅ User PDF upload with advanced OCR (PaddleOCR + EasyOCR) for scanned documents
- ✅ Semantic search with page-level citations
- ✅ Multi-page reasoning (summarization, synthesis)
- ✅ Per-user document isolation
- ✅ Rate limiting (free: 3 queries/day)

### Phase 2 (Next)
- [ ] Eligibility extraction from notification PDFs
- [ ] Quiz generation from uploaded content
- [ ] WhatsApp bot interface
- [ ] Premium subscription (₹99-199/month)

## Project Structure

```
sarkari-ai/
├── services/
│   ├── rag-service/          # FastAPI - ML/RAG pipeline
│   ├── core-service/         # Spring Boot - Auth/billing
│   └── shared/               # Shared models, utilities
├── frontend/                 # React application
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Java 17+
- Docker & Docker Compose
- Gemini API key

### Development Setup

1. **Clone and setup environment**
```bash
# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

2. **Start infrastructure services**
```bash
docker-compose up -d postgres redis qdrant
```

3. **Start RAG service (FastAPI)**
```bash
cd services/rag-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

4. **Start Core service (Spring Boot)**
```bash
cd services/core-service
./mvnw spring-boot:run
```

5. **Start Frontend**
```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:5173

## Architecture Highlights

### PDF Processing Pipeline
1. **Native text extraction** (PyMuPDF) - fast path
2. **OCR fallback** (ChandraOCR) - only for scanned pages
3. **Semantic chunking** - structure-aware, 500-800 tokens
4. **Embedding + storage** - per-user Qdrant collections

### Query Processing (LangGraph)
```
User Query
    ├─→ Classifier Node (query type detection)
    ├─→ Simple Q&A Node (top-k retrieval + rerank + answer)
    ├─→ Multi-page Synthesis Node (map-reduce)
    │       ├─→ Metadata Filter (chapter/section)
    │       ├─→ Parallel Chunk Summarization
    │       └─→ Final Synthesis
    └─→ Eligibility Check Node (structured extraction)
```

### Cost Optimization
- Embedding cache (per document hash)
- Gemini Flash-8B default, escalate to Pro only for complex queries
- Rate limit by pages processed (OCR is primary cost driver)
- Free tier: 3 queries/day, 50 pages/month

## Monetization

### C2C Freemium
- **Free**: 3 queries/day, basic features
- **Premium** (₹99-199/month): Unlimited queries, personalized tracking, quiz generation

### B2B (Future)
- License RAG pipeline to coaching institutes
- Custom deployment for content providers

## Roadmap

**Week 1-2**: PDF upload + Q&A (current focus)  
**Week 3-4**: Eligibility extraction + quiz generation  
**Week 5-6**: WhatsApp bot + payment integration  
**Post-MVP**: Expand to other states/exams, B2B partnerships

## Contributing
This is a solo MVP project. Contributions welcome post-launch.

## License
Proprietary - All rights reserved
