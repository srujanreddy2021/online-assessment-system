# backend/assessment/views.py
import logging
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

class GenerateAssessmentView(APIView):
    def post(self, request):
        topic = request.data.get('topic')
        assessment_type = request.data.get('assessmentType')
        question_count = request.data.get('questionCount')

        if not all([topic, assessment_type, question_count]):
            logger.error("Missing required fields in the request data")
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Create the prompt template
        prompt = f"Generate {question_count} {assessment_type} questions about {topic}. For each question, provide the correct answer and, if it's a multiple-choice question, provide 3 incorrect options."

        # Prepare the payload for the API request
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            # Call the Google Generative Language API
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GOOGLE_GENERATIVE_AI_MODEL}:generateContent"
            headers = {"Content-Type": "application/json"}
            response = requests.post(api_url, json=payload, headers=headers, params={"key": settings.GOOGLE_GENERATIVE_AI_API_KEY})

            if response.status_code == 200:
                result = response.json()
                print(f"API response result: {result}")  # Add this line to inspect the structure
                
                generated_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Parse the result
                questions = parse_generated_text(generated_text)
                
                print(f"generated_text: {generated_text}")
                print(f"questions: {questions}")

                return Response({"questions": questions}, status=status.HTTP_200_OK)
            else:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return Response({"error": f"API request failed: {response.text}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def parse_generated_text(generated_text):
    questions = []
    lines = generated_text.split('\n')
    
    current_question = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('**'):
            if current_question:
                questions.append(current_question)
            # New question
            current_question = {"text": line, "options": [], "correct_answer": ""}
        elif line.startswith('a)') or line.startswith('b)') or line.startswith('c)') or line.startswith('d)'):
            # Option
            current_question["options"].append(line)
        elif line.startswith('**Correct Answer:**'):
            # Correct answer
            current_question["correct_answer"] = line.split(':')[1].strip()
    
    if current_question:
        questions.append(current_question)
    
    return questions
