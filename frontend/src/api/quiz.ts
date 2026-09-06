import axios from 'axios'

const API_BASE = '/api/v1'

export interface QuizQuestion {
  question: string
  options: string[]
  correct_answer: string
  difficulty: string
  explanation: string
  source_page: number
}

export interface QuizResponse {
  quiz_id: string
  questions: QuizQuestion[]
  total_questions: number
  estimated_time_minutes: number
}

export async function generateQuiz(
  documentId: string,
  userId: string,
  numQuestions: number,
  difficulty?: string,
  topic?: string
): Promise<QuizResponse> {
  const response = await axios.post(`${API_BASE}/quiz/generate`, {
    document_id: documentId,
    user_id: userId,
    num_questions: numQuestions,
    difficulty: difficulty || null,
    topic: topic || null,
  })

  return response.data
}

export async function generateQuizByTopic(
  topic: string,
  userId: string,
  numQuestions: number = 5,
  difficulty?: string
): Promise<QuizResponse> {
  const response = await axios.post(`${API_BASE}/quiz/generate-topic`, null, {
    params: {
      topic,
      user_id: userId,
      num_questions: numQuestions,
      difficulty,
    },
  })

  return response.data
}
