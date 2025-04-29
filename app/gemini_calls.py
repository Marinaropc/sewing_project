import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_sewing_instructions(pattern_type, measurements_summary):
    prompt = f"""
You are a sewing assistant helping users assemble sewing patterns.

The user uploaded a pattern for a **{pattern_type}**.
The user's body measurements are: {measurements_summary}.

Your task:
- Write beginner-friendly sewing instructions.
- Assume the user has basic sewing tools and a printed pattern.
- Include cutting instructions (mention adding seam allowances if needed).
- Include sewing instructions (how to assemble the parts).
- Use clear, short, numbered steps.
- Limit to 5 steps maximum.
- If important measurements are missing, still create simple instructions.
    """

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)

    return response.text.strip()