"""
chat_finpilot.py
----------------
Terminal-based interactive CLI chat interface for FinPilot AI.
Allows conversational queries about your transaction data.
"""

import os
import requests
import pandas as pd
from src import excel_engine

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"

def is_ollama_available() -> bool:
    """Check if the local Ollama instance is running in the background."""
    try:
        response = requests.get("http://localhost:11434/", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_formatted_transaction_context() -> str:
    """Fetches real transaction data and formats it for Ollama's context window."""
    try:
        raw_data = excel_engine.read_transactions()
        if not raw_data:
            return "No transaction history recorded yet."
        
        # Load into DataFrame for a super clean text-based table
        columns = ['Date', 'Type', 'Category', 'Merchant', 'Amount', 'Description', 'Confidence', 'Month', 'Year']
        df = pd.DataFrame(raw_data, columns=columns)
        
        # Drop irrelevant technical column 'Confidence' to save space
        df = df.drop(columns=['Confidence', 'Year'])
        
        # Return a text-friendly table representation
        return df.to_string(index=False)
    except Exception as e:
        return f"Error loading history: {str(e)}"

def chat_loop():
    """Main CLI execution loop."""
    print("=" * 60)
    print("         FinPilot AI — Interactive Command Line Chat")
    print("=" * 60)
    
    # 1. Verify Ollama is ready
    if not is_ollama_available():
        print("❌ Error: Ollama background service is offline!")
        print("Please run 'ollama run llama3.2' in another terminal first.")
        print("=" * 60)
        return

    print("⚡ Connecting to database...")
    data_context = get_formatted_transaction_context()
    print("🤖 Local Brain (llama3.2) Active!")
    print("💡 Ask questions like:")
    print("   - 'How much did I spend in July?'")
    print("   - 'What is my biggest expense category?'")
    print("   - 'Can I afford a ₹20,000 purchase?'")
    print("   (Type 'exit' or 'quit' to close the assistant)")
    print("=" * 60)

    # 2. Start Conversation Loop
    while True:
        try:
            user_input = input("\nYou > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye! Happy budgeting! 👋")
                break
            
            print("Thinking... 🤔", end="\r")

            # Craft system prompt forcing concise, accurate financial answers
            prompt = f"""You are FinPilot AI, a professional conversational personal finance manager. 
Below is the user's real transaction history:
---
{data_context}
---

Rules:
1. Base your answer strictly on the provided transaction data context above.
2. Be direct, conversational, and keep answers to 2-3 sentences.
3. Use Indian Rupee formatting (₹) for money values.

User Question: {user_input}
FinPilot AI Response:"""

            payload = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            
            # Clear "Thinking..." line and print response
            print(" " * 20, end="\r") 
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                print(f"FinPilot > {answer}")
            else:
                print(f"❌ Error talking to Ollama (Status: {response.status_code})")
                
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Connection error: {str(e)}")

if __name__ == "__main__":
    chat_loop()