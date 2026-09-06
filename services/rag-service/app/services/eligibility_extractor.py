"""Eligibility extraction from exam notifications using structured output."""
import logging
import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.schemas import EligibilityInfo

logger = logging.getLogger(__name__)
settings = get_settings()


class EligibilityCriteria(BaseModel):
    """Structured eligibility criteria."""
    age_limit: str = Field(description="Age limit for the exam")
    educational_qualification: str = Field(description="Required educational qualification")
    nationality: str = Field(description="Nationality requirement")
    additional_criteria: List[str] = Field(default=[], description="Other eligibility criteria")


class ImportantDates(BaseModel):
    """Important dates for exam."""
    notification_date: str = Field(default="", description="Notification release date")
    application_start: str = Field(default="", description="Application start date")
    application_end: str = Field(default="", description="Application end date")
    exam_date: str = Field(default="", description="Exam date")
    result_date: str = Field(default="", description="Expected result date")


class ApplicationFee(BaseModel):
    """Application fee details."""
    general_category: str = Field(description="Fee for general category")
    obc_category: str = Field(default="", description="Fee for OBC category")
    sc_st_category: str = Field(default="", description="Fee for SC/ST category")
    pwd_category: str = Field(default="", description="Fee for PWD category")


class PostDetail(BaseModel):
    """Individual post details."""
    post_name: str = Field(description="Name of the post")
    vacancies: str = Field(description="Number of vacancies")
    pay_scale: str = Field(default="", description="Pay scale or salary")


class ExtractedNotification(BaseModel):
    """Complete extracted notification."""
    exam_name: str = Field(description="Full name of the exam")
    organization: str = Field(description="Organizing body")
    eligibility: EligibilityCriteria
    dates: ImportantDates
    fee: ApplicationFee
    posts: List[PostDetail]
    official_link: str = Field(default="", description="Official notification URL")


class EligibilityExtractor:
    """
    Extract structured eligibility information from exam notification PDFs.
    Uses Gemini with JSON schema for reliable extraction.
    """
    
    def __init__(self):
        """Initialize extractor."""
        self.settings = settings
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model_pro,  # Use Pro for better extraction
            google_api_key=settings.google_api_key,
            temperature=0.0  # Deterministic for extraction
        )
        self.parser = PydanticOutputParser(pydantic_object=ExtractedNotification)
    
    async def extract_from_text(self, notification_text: str) -> EligibilityInfo:
        """
        Extract eligibility information from notification text.
        
        Args:
            notification_text: Full text of notification document
        
        Returns:
            Structured eligibility information
        """
        system_prompt = """You are an expert at extracting structured information from Indian government exam notifications.

Your task:
1. Read the exam notification carefully
2. Extract eligibility criteria, important dates, fee structure, and post details
3. Return information in the specified JSON format
4. If information is not found, use empty string or empty list
5. Be precise with dates and numbers

Common patterns:
- Age limits: "18-40 years" or "21-27 years as on 01-01-2024"
- Qualifications: "Graduate in any discipline" or "10th pass"
- Dates: DD-MM-YYYY or DD/MM/YYYY format
- Fees: "₹500/-" or "Rs. 500"
"""

        format_instructions = self.parser.get_format_instructions()
        
        user_prompt = f"""Extract information from this exam notification:

{notification_text[:8000]}  # Limit to 8000 chars to avoid token limits

{format_instructions}

Return only valid JSON matching the schema."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Parse response
            extracted = self.parser.parse(response.content)
            
            # Convert to EligibilityInfo schema
            eligibility_info = EligibilityInfo(
                exam_name=extracted.exam_name,
                organization=extracted.organization,
                eligibility_criteria={
                    "age_limit": extracted.eligibility.age_limit,
                    "educational_qualification": extracted.eligibility.educational_qualification,
                    "nationality": extracted.eligibility.nationality,
                    "additional_criteria": extracted.eligibility.additional_criteria
                },
                important_dates={
                    "notification_date": extracted.dates.notification_date,
                    "application_start": extracted.dates.application_start,
                    "application_end": extracted.dates.application_end,
                    "exam_date": extracted.dates.exam_date,
                    "result_date": extracted.dates.result_date
                },
                application_fee={
                    "general": extracted.fee.general_category,
                    "obc": extracted.fee.obc_category,
                    "sc_st": extracted.fee.sc_st_category,
                    "pwd": extracted.fee.pwd_category
                },
                official_link=extracted.official_link,
                post_details=[
                    {
                        "post_name": post.post_name,
                        "vacancies": post.vacancies,
                        "pay_scale": post.pay_scale
                    }
                    for post in extracted.posts
                ]
            )
            
            logger.info(f"Successfully extracted notification: {extracted.exam_name}")
            return eligibility_info
        
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def check_eligibility(
        self,
        eligibility_info: EligibilityInfo,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if user meets eligibility criteria.
        
        Args:
            eligibility_info: Extracted eligibility information
            user_profile: User's details (age, qualification, category, etc.)
        
        Returns:
            Eligibility check result with reasoning
        """
        # TODO: Implement rule-based eligibility checking
        # For MVP, return placeholder
        
        return {
            "eligible": True,
            "exam_name": eligibility_info.exam_name,
            "checks": {
                "age": "Pending user age verification",
                "qualification": "Pending qualification verification",
                "category": "All categories eligible"
            },
            "recommendation": "Please verify your age and qualification details match the requirements"
        }
