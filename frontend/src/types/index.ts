export interface Citation {
  document_id: string
  document_name: string
  page_number: number
  chunk_text: string
  relevance_score: number
}

export interface QueryResponse {
  answer: string
  query_type: string
  citations: Citation[]
  model_used: string
  processing_time_ms: number
  usage_info: {
    user_tier: string
    documents_searched: number
    chunks_retrieved: number
    chunks_used: number
    processing_steps: string[]
  }
}
