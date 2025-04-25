import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_pattern_parameters(pattern_type, svg_summary, user_measurements):
    prompt = f"""
    You are a pattern-resizing assistant.
    
    Here is a simplified summary of the uploaded {pattern_type} SVG pattern:
    {svg_summary}
    
    The user’s measurements are:
    {user_measurements}
    
    First estimate the pattern’s original size (e.g. bust, waist, or hips).
    Then compute how much to scale the X and Y axes so the pattern matches the user’s measurements.
    Respond *exactly* in this format (no extra text):
    
    estimated_bust = <number>
    estimated_waist = <number>
    estimated_hips = <number>
    scale_x = <number>
    scale_y = <number>
    """

    client = openai.OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.3
    )

    return response.choices[0].message.content