import os
import traceback
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

try:
    key = os.getenv('GEMINI_API_KEY')
    print(f"Key starts with: {key[:5]}...")
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("Generating content...")
    response = model.generate_content('hi')
    print("Response:", response.text)
except Exception:
    traceback.print_exc()
