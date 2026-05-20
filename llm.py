import requests
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

MODEL      = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_URL = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/generate")

def clean_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        sql_match = re.search(r'\bSELECT\b.*?;?\s*$', text, re.IGNORECASE | re.DOTALL)
        if sql_match:
            sql = sql_match.group().strip()
            return normalize_response({
                "sql": sql,
                "chart_type": infer_chart_type(sql),
                "insight": "",
            })
        raise ValueError(f"No JSON found in model response:\n{text}")
    
    raw_json = match.group()

    # Fix control characters inside JSON strings (common Ollama issue)
    # Replace literal newlines/tabs inside the matched block
    raw_json = re.sub(r'[\x00-\x1f\x7f]', ' ', raw_json)
    
    # Collapse multiple spaces into one
    raw_json = re.sub(r'  +', ' ', raw_json)
    
    return normalize_response(json.loads(raw_json))


def normalize_response(data):
    if not isinstance(data, dict):
        raise ValueError(f"Model response must be a JSON object, got: {type(data).__name__}")

    sql = str(data.get("sql", "")).strip()
    if not sql:
        raise ValueError(f"Model response did not include SQL:\n{data}")

    chart_type = str(data.get("chart_type") or infer_chart_type(sql)).strip().lower()
    if chart_type not in {"bar", "line", "table", "stacked"}:
        chart_type = infer_chart_type(sql)

    return {
        "sql": sql,
        "chart_type": chart_type,
        "insight": str(data.get("insight", "")).strip(),
    }


def infer_chart_type(sql):
    sql_lower = sql.lower()
    if any(part in sql_lower for part in ("strftime('%y-%m'", 'strftime("%y-%m"', "strftime('%m'", 'strftime("%m"')):
        return "line"
    if "group by" in sql_lower and any(
        part in sql_lower
        for part in ("group by strftime", "group by \"order date\"", "group by year", "group by month")
    ):
        return "line"
    if "group by" in sql_lower:
        return "bar"
    return "table"


def deterministic_sql(question):
    q = question.lower()
    if "monthly" not in q or not any(word in q for word in ("trend", "over time", "month")):
        return None

    metric_map = {
        "profit": ("Profit", "SUM"),
        "quantity": ("Quantity", "SUM"),
        "discount": ("Discount", "AVG"),
        "sales": ("Sales", "SUM"),
    }
    metric, agg = metric_map["sales"]
    for word, value in metric_map.items():
        if word in q:
            metric, agg = value
            break

    year_match = re.search(r"\b(20\d{2})\b", question)
    where = ""
    if year_match:
        where = f"\nWHERE STRFTIME('%Y', \"Order Date\") = '{year_match.group(1)}'"

    sql = f"""SELECT
    STRFTIME('%Y-%m', "Order Date") AS "Month",
    {agg}("{metric}") AS "{metric}"
FROM orders_raw{where}
GROUP BY "Month"
ORDER BY "Month";"""

    return {
        "sql": sql,
        "chart_type": "line",
        "insight": "",
    }


def generate_sql(question):
    deterministic = deterministic_sql(question)
    if deterministic:
        return deterministic

    prompt = f"""You are a SQL expert. Convert the user question into a valid SQLite SQL query.

Return ONLY a JSON object, no markdown, no explanation, no extra text:
{{
  "sql": "...",
  "chart_type": "bar/line/table",
  "insight": "one line insight"
}}

Table: orders_raw
Exact columns (always wrap in double quotes):
- "Order ID", "Order Date" (TEXT as YYYY-MM-DD; SQLite STRFTIME works on it)
- "Ship Date", "Ship Mode", "Customer ID", "Customer Name"
- "Segment", "Country", "City", "State", "Postal Code", "Region"
- "Product ID", "Category", "Sub-Category", "Product Name"
- "Sales" (REAL), "Quantity" (INTEGER), "Discount" (REAL), "Profit" (REAL)

Rules:
- Always wrap column names in double quotes
- For year filtering: STRFTIME('%Y', "Order Date") = '2017'
- For monthly trends: SELECT STRFTIME('%Y-%m', "Order Date") AS "Month", SUM("Sales") AS "Sales" FROM orders_raw WHERE STRFTIME('%Y', "Order Date") = '2016' GROUP BY "Month" ORDER BY "Month"
- Always ORDER BY for aggregations
- For time trends, ORDER BY the time period ascending, not by the metric
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
                    "num_ctx": 1024,
                    "num_batch": 64,
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
    except requests.exceptions.HTTPError as exc:
        body = exc.response.text if exc.response is not None else ""
        raise RuntimeError(
            f"Ollama returned HTTP {exc.response.status_code}: {body or exc}"
        ) from exc

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
