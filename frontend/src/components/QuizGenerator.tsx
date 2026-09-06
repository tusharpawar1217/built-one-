import { useState } from 'react'
import { Brain, CheckCircle, XCircle, Loader2, Trophy, Clock } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { generateQuiz } from '../api/quiz'

interface QuizGeneratorProps {
  userId: string
  documentId: string
  documentName: string
}

interface QuizQuestion {
  question: string
  options: string[]
  correct_answer: string
  difficulty: string
  explanation: string
  source_page: number
}

export default function QuizGenerator({ userId, documentId, documentName }: QuizGeneratorProps) {
  const [numQuestions, setNumQuestions] = useState(5)
  const [difficulty, setDifficulty] = useState<string>('medium')
  const [topic, setTopic] = useState('')
  const [quiz, setQuiz] = useState<QuizQuestion[] | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedAnswers, setSelectedAnswers] = useState<string[]>([])
  const [showResults, setShowResults] = useState(false)
  const [score, setScore] = useState(0)

  const quizMutation = useMutation({
    mutationFn: () => generateQuiz(documentId, userId, numQuestions, difficulty, topic),
    onSuccess: (data) => {
      setQuiz(data.questions)
      setSelectedAnswers(new Array(data.questions.length).fill(''))
      setCurrentQuestion(0)
      setShowResults(false)
      setScore(0)
    },
  })

  const handleGenerateQuiz = () => {
    quizMutation.mutate()
  }

  const handleSelectAnswer = (answer: string) => {
    const newAnswers = [...selectedAnswers]
    newAnswers[currentQuestion] = answer
    setSelectedAnswers(newAnswers)
  }

  const handleNext = () => {
    if (currentQuestion < (quiz?.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1)
    }
  }

  const handlePrevious = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
    }
  }

  const handleSubmit = () => {
    if (!quiz) return
    
    let correctCount = 0
    quiz.forEach((q, idx) => {
      if (selectedAnswers[idx] === q.correct_answer) {
        correctCount++
      }
    })
    
    setScore(correctCount)
    setShowResults(true)
  }

  const resetQuiz = () => {
    setQuiz(null)
    setSelectedAnswers([])
    setCurrentQuestion(0)
    setShowResults(false)
    setScore(0)
  }

  if (!quiz) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3 mb-4">
          <Brain className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">Mock Test Generator</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800">
            Generate practice questions from <strong>{documentName}</strong>
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic (Optional)
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g., Indian History, Mathematics..."
              className="input-field"
            />
            <p className="text-xs text-gray-500 mt-1">
              Leave empty to generate from entire document
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Number of Questions: {numQuestions}
            </label>
            <input
              type="range"
              min="5"
              max="20"
              value={numQuestions}
              onChange={(e) => setNumQuestions(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>5</span>
              <span>20</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Difficulty Level
            </label>
            <div className="grid grid-cols-3 gap-3">
              {['easy', 'medium', 'hard'].map((level) => (
                <button
                  key={level}
                  onClick={() => setDifficulty(level)}
                  className={`py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    difficulty === level
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleGenerateQuiz}
            disabled={quizMutation.isPending}
            className="btn-primary w-full flex items-center justify-center space-x-2"
          >
            {quizMutation.isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Generating Questions...</span>
              </>
            ) : (
              <>
                <Brain className="w-5 h-5" />
                <span>Generate Mock Test</span>
              </>
            )}
          </button>

          {quizMutation.isError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">
                Failed to generate quiz. Please try again.
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (showResults) {
    const percentage = Math.round((score / quiz.length) * 100)
    
    return (
      <div className="space-y-6">
        <div className="text-center">
          <Trophy className={`w-16 h-16 mx-auto mb-4 ${
            percentage >= 70 ? 'text-green-500' : percentage >= 50 ? 'text-yellow-500' : 'text-red-500'
          }`} />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Quiz Complete!
          </h2>
          <p className="text-lg text-gray-600">
            You scored <strong className="text-primary-600">{score}/{quiz.length}</strong> ({percentage}%)
          </p>
        </div>

        <div className="bg-gray-50 rounded-lg p-6 space-y-4">
          {quiz.map((question, idx) => {
            const isCorrect = selectedAnswers[idx] === question.correct_answer
            
            return (
              <div key={idx} className={`p-4 rounded-lg border-2 ${
                isCorrect ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
              }`}>
                <div className="flex items-start space-x-3 mb-3">
                  {isCorrect ? (
                    <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-1" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-1" />
                  )}
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-2">
                      Q{idx + 1}. {question.question}
                    </p>
                    <p className="text-sm text-gray-700">
                      <strong>Your Answer:</strong> {selectedAnswers[idx] || 'Not answered'}
                    </p>
                    {!isCorrect && (
                      <p className="text-sm text-green-700 mt-1">
                        <strong>Correct Answer:</strong> {question.correct_answer}
                      </p>
                    )}
                    <p className="text-xs text-gray-600 mt-2 italic">
                      {question.explanation}
                    </p>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="flex space-x-3">
          <button
            onClick={resetQuiz}
            className="btn-primary flex-1"
          >
            Generate New Quiz
          </button>
          <button
            onClick={() => setShowResults(false)}
            className="btn-secondary flex-1"
          >
            Review Answers
          </button>
        </div>
      </div>
    )
  }

  const question = quiz[currentQuestion]
  const isAnswered = selectedAnswers[currentQuestion] !== ''
  const allAnswered = selectedAnswers.every(a => a !== '')

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-gray-600">
          <span>Question {currentQuestion + 1} of {quiz.length}</span>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4" />
            <span>~{quiz.length * 2} min</span>
          </div>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all"
            style={{ width: `${((currentQuestion + 1) / quiz.length) * 100}%` }}
          />
        </div>
      </div>

      {/* Question Card */}
      <div className="bg-white rounded-lg border-2 border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-medium px-3 py-1 bg-purple-100 text-purple-700 rounded-full">
            {question.difficulty.charAt(0).toUpperCase() + question.difficulty.slice(1)}
          </span>
          <span className="text-xs text-gray-500">
            Page {question.source_page || 'N/A'}
          </span>
        </div>

        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {question.question}
        </h3>

        <div className="space-y-3">
          {question.options.map((option, idx) => (
            <button
              key={idx}
              onClick={() => handleSelectAnswer(option)}
              className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                selectedAnswers[currentQuestion] === option
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <span className="font-medium">{option}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentQuestion === 0}
          className="btn-secondary"
        >
          Previous
        </button>

        <span className="text-sm text-gray-600">
          {selectedAnswers.filter(a => a !== '').length} / {quiz.length} answered
        </span>

        {currentQuestion === quiz.length - 1 ? (
          <button
            onClick={handleSubmit}
            disabled={!allAnswered}
            className="btn-primary"
          >
            Submit Quiz
          </button>
        ) : (
          <button
            onClick={handleNext}
            disabled={!isAnswered}
            className="btn-primary"
          >
            Next
          </button>
        )}
      </div>
    </div>
  )
}
