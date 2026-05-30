"""
Run this script to test your Gemini API key directly.

Usage (Windows PowerShell):
    $env:GEMINI_API_KEY="your_key_here"
    py test_api.py
"""

import os
import sys

print("=" * 50)
print("Smart Agriculture AI — API Key Test")
print("=" * 50)

key = os.environ.get("GEMINI_API_KEY")
if not key:
    print("\nERROR: GEMINI_API_KEY is not set.")
    print("Run:  $env:GEMINI_API_KEY=\"your_key_here\"")
    sys.exit(1)

print(f"\nKey found: {key[:8]}...{key[-4:]} (length: {len(key)})")

try:
    import google.genai as genai
    import google.genai.types as gtypes
    print("SDK imported OK")
except ImportError:
    print("\nERROR: google-genai not installed.")
    print("Run:  pip install google-genai")
    sys.exit(1)

try:
    client = genai.Client(api_key=key)
    print("Client created OK")
except Exception as e:
    print(f"\nERROR creating client: {e}")
    sys.exit(1)

print("\nFetching available models...")
try:
    models = list(client.models.list())
    flash_models = [m.name for m in models if "flash" in m.name.lower()]
    print(f"Flash models available: {flash_models}")
except Exception as e:
    print(f"ERROR listing models: {e}")
    sys.exit(1)

print("\nSending test request to gemini-2.5-flash...")
try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly the word: OK",
        config=gtypes.GenerateContentConfig(max_output_tokens=50),
    )

    # Extract text skipping thought parts
    text = ""
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "thought") and part.thought:
                continue
            if isinstance(part.text, str):
                text += part.text

    print(f"Response: {text.strip()!r}")

    if text.strip():
        print("\nSUCCESS: API key is working. You can now run the app.")
    else:
        print("\nWARNING: Got empty response. Try again.")

except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
