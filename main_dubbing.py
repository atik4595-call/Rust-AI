
import os
import time
from google import genai
from google.genai.errors import APIError

class ProfessionalMovieDubbingAI:
    def __init__(self):
        # সরাসরি কি হার্ডকোড না করে এনভায়রনমেন্ট ভেরিয়েবল থেকে নেওয়া হচ্ছে
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-3.8-flash"

    def generate_emotional_bengali_script(self, original_dialogue: str, emotion: str) -> str:
        prompt = f"""
        You are a professional cinematic dialogue writer and dubbing director.
        Translate and adapt the following English movie dialogue into natural, lip-sync friendly Bengali.
        Ensure the tone perfectly matches the emotion: [{emotion}].
        Include precise emotional cues and pauses for voice synthesis (e.g., [sigh], [angry tone], [soft whisper]).

        Original Dialogue: "{original_dialogue}"

        Provide only the polished Bengali dubbing script.
        """
        max_retries = 5
        backoff_delay = 2
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                return response.text
            except APIError as e:
                if e.code in [503, 429] and attempt < max_retries - 1:
                    print(f"⚠️ API Server busy (status {e.code}). Retrying...")
                    time.sleep(backoff_delay)
                    backoff_delay *= 2
                else:
                    raise e
