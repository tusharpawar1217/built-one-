import axios from 'axios'
import type { QueryResponse } from '../types'

const API_BASE = '/api/v1'

export async function queryDocuments(
  query: string,
  userId: string,
  documentIds: string[],
  conversationHistory?: Array<{ role: string; content: string }>
): Promise<QueryResponse> {
  const response = await axios.post(`${API_BASE}/query`, {
    query,
    user_id: userId,
    document_ids: documentIds,
    user_tier: 'free',
    conversation_history: conversationHistory?.map(msg => ({
      role: msg.role,
      content: msg.content,
    })),
  })

  return response.data
}
