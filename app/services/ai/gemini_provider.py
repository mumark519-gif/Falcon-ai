from google import genai

from app.core.config import settings


client = genai.Client(
    api_key=settings.GOOGLE_API_KEY,
)

def ask_gemini(
    prompt: str,
):

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text