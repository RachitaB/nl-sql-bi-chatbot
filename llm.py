import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

MODEL      = os.getenv("OLLAMA_MODEL", "qwen2.5-coder")
OLLAMA_URL = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")

def clean_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in model response:\n{text}")
    
    raw_json = match.group()

    # Fix control characters inside JSON strings (common Ollama issue)
    # Replace literal newlines/tabs inside the matched block
    raw_json = re.sub(r'[\x00-\x1f\x7f]', ' ', raw_json)
    
    # Collapse multiple spaces into one
    raw_json = re.sub(r'  +', ' ', raw_json)
    
    return json.loads(raw_json)

def generate_sql(question):
    prompt = f"""You are a SQL expert. Convert the user question into a valid SQLite SQL query.

Return ONLY a JSON object, no markdown, no explanation, no extra text:
{{
  "sql": "...",
  "chart_type": "bar/line/table",
  "insight": "one line insight"
}}

Table: orders_raw
Exact columns (always wrap in double quotes):
- "Order ID", "Order Date" (TEXT as MM/DD/YYYY, use STRFTIME for year filtering)
- "Ship Date", "Ship Mode", "Customer ID", "Customer Name"
- "Segment", "Country", "City", "State", "Postal Code", "Region"
- "Product ID", "Category", "Sub-Category", "Product Name"
- "Sales" (REAL), "Quantity" (INTEGER), "Discount" (REAL), "Profit" (REAL)

Rules:
- Always wrap column names in double quotes
- For year filtering: STRFTIME('%Y', "Order Date") = '2017'
- Always ORDER BY for aggregations
- Use LIMIT 10 for city/product level queries
- chart_type = "bar" for category/region/segment comparisons
- chart_type = "line" for time-based trends
- chart_type = "table" for raw row queries

Question: {question}

JSON:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model":  MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "num_predict": 400,
                }
            },
            timeout=120        # wait up to 2 min (first run loads model into RAM)
        )
        response.raise_for_status()

    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach Ollama. Is it running? Start it with: ollama serve")
    except requests.exceptions.Timeout:
        raise RuntimeError("Ollama timed out. Try a smaller model like llama3.2")

    raw = response.json().get("response", "").strip()

    # debug — remove this line once it's working
    print(f"\n[OLLAMA RAW RESPONSE]\n{raw}\n")

    if not raw:
        raise ValueError(
            "Ollama returned an empty response. "
            "The model may still be loading — wait 30s and try again. "
            f"Model in use: {MODEL}"
        )

    return clean_json(raw)