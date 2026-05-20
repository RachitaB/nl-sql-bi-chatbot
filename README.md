# NL-to-SQL BI Chatbot

Ask business questions in plain English and get SQL queries, charts, and insights from a local SQLite database.

Built using Python, Streamlit, Ollama, SQLite, Pandas, and Matplotlib.

---

## Features

- Convert natural-language business questions into SQLite queries using a local LLM
- Execute queries against a US Superstore SQLite database
- Generate:
  - Bar charts
  - Line charts
  - Grouped comparison charts
  - Data tables
- Handle monthly trend analysis with deterministic SQL logic
- Support both JSON and raw SQL responses from the LLM
- Detect multi-metric queries and generate comparison charts automatically
- Highlight negative profit values in outputs
- Display detailed error traces inside the Streamlit app
- Export charts and results as CSV files

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | Streamlit |
| Local LLM | Ollama + llama3.2 |
| Database | SQLite |
| Data Processing | Pandas |
| Visualization | Matplotlib |
| Dataset | US Superstore Orders |

---

## Requirements

- Python 3.14
- Ollama installed and running locally
- `llama3.2:latest` model pulled in Ollama
- Dependencies listed in `requirements.txt`

---
## Demo

```md
https://youtu.be/GZby-QbjRM4
```
---

---

## Project Setup

### 1. Install Dependencies

```powershell
python -m pip install --user -r requirements.txt
```

### 2. Install Ollama Model

```powershell
ollama pull llama3.2
```

### 3. Configure Environment Variables

Create a `.env` file from `.env.example`:

```powershell
Copy-Item .env.example .env
```

### 4. Run the Application

```powershell
.\run_app.ps1
```

### 5. Open the Application

After starting Streamlit, open:

```text
http://localhost:8501
```

---

## Environment Configuration

Default `.env` values:

```env
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:latest
```

### Ollama Memory Settings

The application uses optimized low-memory settings in `llm.py`:

```python
"num_ctx": 1024,
"num_batch": 64,
```

These settings help the application run efficiently on systems with limited RAM.

---

## Sample Questions

- Compare sales and profit by category
- Show profit by region
- Monthly sales trend for 2016
- Top 10 cities by sales in 2017
- Which segment is most profitable?
- Sales vs profit by region
- Top 5 sub-categories by profit

---

## Troubleshooting

### Ollama HTTP 500 Error

This is usually caused by insufficient memory.

Possible fixes:
- Close memory-intensive applications
- Restart Ollama
- Use a smaller LLM model

### Python Import Errors

If Python cannot import packages such as `dotenv` or `streamlit`, run the application using:

```powershell
.\run_app.ps1
```

This script automatically updates `PYTHONPATH` to include user-installed Python packages.

---

## Future Improvements

- Add support for multiple database engines
- Improve SQL validation and query correction
- Add conversational memory for follow-up questions
- Enhance dashboard visualizations
- Deploy using Docker or cloud platforms

---

## License

This project is intended for learning and experimentation purposes.
