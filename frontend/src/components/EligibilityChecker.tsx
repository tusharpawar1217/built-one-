import { useState } from 'react'
import { Shield, CheckCircle, AlertCircle, Loader2, Calendar, DollarSign, Users } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { extractEligibility } from '../api/eligibility'

interface EligibilityCheckerProps {
  userId: string
  documentId: string
  documentName: string
}

export default function EligibilityChecker({ userId, documentId, documentName }: EligibilityCheckerProps) {
  const [eligibilityData, setEligibilityData] = useState<any>(null)

  const extractMutation = useMutation({
    mutationFn: () => extractEligibility(documentId, userId),
    onSuccess: (data) => {
      setEligibilityData(data)
    },
  })

  const handleExtract = () => {
    extractMutation.mutate()
  }

  if (!eligibilityData) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3 mb-4">
          <Shield className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">Eligibility Checker</h2>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800">
            Extract eligibility criteria from <strong>{documentName}</strong>
          </p>
          <p className="text-xs text-blue-600 mt-1">
            This will analyze age limits, qualifications, important dates, and application fees
          </p>
        </div>

        <button
          onClick={handleExtract}
          disabled={extractMutation.isPending}
          className="btn-primary w-full flex items-center justify-center space-x-2"
        >
          {extractMutation.isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Extracting Information...</span>
            </>
          ) : (
            <>
              <Shield className="w-5 h-5" />
              <span>Extract Eligibility Criteria</span>
            </>
          )}
        </button>

        {extractMutation.isError && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              Failed to extract eligibility. This might not be a notification document.
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <Shield className="w-6 h-6 text-primary-600" />
          <h2 className="text-xl font-semibold text-gray-900">Eligibility Information</h2>
        </div>
        <button
          onClick={() => setEligibilityData(null)}
          className="text-sm text-primary-600 hover:text-primary-700"
        >
          Extract Another
        </button>
      </div>

      {/* Exam Details */}
      <div className="card bg-gradient-to-r from-primary-50 to-purple-50 border-primary-200">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">
          {eligibilityData.exam_name}
        </h3>
        <p className="text-gray-700">{eligibilityData.organization}</p>
        {eligibilityData.official_link && (
          <a
            href={eligibilityData.official_link}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary-600 hover:underline mt-2 inline-block"
          >
            Official Notification →
          </a>
        )}
      </div>

      {/* Eligibility Criteria */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Eligibility Criteria</h3>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-sm font-medium text-gray-700">Age Limit</p>
            <p className="text-sm text-gray-900 mt-1">
              {eligibilityData.eligibility_criteria.age_limit || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700">Educational Qualification</p>
            <p className="text-sm text-gray-900 mt-1">
              {eligibilityData.eligibility_criteria.educational_qualification || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-700">Nationality</p>
            <p className="text-sm text-gray-900 mt-1">
              {eligibilityData.eligibility_criteria.nationality || 'Not specified'}
            </p>
          </div>
          {eligibilityData.eligibility_criteria.additional_criteria?.length > 0 && (
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Additional Criteria</p>
              <ul className="list-disc list-inside text-sm text-gray-900 space-y-1">
                {eligibilityData.eligibility_criteria.additional_criteria.map((criteria: string, idx: number) => (
                  <li key={idx}>{criteria}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Important Dates */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Calendar className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Important Dates</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(eligibilityData.important_dates).map(([key, value]) => (
            value && (
              <div key={key}>
                <p className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-sm text-gray-900 mt-1">{value as string}</p>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Application Fee */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <DollarSign className="w-5 h-5 text-green-600" />
          <h3 className="text-lg font-semibold text-gray-900">Application Fee</h3>
        </div>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(eligibilityData.application_fee).map(([category, fee]) => (
            fee && (
              <div key={category} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700 capitalize">
                  {category === 'sc_st' ? 'SC/ST' : category.toUpperCase()}
                </span>
                <span className="text-sm font-bold text-gray-900">{fee as string}</span>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Post Details */}
      {eligibilityData.post_details?.length > 0 && (
        <div className="card">
          <div className="flex items-center space-x-2 mb-4">
            <Users className="w-5 h-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">Post Details</h3>
          </div>
          <div className="space-y-3">
            {eligibilityData.post_details.map((post: any, idx: number) => (
              <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900">{post.post_name}</h4>
                <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                  <span>
                    <strong>Vacancies:</strong> {post.vacancies}
                  </span>
                  {post.pay_scale && (
                    <span>
                      <strong>Pay Scale:</strong> {post.pay_scale}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
