from google import genai
import os
import json
import re
from dotenv import load_dotenv

def clean_json(text):
    text = re.sub(r"```json|```", "", text).strip()
    return json.loads(text)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_sql(question):
    prompt = f"""
    Convert the user question into a valid SQLite SQL query.

    Return ONLY a JSON object, no markdown, no explanation:
    {{
      "sql": "...",
      "chart_type": "bar/line/table",
      "insight": "one line insight"
    }}

    Table: orders_raw
    Exact columns (use these names exactly, with quotes around names that have spaces or hyphens):
    - "Row ID"
    - "Order ID"
    - "Order Date"   (TEXT stored as MM/DD/YYYY, use STRFTIME for year filtering)
    - "Ship Date"
    - "Ship Mode"
    - "Customer ID"
    - "Customer Name"
    - "Segment"
    - "Country"
    - "City"
    - "State"
    - "Postal Code"
    - "Region"
    - "Product ID"
    - "Category"
    - "Sub-Category"  (must always be written as "Sub-Category" with quotes)
    - "Product Name"
    - "Sales"
    - "Quantity"
    - "Discount"
    - "Profit"

    Rules:
    - Always wrap column names in double quotes: "City", "Sub-Category", "Order Date"
    - For year filtering: STRFTIME('%Y', "Order Date") = '2017'
    - Always use ORDER BY with aggregations
    - Use LIMIT 10 for city/product level queries to keep results readable

    Question: {question}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return clean_json(response.text)