import axios from 'axios'

const API_BASE = '/api/v1'

export interface EligibilityInfo {
  exam_name: string
  organization: string
  eligibility_criteria: {
    age_limit: string
    educational_qualification: string
    nationality: string
    additional_criteria: string[]
  }
  important_dates: {
    notification_date: string
    application_start: string
    application_end: string
    exam_date: string
    result_date: string
  }
  application_fee: {
    general: string
    obc: string
    sc_st: string
    pwd: string
  }
  official_link: string
  post_details: Array<{
    post_name: string
    vacancies: string
    pay_scale: string
  }>
}

export async function extractEligibility(
  documentId: string,
  userId: string
): Promise<EligibilityInfo> {
  const response = await axios.post(`${API_BASE}/eligibility/extract`, null, {
    params: {
      document_id: documentId,
      user_id: userId,
    },
  })

  return response.data
}

export async function checkEligibility(
  documentId: string,
  userId: string,
  userAge?: number,
  userQualification?: string,
  userCategory?: string
): Promise<any> {
  const response = await axios.post(`${API_BASE}/eligibility/check`, null, {
    params: {
      document_id: documentId,
      user_id: userId,
      user_age: userAge,
      user_qualification: userQualification,
      user_category: userCategory,
    },
  })

  return response.data
}
