# NL-to-SQL BI Chatbot

Ask business questions in plain English and get SQL, charts, and quick insights from a local SQLite database.

Built with Python, Streamlit, Ollama, SQLite, Pandas, and Matplotlib.

## Demo

Add your app recording here:

```md
[Watch the demo](https://youtu.be/GZby-QbjRM4)
```

You can upload the recording to GitHub by dragging it into a release, an issue, or the README editor, then replacing the placeholder above with the generated link.

## What It Does

- Converts natural-language business questions into SQLite queries using a local LLM.
- Runs queries against a US Superstore SQLite database.
- Builds bar charts, line charts, grouped comparisons, and tables.
- Handles monthly trend questions with deterministic SQL for reliable date logic.
- Accepts both JSON and raw SQL responses from the local model.
- Detects multi-metric queries and switches to side-by-side comparison charts.
- Color-codes negative profit values in results.
- Shows detailed error traces inside the Streamlit app when something fails.
- Supports one-click CSV and chart downloads.

## Tech Stack

| Layer | Tool |
| --- | --- |
| App | Streamlit |
| Local LLM | Ollama + llama3.2 |
| Database | SQLite |
| Data work | Pandas |
| Charts | Matplotlib |
| Dataset | US Superstore orders |

## Requirements

- Python 3.14
- Ollama running locally
- `llama3.2:latest` pulled in Ollama
- Project dependencies from `requirements.txt`

This project currently runs without a virtual environment. `run_app.ps1` sets `PYTHONPATH` so Python can find packages installed in the user site-packages directory.

## Setup

1. Install dependencies:

   ```powershell
   python -m pip install --user -r requirements.txt
   ```

2. Install and start Ollama:

   ```powershell
   ollama pull llama3.2
   ```

3. Create a `.env` file from `.env.example`:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Run the Streamlit app:

   ```powershell
   .\run_app.ps1
   ```

5. Open the local URL Streamlit prints, usually:

   ```text
   http://localhost:8501
   ```

## Environment

Default `.env` values:

```env
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2:latest
```

The app uses lower-memory Ollama settings in `llm.py`:

```python
"num_ctx": 1024,
"num_batch": 64,
```

These settings help the app run on machines with limited free RAM.

## Sample Questions

- Compare sales and profit by category
- Show profit by region
- Monthly sales trend for 2016
- Top 10 cities by sales in 2017
- Which segment is most profitable?
- Sales vs profit by region
- Top 5 sub-categories by profit

## Troubleshooting

If Ollama returns HTTP 500, it is often a memory issue. Close memory-heavy apps, restart Ollama, or use a smaller model.

If Python cannot import `dotenv` or `streamlit`, run the app with:

```powershell
.\run_app.ps1
```

That script adds the Python user package directory to `PYTHONPATH` before launching Streamlit.
