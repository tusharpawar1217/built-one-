"""Exam-specific templates with accurate patterns and section timings."""
from typing import Dict, List, Any
from app.models.test_schemas import ExamType, Subject, DifficultyLevel


class ExamTemplates:
    """Pre-configured templates for different government exams."""
    
    @staticmethod
    def get_upsc_prelims_gs1() -> Dict[str, Any]:
        """UPSC Civil Services Prelims - General Studies Paper I"""
        return {
            "name": "UPSC Prelims - GS Paper I",
            "exam_type": ExamType.UPSC,
            "description": "Civil Services Preliminary Examination - General Studies Paper I",
            "total_questions": 100,
            "total_marks": 200.0,  # 2 marks per question
            "duration_minutes": 120,
            "negative_marking": True,
            "negative_marks_ratio": 0.66,  # 2/3 = 0.66 for 2-mark questions
            "passing_percentage": 33.0,
            "sections": [
                {
                    "name": "Indian History & Culture",
                    "subjects": [Subject.INDIAN_HISTORY],
                    "questions": 15,
                    "marks_per_question": 2,
                },
                {
                    "name": "Indian Polity & Governance",
                    "subjects": [Subject.INDIAN_POLITY],
                    "questions": 20,
                    "marks_per_question": 2,
                },
                {
                    "name": "Geography",
                    "subjects": [Subject.GEOGRAPHY],
                    "questions": 15,
                    "marks_per_question": 2,
                },
                {
                    "name": "Economics & Social Development",
                    "subjects": [Subject.ECONOMICS],
                    "questions": 15,
                    "marks_per_question": 2,
                },
                {
                    "name": "Environment & Ecology",
                    "subjects": [Subject.ENVIRONMENT],
                    "questions": 15,
                    "marks_per_question": 2,
                },
                {
                    "name": "General Science",
                    "subjects": [Subject.SCIENCE_TECH],
                    "questions": 10,
                    "marks_per_question": 2,
                },
                {
                    "name": "Current Affairs",
                    "subjects": [Subject.CURRENT_AFFAIRS],
                    "questions": 10,
                    "marks_per_question": 2,
                },
            ],
            "difficulty_distribution": {
                "easy": 30,
                "medium": 50,
                "hard": 20,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 200 | Duration: 2 Hours",
                "Each question carries 2 marks",
                "Negative marking: -0.66 marks (1/3) for each wrong answer",
                "Questions will be of objective type (multiple choice)",
                "OMR sheet pattern - mark only one answer",
                "Qualifying marks: 33% (66 marks)",
            ]
        }
    
    @staticmethod
    def get_upsc_prelims_gs2() -> Dict[str, Any]:
        """UPSC Civil Services Prelims - General Studies Paper II (CSAT)"""
        return {
            "name": "UPSC Prelims - GS Paper II (CSAT)",
            "exam_type": ExamType.UPSC,
            "description": "Civil Services Preliminary Examination - CSAT",
            "total_questions": 80,
            "total_marks": 200.0,  # 2.5 marks per question
            "duration_minutes": 120,
            "negative_marking": True,
            "negative_marks_ratio": 0.83,  # 1/3 of 2.5
            "passing_percentage": 33.0,
            "sections": [
                {
                    "name": "Comprehension",
                    "subjects": [Subject.ENGLISH],
                    "questions": 30,
                    "marks_per_question": 2.5,
                },
                {
                    "name": "Logical Reasoning",
                    "subjects": [Subject.REASONING],
                    "questions": 25,
                    "marks_per_question": 2.5,
                },
                {
                    "name": "Analytical & Decision Making",
                    "subjects": [Subject.REASONING],
                    "questions": 15,
                    "marks_per_question": 2.5,
                },
                {
                    "name": "General Mental Ability",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 10,
                    "marks_per_question": 2.5,
                },
            ],
            "difficulty_distribution": {
                "easy": 25,
                "medium": 50,
                "hard": 25,
            },
            "instructions": [
                "Total Questions: 80 | Total Marks: 200 | Duration: 2 Hours",
                "Each question carries 2.5 marks",
                "Negative marking: -0.83 marks (1/3) for each wrong answer",
                "This is a qualifying paper (minimum 33% required)",
                "Marks in CSAT are NOT counted for final merit",
            ]
        }
    
    @staticmethod
    def get_mpsc_prelims() -> Dict[str, Any]:
        """MPSC State Services Prelims"""
        return {
            "name": "MPSC Prelims - General Studies",
            "exam_type": ExamType.MPSC,
            "description": "Maharashtra Public Service Commission Preliminary Examination",
            "total_questions": 100,
            "total_marks": 100.0,  # 1 mark per question
            "duration_minutes": 120,
            "negative_marking": True,
            "negative_marks_ratio": 0.25,
            "passing_percentage": 33.0,
            "sections": [
                {
                    "name": "Indian & Maharashtra History",
                    "subjects": [Subject.INDIAN_HISTORY],
                    "questions": 20,
                    "marks_per_question": 1,
                },
                {
                    "name": "Indian Polity & Maharashtra Government",
                    "subjects": [Subject.INDIAN_POLITY],
                    "questions": 20,
                    "marks_per_question": 1,
                },
                {
                    "name": "Geography & Economy",
                    "subjects": [Subject.GEOGRAPHY, Subject.ECONOMICS],
                    "questions": 20,
                    "marks_per_question": 1,
                },
                {
                    "name": "Science & Technology",
                    "subjects": [Subject.SCIENCE_TECH],
                    "questions": 15,
                    "marks_per_question": 1,
                },
                {
                    "name": "Current Events",
                    "subjects": [Subject.CURRENT_AFFAIRS],
                    "questions": 15,
                    "marks_per_question": 1,
                },
                {
                    "name": "General Knowledge",
                    "subjects": [Subject.GENERAL_KNOWLEDGE],
                    "questions": 10,
                    "marks_per_question": 1,
                },
            ],
            "difficulty_distribution": {
                "easy": 35,
                "medium": 45,
                "hard": 20,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 100 | Duration: 2 Hours",
                "Each question carries 1 mark",
                "Negative marking: -0.25 marks for each wrong answer",
                "Questions in Marathi and English both",
                "OMR based examination",
                "Qualifying marks: 33% (33 marks)",
            ]
        }
    
    @staticmethod
    def get_ssc_cgl_tier1() -> Dict[str, Any]:
        """SSC Combined Graduate Level Tier 1"""
        return {
            "name": "SSC CGL Tier I",
            "exam_type": ExamType.SSC,
            "description": "Staff Selection Commission - Combined Graduate Level Tier I",
            "total_questions": 100,
            "total_marks": 200.0,  # 2 marks per question
            "duration_minutes": 60,
            "negative_marking": True,
            "negative_marks_ratio": 0.50,  # 0.5 marks penalty
            "passing_percentage": 33.0,
            "sections": [
                {
                    "name": "General Intelligence & Reasoning",
                    "subjects": [Subject.REASONING],
                    "questions": 25,
                    "marks_per_question": 2,
                    "time_minutes": 15,
                },
                {
                    "name": "General Awareness",
                    "subjects": [Subject.GENERAL_KNOWLEDGE, Subject.CURRENT_AFFAIRS],
                    "questions": 25,
                    "marks_per_question": 2,
                    "time_minutes": 15,
                },
                {
                    "name": "Quantitative Aptitude",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 25,
                    "marks_per_question": 2,
                    "time_minutes": 15,
                },
                {
                    "name": "English Comprehension",
                    "subjects": [Subject.ENGLISH],
                    "questions": 25,
                    "marks_per_question": 2,
                    "time_minutes": 15,
                },
            ],
            "difficulty_distribution": {
                "easy": 30,
                "medium": 50,
                "hard": 20,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 200 | Duration: 60 Minutes",
                "4 Sections with 25 questions each",
                "Each question carries 2 marks",
                "Negative marking: -0.50 marks for each wrong answer",
                "Computer Based Examination (CBE)",
                "Section-wise time limit NOT applicable",
            ]
        }
    
    @staticmethod
    def get_ssc_chsl() -> Dict[str, Any]:
        """SSC Combined Higher Secondary Level"""
        return {
            "name": "SSC CHSL Tier I",
            "exam_type": ExamType.SSC,
            "description": "Staff Selection Commission - Combined Higher Secondary Level",
            "total_questions": 100,
            "total_marks": 200.0,
            "duration_minutes": 60,
            "negative_marking": True,
            "negative_marks_ratio": 0.50,
            "passing_percentage": 33.0,
            "sections": [
                {
                    "name": "English Language",
                    "subjects": [Subject.ENGLISH],
                    "questions": 25,
                    "marks_per_question": 2,
                },
                {
                    "name": "General Intelligence",
                    "subjects": [Subject.REASONING],
                    "questions": 25,
                    "marks_per_question": 2,
                },
                {
                    "name": "Quantitative Aptitude",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 25,
                    "marks_per_question": 2,
                },
                {
                    "name": "General Awareness",
                    "subjects": [Subject.GENERAL_KNOWLEDGE],
                    "questions": 25,
                    "marks_per_question": 2,
                },
            ],
            "difficulty_distribution": {
                "easy": 35,
                "medium": 45,
                "hard": 20,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 200 | Duration: 60 Minutes",
                "Each question carries 2 marks",
                "Negative marking: -0.50 marks for wrong answer",
                "Computer Based Test (Online)",
            ]
        }
    
    @staticmethod
    def get_ibps_po_prelims() -> Dict[str, Any]:
        """IBPS PO Prelims"""
        return {
            "name": "IBPS PO Prelims",
            "exam_type": ExamType.BANKING,
            "description": "Institute of Banking Personnel Selection - Probationary Officer Prelims",
            "total_questions": 100,
            "total_marks": 100.0,
            "duration_minutes": 60,
            "negative_marking": True,
            "negative_marks_ratio": 0.25,
            "passing_percentage": 0.0,  # Sectional cutoffs apply
            "sections": [
                {
                    "name": "English Language",
                    "subjects": [Subject.ENGLISH],
                    "questions": 30,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Quantitative Aptitude",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Reasoning Ability",
                    "subjects": [Subject.REASONING],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
            ],
            "difficulty_distribution": {
                "easy": 25,
                "medium": 50,
                "hard": 25,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 100 | Duration: 60 Minutes",
                "3 Sections with sectional timing",
                "Each question carries 1 mark",
                "Negative marking: -0.25 marks for wrong answer",
                "Sectional timing: 20 minutes per section",
                "Must clear sectional cutoffs + overall cutoff",
                "Online Computer Based Test",
            ]
        }
    
    @staticmethod
    def get_ibps_clerk_prelims() -> Dict[str, Any]:
        """IBPS Clerk Prelims"""
        return {
            "name": "IBPS Clerk Prelims",
            "exam_type": ExamType.BANKING,
            "description": "Institute of Banking Personnel Selection - Clerk Prelims",
            "total_questions": 100,
            "total_marks": 100.0,
            "duration_minutes": 60,
            "negative_marking": True,
            "negative_marks_ratio": 0.25,
            "passing_percentage": 0.0,
            "sections": [
                {
                    "name": "English Language",
                    "subjects": [Subject.ENGLISH],
                    "questions": 30,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Numerical Ability",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Reasoning Ability",
                    "subjects": [Subject.REASONING],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
            ],
            "difficulty_distribution": {
                "easy": 30,
                "medium": 50,
                "hard": 20,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 100 | Duration: 60 Minutes",
                "3 Sections with sectional timing of 20 minutes each",
                "Each question carries 1 mark",
                "Negative marking: -0.25 marks for wrong answer",
                "Must qualify in each section individually",
            ]
        }
    
    @staticmethod
    def get_sbi_po_prelims() -> Dict[str, Any]:
        """SBI PO Prelims"""
        return {
            "name": "SBI PO Prelims",
            "exam_type": ExamType.BANKING,
            "description": "State Bank of India - Probationary Officer Prelims",
            "total_questions": 100,
            "total_marks": 100.0,
            "duration_minutes": 60,
            "negative_marking": True,
            "negative_marks_ratio": 0.25,
            "passing_percentage": 0.0,
            "sections": [
                {
                    "name": "English Language",
                    "subjects": [Subject.ENGLISH],
                    "questions": 30,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Quantitative Aptitude",
                    "subjects": [Subject.QUANTITATIVE],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
                {
                    "name": "Reasoning Ability",
                    "subjects": [Subject.REASONING],
                    "questions": 35,
                    "marks_per_question": 1,
                    "time_minutes": 20,
                    "sectional": True,
                },
            ],
            "difficulty_distribution": {
                "easy": 20,
                "medium": 50,
                "hard": 30,
            },
            "instructions": [
                "Total Questions: 100 | Total Marks: 100 | Duration: 60 Minutes",
                "Sectional timing: 20 minutes per section",
                "Cannot switch between sections",
                "Each question carries 1 mark",
                "Negative marking: -0.25 marks for wrong answer",
                "Sectional as well as overall cutoff applies",
            ]
        }
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, Dict[str, Any]]:
        """Get all exam templates."""
        return {
            "upsc_prelims_gs1": cls.get_upsc_prelims_gs1(),
            "upsc_prelims_gs2": cls.get_upsc_prelims_gs2(),
            "mpsc_prelims": cls.get_mpsc_prelims(),
            "ssc_cgl_tier1": cls.get_ssc_cgl_tier1(),
            "ssc_chsl": cls.get_ssc_chsl(),
            "ibps_po_prelims": cls.get_ibps_po_prelims(),
            "ibps_clerk_prelims": cls.get_ibps_clerk_prelims(),
            "sbi_po_prelims": cls.get_sbi_po_prelims(),
        }
    
    @classmethod
    def get_templates_by_exam_type(cls, exam_type: ExamType) -> List[Dict[str, Any]]:
        """Get templates for specific exam type."""
        all_templates = cls.get_all_templates()
        return [
            template for template in all_templates.values()
            if template["exam_type"] == exam_type
        ]
    
    @classmethod
    def get_template(cls, template_id: str) -> Dict[str, Any]:
        """Get specific template by ID."""
        all_templates = cls.get_all_templates()
        return all_templates.get(template_id)
