import axios from 'axios'

const API_BASE = '/api/v1'

export interface DocumentUploadResponse {
  document_id: string
  filename: string
  status: string
  total_pages: number
  message: string
}

export async function uploadDocument(file: File, userId: string): Promise<DocumentUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', userId)

  const response = await axios.post(`${API_BASE}/documents/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

export async function deleteDocument(documentId: string, userId: string): Promise<void> {
  await axios.delete(`${API_BASE}/documents/${documentId}`, {
    params: { user_id: userId },
  })
}

export async function getDocumentInfo(documentId: string, userId: string): Promise<any> {
  const response = await axios.get(`${API_BASE}/documents/${documentId}/info`, {
    params: { user_id: userId },
  })
  return response.data
}
