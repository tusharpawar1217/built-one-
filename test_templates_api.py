"""Quick test script to verify templates API works."""
import sys
sys.path.insert(0, 'services/rag-service')

from app.services.exam_templates import ExamTemplates

# Test getting all templates
print("=== Testing Exam Templates ===\n")

all_templates = ExamTemplates.get_all_templates()

print(f"Total Templates: {len(all_templates)}\n")

for template_id, template in all_templates.items():
    print(f"ID: {template_id}")
    print(f"Name: {template['name']}")
    print(f"Exam: {template['exam_type']}")
    print(f"Questions: {template['total_questions']}")
    print(f"Duration: {template['duration_minutes']} min")
    print(f"Sections: {len(template['sections'])}")
    print("-" * 50)

print("\n✅ All templates loaded successfully!")
print("\nTo see in API:")
print("1. Start backend: uvicorn app.main:app --reload --port 8000")
print("2. Visit: http://localhost:8000/api/v1/tests/templates")
print("3. Or in frontend: Click 'Test Series' tab")
