import axios from 'axios'

const API_BASE = '/api/v1/tests'

export enum ExamType {
  UPSC = 'upsc',
  MPSC = 'mpsc',
  SSC = 'ssc',
  BANKING = 'banking',
  RAILWAY = 'railway',
  STATE_PSC = 'state_psc',
  CUSTOM = 'custom',
}

export enum DifficultyLevel {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard',
  EXPERT = 'expert',
}

export enum TestMode {
  PRACTICE = 'practice',
  EXAM = 'exam',
  TIMED = 'timed',
  UNTIMED = 'untimed',
}

export enum Subject {
  GENERAL_KNOWLEDGE = 'general_knowledge',
  CURRENT_AFFAIRS = 'current_affairs',
  INDIAN_HISTORY = 'indian_history',
  INDIAN_POLITY = 'indian_polity',
  GEOGRAPHY = 'geography',
  ECONOMICS = 'economics',
  SCIENCE_TECH = 'science_tech',
  REASONING = 'reasoning',
  QUANTITATIVE = 'quantitative',
  ENGLISH = 'english',
  HINDI = 'hindi',
  MARATHI = 'marathi',
}

export interface TestMetadata {
  test_id: string
  test_series_id?: string
  name: string
  description: string
  exam_type: ExamType
  subjects: Subject[]
  total_questions: number
  total_marks: number
  duration_minutes: number
  negative_marking: boolean
  negative_marks_ratio: number
  passing_percentage: number
  difficulty_distribution: Record<string, number>
  instructions: string[]
  created_at: string
  created_by: string
}

export interface CreateTestRequest {
  name: string
  description: string
  exam_type: ExamType
  subjects: Subject[]
  duration_minutes: number
  total_questions: number
  difficulty_level: DifficultyLevel
  negative_marking: boolean
  test_series_id?: string
  user_id: string
  source_document_ids?: string[]
  topic_filter?: string
}

export interface TestAttempt {
  attempt_id: string
  test_id: string
  user_id: string
  test_metadata: TestMetadata
  started_at: string
  submitted_at?: string
  time_remaining_seconds?: number
  questions_attempted: any[]
  current_question_index: number
  is_submitted: boolean
  is_paused: boolean
  mode: TestMode
  config: any
}

export interface TestResult {
  attempt_id: string
  test_id: string
  user_id: string
  total_questions: number
  attempted: number
  correct: number
  incorrect: number
  skipped: number
  marks_obtained: number
  total_marks: number
  percentage: number
  subject_wise_analysis: Record<string, any>
  difficulty_wise_analysis: Record<string, any>
  total_time_taken_seconds: number
  average_time_per_question: number
  time_per_subject?: Record<string, number>
  rank?: number
  total_test_takers: number
  percentile?: number
  topper_score?: number
  average_score?: number
  weak_topics: string[]
  strong_topics: string[]
  improvement_suggestions: string[]
  question_wise_results: any[]
  submitted_at: string
  evaluated_at: string
}

export interface UserTestPerformance {
  user_id: string
  total_tests_taken: number
  total_tests_completed: number
  total_questions_attempted: number
  overall_accuracy: number
  average_score_percentage: number
  subject_performance: Record<string, any>
  tests_by_exam_type: Record<ExamType, number>
  improvement_trend: any[]
  strongest_subjects: string[]
  weakest_subjects: string[]
  average_time_per_question: number
  time_management_score: number
  current_streak_days: number
  longest_streak_days: number
  last_test_date?: string
  updated_at: string
}

// API Functions

export async function getExamTemplates(examType?: ExamType): Promise<any> {
  const response = await axios.get(`${API_BASE}/templates`, {
    params: { exam_type: examType },
  })
  return response.data
}

export async function createTestFromTemplate(
  templateId: string,
  userId: string,
  sourceDocumentIds?: string[]
): Promise<TestMetadata> {
  const response = await axios.post(`${API_BASE}/create-from-template`, null, {
    params: {
      template_id: templateId,
      user_id: userId,
      source_document_ids: sourceDocumentIds,
    },
  })
  return response.data
}

