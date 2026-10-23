import os
from dotenv import load_dotenv
from google import genai

# 1. Load environment variables from .env
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "paste_your_actual_key_here" or api_key == "KULVORA_AI":
    raise RuntimeError(
        "GEMINI_API_KEY is missing or still set to a placeholder.\n"
        "Please open your '.env' file and replace 'paste_your_actual_key_here' with your real API key "
        "from Google AI Studio: https://aistudio.google.com/apikey"
    )

print(f"[*] Gemini API Key loaded and verified (length: {len(api_key)})")

# 2. Initialize the official Google GenAI Client
client = genai.Client(api_key=api_key)

# 3. Models to try (prioritizing active free-tier models without capacity throttling)
models_to_try = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
    "gemini-3-flash-preview",
    "gemini-3.7-flash"
]

prompt = "Write a Python function to check whether a number is prime. Explain the code briefly."

print("\n[*] Sending request to Google Gemini API...")
response_text = None
used_model = None

for model_name in models_to_try:
    print(f"    -> Trying model '{model_name}'...")
    try:
        # Use Google GenAI official Interactions API
        interaction = client.interactions.create(
            model=model_name,
            input=prompt,
        )
        response_text = getattr(interaction, "output_text", None) or str(interaction)
        used_model = model_name
        break
    except Exception as err:
        # If model is unavailable or overloaded, try standard generate_content fallback
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if res and res.text:
                response_text = res.text
                used_model = model_name
                break
        except Exception:
            pass
        print(f"       Notice: '{model_name}' skipped ({err.__class__.__name__}). Switching to next model...")

if response_text:
    print(f"\n=======================================================")
    print(f" [SUCCESS] AI Coding Response Received from: {used_model}")
    print(f"=======================================================\n")
    print(response_text)
else:
    raise RuntimeError("All candidate models failed. Please verify your Google AI Studio quota and network connection.")
