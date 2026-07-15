"""
ai_engine.py
------------

FinPilot AI

Local AI transaction-extraction engine. Sends natural language
transaction descriptions to a locally running Ollama instance
(llama3.2 model) and returns a structured transaction dictionary
compatible with excel_engine.normalize_transaction().

Fully local. No cloud calls, no databases, no new files.
"""

from __future__ import annotations

import json
import re
from typing import Any

import requests

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2"
REQUEST_TIMEOUT = 30  # seconds

VALID_TYPES = {"Income", "Expense", "Savings", "Debt"}

# The exact shape the GUI / excel_engine expect back.
EMPTY_TRANSACTION: dict[str, Any] = {
    "type": "Expense",
    "category": "Other Expenses",
    "amount": 0,
    "merchant": "Unspecified",
    "date": "",
    "month": "",
    "year": 0,
    "description": "",
}

SYSTEM_PROMPT = """You are a financial transaction extraction engine.
Read the user's message describing a money transaction and respond
with ONLY a single JSON object, no explanations, no markdown, no
code fences. The JSON object must have exactly these keys:

{
  "type": "Income" | "Expense" | "Savings" | "Debt",
  "category": string,
  "amount": number,
  "merchant": string,
  "date": string,
  "month": string,
  "year": number,
  "description": string
}

Rules:
- "type" must be exactly one of: Income, Expense, Savings, Debt.
- "amount" must be a positive number with no currency symbol.
- If the message mentions "today", "yesterday", or no date, leave
  "date" as an empty string.
- If no month is mentioned, leave "month" as an empty string.
- If no year is mentioned, leave "year" as 0.
- "category" should be a short, sensible spending category
  (e.g. "Dining Out", "Bus", "Uber/Rapido", "Food Order",
  "Food Outside", "Other Expenses") based on the message.
- "merchant" should be the store/service/person name mentioned,
  or "Unspecified" if none is mentioned.
- "description" should be a short optional note, or empty string.
- Respond with the JSON object and nothing else.
"""


# ----------------------------------------------------
# OLLAMA AVAILABILITY
# ----------------------------------------------------