export async function createTest(request: CreateTestRequest): Promise<TestMetadata> {
  const response = await axios.post(`${API_BASE}/create`, request)
  return response.data
}

export async function listTests(
  examType?: ExamType,
  difficulty?: DifficultyLevel,
  page: number = 1,
  pageSize: number = 20
): Promise<{ tests: TestMetadata[]; total: number; page: number; page_size: number }> {
  const response = await axios.get(`${API_BASE}/list`, {
    params: { exam_type: examType, difficulty, page, page_size: pageSize },
  })
  return response.data
}

export async function getTest(testId: string): Promise<TestMetadata> {
  const response = await axios.get(`${API_BASE}/${testId}`)
  return response.data
}

export async function previewTest(testId: string, numQuestions: number = 3): Promise<any> {
  const response = await axios.get(`${API_BASE}/${testId}/preview`, {
    params: { num_questions: numQuestions },
  })
  return response.data
}

export async function startTest(
  testId: string,
  userId: string,
  mode: TestMode = TestMode.EXAM,
  enableCalculator: boolean = false,
  shuffleQuestions: boolean = false
): Promise<TestAttempt> {
  const response = await axios.post(`${API_BASE}/start`, {
    test_id: testId,
    user_id: userId,
    mode,
    enable_calculator: enableCalculator,
    shuffle_questions: shuffleQuestions,
  })
  return response.data
}

export async function getAttempt(attemptId: string, userId: string): Promise<TestAttempt> {
  const response = await axios.get(`${API_BASE}/attempt/${attemptId}`, {
    params: { user_id: userId },
  })
  return response.data
}

export async function getAttemptQuestions(
  attemptId: string,
  userId: string,
  includeAnswers: boolean = false
): Promise<any> {
  const response = await axios.get(`${API_BASE}/attempt/${attemptId}/questions`, {
    params: { user_id: userId, include_answers: includeAnswers },
  })
  return response.data
}

export async function submitAnswer(
  attemptId: string,
  questionId: string,
  userAnswer: string[] | null,
  numericAnswer: number | null,
  isMarkedForReview: boolean,
  timeSpentSeconds: number
): Promise<any> {
  const response = await axios.post(`${API_BASE}/attempt/${attemptId}/answer`, {
    attempt_id: attemptId,
    question_id: questionId,
    user_answer: userAnswer,
    numeric_answer: numericAnswer,
    is_marked_for_review: isMarkedForReview,
    time_spent_seconds: timeSpentSeconds,
  })
  return response.data
}

export async function submitTest(
  attemptId: string,
  userId: string,
  forceSubmit: boolean = false
): Promise<TestResult> {
  const response = await axios.post(`${API_BASE}/attempt/${attemptId}/submit`, {
    attempt_id: attemptId,
    user_id: userId,
    force_submit: forceSubmit,
  })
  return response.data
}

export async function getResult(attemptId: string, userId: string): Promise<TestResult> {
  const response = await axios.get(`${API_BASE}/result/${attemptId}`, {
    params: { user_id: userId },
  })
  return response.data
}

export async function getUserPerformance(userId: string): Promise<UserTestPerformance> {
  const response = await axios.get(`${API_BASE}/user/${userId}/performance`)
  return response.data
}

export async function getTestHistory(
  userId: string,
  examType?: ExamType,
  page: number = 1,
  pageSize: number = 20
): Promise<any> {
  const response = await axios.get(`${API_BASE}/user/${userId}/history`, {
    params: { exam_type: examType, page, page_size: pageSize },
  })
  return response.data
}

export async function getLeaderboard(
  testId: string,
  period: string = 'all_time',
  page: number = 1,
  pageSize: number = 50
): Promise<any> {
  const response = await axios.get(`${API_BASE}/${testId}/leaderboard`, {
    params: { period, page, page_size: pageSize },
  })
  return response.data
}

export async function getPlatformStats(): Promise<any> {
  const response = await axios.get(`${API_BASE}/stats/overview`)
  return response.data
}
