import { useState, useEffect } from 'react'
import {
  BookOpen,
  Clock,
  Trophy,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Bookmark,
  Calculator,
  Play,
  Pause,
  Flag,
  BarChart3,
} from 'lucide-react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  listTests,
  getTest,
  startTest,
  getAttemptQuestions,
  submitAnswer,
  submitTest,
  getUserPerformance,
  ExamType,
  DifficultyLevel,
  TestMode,
  TestMetadata,
  TestAttempt,
  TestResult,
} from '../api/tests'
import ExamTestBrowser from './ExamTestBrowser'

interface TestEnvironmentProps {
  userId: string
}

type ViewMode = 'browse' | 'instructions' | 'taking' | 'results' | 'performance'

export default function TestEnvironment({ userId }: TestEnvironmentProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('browse')
  const [selectedTest, setSelectedTest] = useState<TestMetadata | null>(null)
  const [currentAttempt, setCurrentAttempt] = useState<TestAttempt | null>(null)
  const [questions, setQuestions] = useState<any[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string[]>>({})
  const [markedForReview, setMarkedForReview] = useState<Set<string>>(new Set())
  const [timeRemaining, setTimeRemaining] = useState<number>(0)
  const [questionTime, setQuestionTime] = useState<number>(0)
  const [testResult, setTestResult] = useState<TestResult | null>(null)

  // Fetch available tests
  const { data: testsData } = useQuery({
    queryKey: ['tests', 'list'],
    queryFn: () => listTests(),
  })

  // Fetch user performance
  const { data: performanceData } = useQuery({
    queryKey: ['performance', userId],
    queryFn: () => getUserPerformance(userId),
    enabled: viewMode === 'performance',
  })

  // Start test mutation
  const startTestMutation = useMutation({
    mutationFn: (testId: string) => startTest(testId, userId, TestMode.EXAM),
    onSuccess: async (attempt) => {
      setCurrentAttempt(attempt)
      setTimeRemaining(attempt.test_metadata.duration_minutes * 60)
      
      // Fetch questions
      const questionsData = await getAttemptQuestions(attempt.attempt_id, userId)
      setQuestions(questionsData.questions)
      setViewMode('taking')
    },
  })

  // Submit test mutation
  const submitTestMutation = useMutation({
    mutationFn: () => submitTest(currentAttempt!.attempt_id, userId),
    onSuccess: (result) => {
      setTestResult(result)
      setViewMode('results')
    },
  })

  // Timer effect
  useEffect(() => {
    if (viewMode === 'taking' && timeRemaining > 0) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            // Auto-submit when time expires
            submitTestMutation.mutate()
            return 0
          }
          return prev - 1
        })
        setQuestionTime((prev) => prev + 1)
      }, 1000)
      return () => clearInterval(timer)
    }
  }, [viewMode, timeRemaining])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const handleSelectAnswer = (questionId: string, option: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: [option],
    }))
  }

  const handleMarkForReview = (questionId: string) => {
    setMarkedForReview((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(questionId)) {
        newSet.delete(questionId)
      } else {
        newSet.add(questionId)
      }
      return newSet
    })
  }

  const handleNextQuestion = async () => {
    const currentQuestion = questions[currentQuestionIndex]
    
    // Submit current answer
    if (currentAttempt) {
      await submitAnswer(
        currentAttempt.attempt_id,
        currentQuestion.question_id,
        answers[currentQuestion.question_id] || null,
        null,
        markedForReview.has(currentQuestion.question_id),
        questionTime
      )
    }

    setQuestionTime(0)
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
    }
  }

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setQuestionTime(0)
      setCurrentQuestionIndex(currentQuestionIndex - 1)
    }
  }

  const handleSubmitTest = () => {
    if (window.confirm('Are you sure you want to submit the test?')) {
      submitTestMutation.mutate()
    }
  }

  // Browse Tests View
  if (viewMode === 'browse') {
    return (
      <ExamTestBrowser
        userId={userId}
        onTestCreated={async (testId) => {
          // Fetch the created test and show instructions
          const test = await getTest(testId)
          setSelectedTest(test)
          setViewMode('instructions')
        }}
      />
    )
  }

  // Instructions View
  if (viewMode === 'instructions' && selectedTest) {
    return (
      <div className="max-w-3xl mx-auto space-y-6">
        <button
          onClick={() => setViewMode('browse')}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          ← Back to Tests
        </button>

        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{selectedTest.name}</h2>
              <p className="text-sm text-gray-600 mt-1">{selectedTest.description}</p>
            </div>
            <span className="px-3 py-1 bg-primary-100 text-primary-700 text-xs font-medium rounded-full">
              {selectedTest.exam_type.toUpperCase()}
            </span>
          </div>

          {/* Test Details */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <BookOpen className="w-5 h-5 text-primary-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-gray-900">{selectedTest.total_questions}</p>
              <p className="text-xs text-gray-600">Questions</p>
            </div>
            <div className="text-center">
              <Clock className="w-5 h-5 text-primary-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-gray-900">{selectedTest.duration_minutes}</p>
              <p className="text-xs text-gray-600">Minutes</p>
            </div>
            <div className="text-center">
              <Trophy className="w-5 h-5 text-primary-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-gray-900">{selectedTest.total_marks}</p>
              <p className="text-xs text-gray-600">Marks</p>
            </div>
            <div className="text-center">
              <AlertCircle className="w-5 h-5 text-red-600 mx-auto mb-1" />
              <p className="text-sm font-medium text-gray-900">-{selectedTest.negative_marks_ratio}</p>
              <p className="text-xs text-gray-600">Negative</p>
            </div>
          </div>

          {/* Instructions */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Instructions:</h3>
            <ul className="space-y-2">
              {selectedTest.instructions.map((instruction, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                  <span className="text-sm text-gray-700">{instruction}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Start Button */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <button
              onClick={() => startTestMutation.mutate(selectedTest.test_id)}
              disabled={startTestMutation.isPending}
              className="btn-primary w-full flex items-center justify-center space-x-2"
            >
              {startTestMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Starting Test...</span>
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  <span>Start Test</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Test Taking View
  if (viewMode === 'taking' && currentAttempt && questions.length > 0) {
    const currentQuestion = questions[currentQuestionIndex]
    const answered = Object.keys(answers).length
    const markedCount = markedForReview.size

    return (
      <div className="h-full flex flex-col">
        {/* Header with Timer */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center space-x-4">
              <h2 className="font-semibold text-gray-900">{currentAttempt.test_metadata.name}</h2>
              <span className="text-sm text-gray-600">
                Question {currentQuestionIndex + 1} / {questions.length}
              </span>
            </div>
            <div className="flex items-center space-x-6">
              <div className={`flex items-center space-x-2 ${timeRemaining < 300 ? 'text-red-600' : 'text-gray-700'}`}>
                <Clock className="w-5 h-5" />
                <span className="font-mono font-semibold">{formatTime(timeRemaining)}</span>
              </div>
              <button
                onClick={handleSubmitTest}
                className="btn-primary"
              >
                <Flag className="w-4 h-4 mr-2" />
                Submit Test
              </button>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-5xl mx-auto p-6 grid grid-cols-4 gap-6">
            {/* Main Question Area */}
            <div className="col-span-3 space-y-6">
              <div className="card">
                {/* Question Header */}
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
                  <div className="flex items-center space-x-3">
                    <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
                      {currentQuestion.subject.replace(/_/g, ' ').toUpperCase()}
                    </span>
                    <span className="px-3 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">
                      {currentQuestion.difficulty}
                    </span>
                    <span className="text-sm text-gray-600">
                      {currentQuestion.marks} {currentQuestion.marks === 1 ? 'Mark' : 'Marks'}
                    </span>
                  </div>
                  <button
                    onClick={() => handleMarkForReview(currentQuestion.question_id)}
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg transition-colors ${
                      markedForReview.has(currentQuestion.question_id)
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <Bookmark className="w-4 h-4" />
                    <span className="text-sm">Mark for Review</span>
                  </button>
                </div>

                {/* Question Text */}
                <h3 className="text-lg font-medium text-gray-900 mb-6">
                  {currentQuestion.question_text}
                </h3>

                {/* Options */}
                <div className="space-y-3">
                  {currentQuestion.options?.map((option: string, idx: number) => (
                    <button
                      key={idx}
                      onClick={() => handleSelectAnswer(currentQuestion.question_id, option)}
                      className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                        answers[currentQuestion.question_id]?.[0] === option
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200 hover:border-gray-300 bg-white'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full border-2 border-current">
                          {String.fromCharCode(65 + idx)}
                        </span>
                        <span className="flex-1">{option}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePreviousQuestion}
                  disabled={currentQuestionIndex === 0}
                  className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ← Previous
                </button>

                <div className="text-sm text-gray-600">
                  <span className="font-medium text-green-600">{answered}</span> answered,{' '}
                  <span className="font-medium text-yellow-600">{markedCount}</span> marked
                </div>

                <button
                  onClick={handleNextQuestion}
                  className="btn-primary"
                >
                  {currentQuestionIndex === questions.length - 1 ? 'Review →' : 'Next →'}
                </button>
              </div>
            </div>

            {/* Question Palette */}
            <div className="col-span-1">
              <div className="card sticky top-6">
                <h3 className="font-semibold text-gray-900 mb-4">Question Palette</h3>
                <div className="grid grid-cols-4 gap-2">
                  {questions.map((q: any, idx: number) => {
                    const isAnswered = answers[q.question_id] !== undefined
                    const isMarked = markedForReview.has(q.question_id)
                    const isCurrent = idx === currentQuestionIndex

                    return (
                      <button
                        key={q.question_id}
                        onClick={() => setCurrentQuestionIndex(idx)}
                        className={`w-full aspect-square flex items-center justify-center rounded-lg text-sm font-medium transition-all ${
                          isCurrent
                            ? 'bg-primary-600 text-white ring-2 ring-primary-300'
                            : isAnswered && isMarked
                            ? 'bg-yellow-100 text-yellow-700'
                            : isAnswered
                            ? 'bg-green-100 text-green-700'
                            : isMarked
                            ? 'bg-orange-100 text-orange-700'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {idx + 1}
                      </button>
                    )
                  })}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 space-y-2 text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-green-100 rounded" />
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-yellow-100 rounded" />
                    <span>Marked</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 bg-gray-100 rounded" />
                    <span>Not Visited</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Results View
  if (viewMode === 'results' && testResult) {
    const percentage = testResult.percentage
    const passed = percentage >= testResult.percentage

    return (
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Score Card */}
        <div className="card text-center">
          <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4 ${
            percentage >= 75 ? 'bg-green-100' : percentage >= 50 ? 'bg-yellow-100' : 'bg-red-100'
          }`}>
            <Trophy className={`w-12 h-12 ${
              percentage >= 75 ? 'text-green-600' : percentage >= 50 ? 'text-yellow-600' : 'text-red-600'
            }`} />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            {testResult.percentage.toFixed(2)}%
          </h2>
          <p className="text-lg text-gray-600 mb-1">
            {testResult.marks_obtained.toFixed(2)} / {testResult.total_marks} Marks
          </p>
          <p className="text-sm text-gray-500">
            {testResult.correct} correct, {testResult.incorrect} incorrect, {testResult.skipped} skipped
          </p>
        </div>

        {/* Subject-wise Analysis */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Subject-wise Performance</h3>
          <div className="space-y-3">
            {Object.entries(testResult.subject_wise_analysis).map(([subject, stats]: [string, any]) => (
              <div key={subject}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">
                    {subject.replace(/_/g, ' ').toUpperCase()}
                  </span>
                  <span className="text-sm text-gray-600">
                    {stats.correct} / {stats.total} ({stats.accuracy.toFixed(0)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      stats.accuracy >= 75 ? 'bg-green-500' : stats.accuracy >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${stats.accuracy}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Improvement Suggestions */}
        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Recommendations</h3>
          <ul className="space-y-2">
            {testResult.improvement_suggestions.map((suggestion, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <TrendingUp className="w-4 h-4 text-primary-600 flex-shrink-0 mt-0.5" />
                <span className="text-sm text-gray-700">{suggestion}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex space-x-4">
          <button
            onClick={() => setViewMode('browse')}
            className="btn-secondary flex-1"
          >
            Back to Tests
          </button>
          <button
            onClick={() => setViewMode('performance')}
            className="btn-primary flex-1"
          >
            View Performance
          </button>
        </div>
      </div>
    )
  }

  // Performance View
  if (viewMode === 'performance' && performanceData) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setViewMode('browse')}
          className="text-sm text-gray-600 hover:text-gray-900"
        >
          ← Back to Tests
        </button>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card text-center">
            <BookOpen className="w-8 h-8 text-primary-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{performanceData.total_tests_completed}</p>
            <p className="text-sm text-gray-600">Tests Completed</p>
          </div>
          <div className="card text-center">
            <Trophy className="w-8 h-8 text-yellow-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{performanceData.average_score_percentage.toFixed(1)}%</p>
            <p className="text-sm text-gray-600">Avg Score</p>
          </div>
          <div className="card text-center">
            <CheckCircle2 className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{performanceData.overall_accuracy.toFixed(1)}%</p>
            <p className="text-sm text-gray-600">Accuracy</p>
          </div>
          <div className="card text-center">
            <TrendingUp className="w-8 h-8 text-blue-600 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{performanceData.current_streak_days}</p>
            <p className="text-sm text-gray-600">Day Streak</p>
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Strongest Subjects</h3>
          <div className="flex flex-wrap gap-2">
            {performanceData.strongest_subjects.map((subject) => (
              <span key={subject} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                {subject.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 className="font-semibold text-gray-900 mb-4">Areas to Improve</h3>
          <div className="flex flex-wrap gap-2">
            {performanceData.weakest_subjects.map((subject) => (
              <span key={subject} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                {subject.replace(/_/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return null
}