def is_ollama_available() -> bool:
    """Checks whether the local Ollama server is reachable."""

    try:
        response = requests.get("http://localhost:11434", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# ----------------------------------------------------
# OLLAMA CALL
# ----------------------------------------------------

def _call_ollama(prompt: str) -> str | None:
    """
    Sends a prompt to the local Ollama API and returns the raw text
    response. Returns None if Ollama is unavailable or the request
    fails for any reason.
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nUser message: \"{prompt}\"",
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None

    try:
        data = response.json()
    except (ValueError, json.JSONDecodeError):
        return None

    return data.get("response")


# ----------------------------------------------------
# JSON EXTRACTION
# ----------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Removes ```json / ``` markdown code fences if present."""

    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """
    Extracts the first valid JSON object found in a block of text.
    Handles markdown fences, leading/trailing commentary, and minor
    formatting noise. Returns None if no valid JSON object can be
    parsed.
    """

    if not text:
        return None

    cleaned = _strip_code_fences(text)

    # Fast path: the whole cleaned string is valid JSON.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, json.JSONDecodeError):
        pass

    # Fallback: find the first {...} span and try to parse that.
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return None

    candidate = match.group(0)

    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return parsed
    except (ValueError, json.JSONDecodeError):
        return None

    return None


# ----------------------------------------------------
# VALIDATION / NORMALIZATION OF AI OUTPUT
# ----------------------------------------------------

def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text.lower() not in ("none", "null", "unknown") else default


def _safe_amount(value: Any) -> float:
    try:
        amount = float(value)
        return amount if amount >= 0 else 0.0
    except (TypeError, ValueError):
        return 0.0


def _safe_year(value: Any) -> int:
    try:
        year = int(value)
        return year if year > 0 else 0
    except (TypeError, ValueError):
        return 0


def _validate_transaction(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Validates and normalizes a raw dict (as parsed from the AI's
    JSON response) into the guaranteed transaction shape. Missing or
    malformed fields fall back to safe defaults - this never raises.
    """

    txn_type = _safe_str(raw.get("type"), "Expense")
    if txn_type not in VALID_TYPES:
        txn_type = "Expense"

    return {
        "type": txn_type,
        "category": _safe_str(raw.get("category"), "Other Expenses"),
        "amount": _safe_amount(raw.get("amount")),
        "merchant": _safe_str(raw.get("merchant"), "Unspecified"),
        "date": _safe_str(raw.get("date"), ""),
        "month": _safe_str(raw.get("month"), ""),
        "year": _safe_year(raw.get("year")),
        "description": _safe_str(raw.get("description"), ""),
    }


# ----------------------------------------------------
# MAIN ENTRY POINT
# ----------------------------------------------------

def extract_transaction(text: str) -> dict[str, Any]:
    """
    Extracts a structured transaction dictionary from a natural
    language description, using the local Ollama LLM.

    Args:
        text: Natural language transaction description, e.g.
              "Spent ₹450 on Domino's today".

    Returns:
        A dictionary with keys: type, category, amount, merchant,
        date, month, year, description. Always returns this exact
        shape, even on failure (safe fallback values are used).

    This function never raises - all failure modes (empty input,
    Ollama unavailable, malformed AI response) result in a safe
    fallback dictionary being returned instead.
    """

    if not isinstance(text, str) or not text.strip():
        return dict(EMPTY_TRANSACTION)

    if not is_ollama_available():
        fallback = dict(EMPTY_TRANSACTION)
        fallback["description"] = text.strip()
        return fallback

    raw_response = _call_ollama(text.strip())

    if raw_response is None:
        fallback = dict(EMPTY_TRANSACTION)
        fallback["description"] = text.strip()
        return fallback

    parsed = _extract_json_object(raw_response)

    if parsed is None:
        fallback = dict(EMPTY_TRANSACTION)
        fallback["description"] = text.strip()
        return fallback

    return _validate_transaction(parsed)


# ----------------------------------------------------
# TEST
# ----------------------------------------------------

def ask_financial_assistant(user_question: str) -> str:
    """Takes a natural conversation question, looks up your Excel history, and answers contextually."""
    import excel_engine
    import pandas as pd
    import requests

    if not is_ollama_available():
        return "System Status: Local Assistant Offline. Please verify that Ollama is launched."

    # Read live values directly from our sheets
    all_txns = excel_engine.read_transactions()
    df = pd.DataFrame(all_txns, columns=['date','type','category','merchant','amount','desc','conf','month','year'])
    
    # Strip down formatting to give the AI context without wasting processing memory
    data_summary = df[['date', 'type', 'category', 'merchant', 'amount', 'month']].to_string(index=False)
    
    assistant_prompt = f"""You are FinPilot AI, a professional conversational personal finance manager. 
Below is the comprehensive financial ledger data of the user:
{data_summary}

Analyze this information critically to answer the user's question. Be direct, professional, and use currency markings (₹) explicitly when reporting calculated values.

User Question: {user_question}
FinPilot AI Response:"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": assistant_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "I encountered an error trying to process that data analysis request.")
    except Exception as e:
        return f"Failed to retrieve dynamic advice. Connection Error: {str(e)}"

if __name__ == "__main__":

    print("=" * 60)
    print("FinPilot AI - Transaction Extraction Engine")
    print("=" * 60)
    print()
    print("Ollama available:", is_ollama_available())
    print()

    sample_inputs = [
        "Spent ₹450 on Domino's today",
        "Got ₹20000 salary this month",
        "Paid ₹1200 towards credit card debt yesterday",
    ]

    for sample in sample_inputs:
        print("Input:", sample)
        result = extract_transaction(sample)
        print("Output:", json.dumps(result, indent=2))
        print()