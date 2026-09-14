import os, sys
from google import genai
from google.genai import types

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
client = genai.Client(api_key=api_key)

prompt_parts = []
claude_md = os.path.join(os.path.dirname(__file__), "CLAUDE.md")
if os.path.exists(claude_md):
    with open(claude_md, "r", encoding="utf-8") as f:
        prompt_parts.append(f.read())

vault_dir = "C:/Users/gowth/das and co"
vindex = os.path.join(vault_dir, "VAULT-INDEX.md")
if os.path.exists(vindex):
    with open(vindex, "r", encoding="utf-8") as f:
        prompt_parts.append("\n\n---\nVAULT INDEX:\n" + f.read())

chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction="\n\n".join(prompt_parts),
        temperature=0.7,
    )
)

print("=" * 60)
print("  LEO — Personal Workflow Assistant (Powered by Gemini)")
print("  Type your message and press Enter. Type 'exit' to quit.")
print("=" * 60)
print("\nLEO: Hello Gowtham, what are we working on today?\n")

while True:
    try:
        user_input = input("Gowtham: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nLEO: Talk soon.")
        break
    if not user_input:
        continue
    if user_input.lower() in ("exit", "quit", "goodbye leo", "goodbye"):
        print("LEO: Talk soon.")
        break
    print("\nLEO: ", end="", flush=True)
    try:
        response_stream = chat.send_message_stream(user_input)
        for chunk in response_stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"\n[Error: {e}]\n")
