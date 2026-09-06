import { useState } from 'react'
import { BookOpen, Clock, Trophy, Target, Users, AlertCircle, Play, Zap } from 'lucide-react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getExamTemplates, createTestFromTemplate, ExamType } from '../api/tests'

interface ExamTestBrowserProps {
  userId: string
  onTestCreated: (testId: string) => void
}

export default function ExamTestBrowser({ userId, onTestCreated }: ExamTestBrowserProps) {
  const [selectedExam, setSelectedExam] = useState<ExamType>(ExamType.UPSC)
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null)

  // Fetch templates for selected exam
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['exam-templates', selectedExam],
    queryFn: () => getExamTemplates(selectedExam),
  })

  // Create test from template
  const createTestMutation = useMutation({
    mutationFn: (templateId: string) => createTestFromTemplate(templateId, userId),
    onSuccess: (test) => {
      onTestCreated(test.test_id)
    },
  })

  const examTypes = [
    { type: ExamType.UPSC, label: 'UPSC', icon: '🇮🇳', color: 'bg-red-100 text-red-700' },
    { type: ExamType.MPSC, label: 'MPSC', icon: '🏛️', color: 'bg-orange-100 text-orange-700' },
    { type: ExamType.SSC, label: 'SSC', icon: '📋', color: 'bg-blue-100 text-blue-700' },
    { type: ExamType.BANKING, label: 'Banking', icon: '🏦', color: 'bg-green-100 text-green-700' },
  ]

  const getExamColor = (examType: string) => {
    const exam = examTypes.find(e => e.type === examType)
    return exam?.color || 'bg-gray-100 text-gray-700'
  }

  const getExamIcon = (examType: string) => {
    const exam = examTypes.find(e => e.type === examType)
    return exam?.icon || '📝'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Government Exam Test Series</h2>
        <p className="text-gray-600">
          Practice with real exam patterns • Sectional timing • Accurate negative marking
        </p>
      </div>

      {/* Exam Type Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {examTypes.map((exam) => (
          <button
            key={exam.type}
            onClick={() => {
              setSelectedExam(exam.type)
              setSelectedTemplate(null)
            }}
            className={`p-4 rounded-xl border-2 transition-all ${
              selectedExam === exam.type
                ? 'border-primary-500 bg-primary-50 shadow-md'
                : 'border-gray-200 hover:border-gray-300 bg-white'
            }`}
          >
            <div className="text-3xl mb-2">{exam.icon}</div>
            <div className="font-semibold text-gray-900">{exam.label}</div>
            <div className="text-xs text-gray-500 mt-1">
              {templatesData?.templates.filter((t: any) => t.exam_type === exam.type).length || 0} tests
            </div>
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="w-12 h-12 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading test templates...</p>
        </div>
      )}

      {/* Template Cards */}
      {!isLoading && templatesData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {templatesData.templates.map((template: any, idx: number) => (
            <div
              key={idx}
              className="card hover:shadow-xl transition-all cursor-pointer border-2 border-transparent hover:border-primary-200"
              onClick={() => setSelectedTemplate(template)}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getExamColor(template.exam_type)}`}>
                      {getExamIcon(template.exam_type)} {template.exam_type.toUpperCase()}
                    </span>
                    {template.sections && (
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs">
                        {template.sections.length} Sections
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">{template.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{template.description}</p>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 mb-4 p-3 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <BookOpen className="w-4 h-4 text-primary-600 mx-auto mb-1" />
                  <p className="text-sm font-bold text-gray-900">{template.total_questions}</p>
                  <p className="text-xs text-gray-600">Questions</p>
                </div>
                <div className="text-center">
                  <Clock className="w-4 h-4 text-primary-600 mx-auto mb-1" />
                  <p className="text-sm font-bold text-gray-900">{template.duration_minutes}</p>
                  <p className="text-xs text-gray-600">Minutes</p>
                </div>
                <div className="text-center">
                  <Trophy className="w-4 h-4 text-primary-600 mx-auto mb-1" />
                  <p className="text-sm font-bold text-gray-900">{template.total_marks}</p>
                  <p className="text-xs text-gray-600">Marks</p>
                </div>
                <div className="text-center">
                  <AlertCircle className="w-4 h-4 text-red-600 mx-auto mb-1" />
                  <p className="text-sm font-bold text-gray-900">-{template.negative_marks_ratio}</p>
                  <p className="text-xs text-gray-600">Negative</p>
                </div>
              </div>

              {/* Sections */}
              {template.sections && template.sections.length > 0 && (
                <div className="space-y-2 mb-4">
                  <p className="text-xs font-medium text-gray-700 uppercase tracking-wide">Sections:</p>
                  <div className="space-y-1">
                    {template.sections.slice(0, 3).map((section: any, sIdx: number) => (
                      <div key={sIdx} className="flex items-center justify-between text-sm">
                        <span className="text-gray-700">{section.name}</span>
                        <div className="flex items-center space-x-3 text-xs text-gray-600">
                          <span>{section.questions}Q</span>
                          {section.time_minutes && (
                            <span className="flex items-center">
                              <Clock className="w-3 h-3 mr-1" />
                              {section.time_minutes}m
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                    {template.sections.length > 3 && (
                      <p className="text-xs text-gray-500">+ {template.sections.length - 3} more sections</p>
                    )}
                  </div>
                </div>
              )}

              {/* Difficulty Distribution */}
              {template.difficulty_distribution && (
                <div className="mb-4">
                  <p className="text-xs font-medium text-gray-700 uppercase tracking-wide mb-2">Difficulty:</p>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2 overflow-hidden flex">
                      <div
                        className="bg-green-500"
                        style={{ width: `${template.difficulty_distribution.easy}%` }}
                      />
                      <div
                        className="bg-yellow-500"
                        style={{ width: `${template.difficulty_distribution.medium}%` }}
                      />
                      <div
                        className="bg-red-500"
                        style={{ width: `${template.difficulty_distribution.hard}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-600 mt-1">
                    <span>Easy {template.difficulty_distribution.easy}%</span>
                    <span>Medium {template.difficulty_distribution.medium}%</span>
                    <span>Hard {template.difficulty_distribution.hard}%</span>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center space-x-2 pt-3 border-t border-gray-200">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedTemplate(template)
                  }}
                  className="btn-secondary flex-1 text-sm"
                >
                  <Target className="w-4 h-4 mr-1" />
                  View Details
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    createTestMutation.mutate(template.template_id)
                  }}
                  disabled={createTestMutation.isPending}
                  className="btn-primary flex-1 text-sm"
                >
                  {createTestMutation.isPending ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />
                      Creating...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-1" />
                      Start Test
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && templatesData && templatesData.templates.length === 0 && (
        <div className="text-center py-12">
          <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-600">No test templates available for {selectedExam.toUpperCase()}</p>
        </div>
      )}

      {/* Template Detail Modal */}
      {selectedTemplate && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedTemplate(null)}
        >
          <div
            className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-center space-x-2 mb-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getExamColor(selectedTemplate.exam_type)}`}>
                  {getExamIcon(selectedTemplate.exam_type)} {selectedTemplate.exam_type.toUpperCase()}
                </span>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedTemplate.name}</h2>
              <p className="text-gray-600">{selectedTemplate.description}</p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-4 gap-4 mb-6 p-4 bg-gradient-to-r from-primary-50 to-purple-50 rounded-xl">
              <div className="text-center">
                <BookOpen className="w-6 h-6 text-primary-600 mx-auto mb-2" />
                <p className="text-lg font-bold text-gray-900">{selectedTemplate.total_questions}</p>
                <p className="text-xs text-gray-600">Questions</p>
              </div>
              <div className="text-center">
                <Clock className="w-6 h-6 text-primary-600 mx-auto mb-2" />
                <p className="text-lg font-bold text-gray-900">{selectedTemplate.duration_minutes}</p>
                <p className="text-xs text-gray-600">Minutes</p>
              </div>
              <div className="text-center">
                <Trophy className="w-6 h-6 text-primary-600 mx-auto mb-2" />
                <p className="text-lg font-bold text-gray-900">{selectedTemplate.total_marks}</p>
                <p className="text-xs text-gray-600">Total Marks</p>
              </div>
              <div className="text-center">
                <AlertCircle className="w-6 h-6 text-red-600 mx-auto mb-2" />
                <p className="text-lg font-bold text-gray-900">-{selectedTemplate.negative_marks_ratio}</p>
                <p className="text-xs text-gray-600">Negative</p>
              </div>
            </div>

            {/* Sections */}
            {selectedTemplate.sections && (
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">Test Sections:</h3>
                <div className="space-y-3">
                  {selectedTemplate.sections.map((section: any, idx: number) => (
                    <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">{section.name}</h4>
                        <div className="flex items-center space-x-4 text-sm text-gray-600">
                          <span className="flex items-center">
                            <BookOpen className="w-4 h-4 mr-1" />
                            {section.questions} Questions
                          </span>
                          {section.time_minutes && (
                            <span className="flex items-center">
                              <Clock className="w-4 h-4 mr-1" />
                              {section.time_minutes} Minutes
                            </span>
                          )}
                          {section.sectional && (
                            <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs">
                              Sectional Timing
                            </span>
                          )}
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">
                        {section.marks_per_question} mark{section.marks_per_question > 1 ? 's' : ''} per question
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Instructions */}
            {selectedTemplate.instructions && (
              <div className="mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">Instructions:</h3>
                <ul className="space-y-2">
                  {selectedTemplate.instructions.map((instruction: string, idx: number) => (
                    <li key={idx} className="flex items-start space-x-2 text-sm text-gray-700">
                      <Zap className="w-4 h-4 text-primary-600 flex-shrink-0 mt-0.5" />
                      <span>{instruction}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setSelectedTemplate(null)}
                className="btn-secondary flex-1"
              >
                Close
              </button>
              <button
                onClick={() => {
                  createTestMutation.mutate(selectedTemplate.template_id)
                  setSelectedTemplate(null)
                }}
                disabled={createTestMutation.isPending}
                className="btn-primary flex-1"
              >
                {createTestMutation.isPending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Creating Test...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5 mr-2" />
                    Start This Test
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
