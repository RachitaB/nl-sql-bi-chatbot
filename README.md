# 🧠 NL-to-SQL BI Chatbot

Ask business questions in plain English — get SQL, charts, and insights instantly.

Built with Python · Streamlit · Ollama (qwen2.5-coder) · SQLite

---

## 💡 What it does
- Converts natural language to SQL using a local LLM (no API costs)
- Executes queries against a real SQLite database (US Superstore 2014–2017)
- Renders grouped bar charts, line trends, and data tables automatically
- Detects multi-metric queries and switches to side-by-side comparison charts
- Color-codes negative profit values in results
- One-click CSV and chart downloads

## 🛠 Tech Stack
| Layer | Tool |
|---|---|
| Frontend | Streamlit |
| LLM | Ollama + qwen2.5-coder (runs locally) |
| Database | SQLite |
| Charts | Matplotlib |
| Data | Kaggle US Superstore dataset |

## 🚀 Run it locally
1. Install Ollama from https://ollama.com
2. Pull the model: `ollama pull qwen2.5-coder`
3. Clone this repo and install dependencies:
   pip install -r requirements.txt
4. Add your .env file (see .env.example)
5. Run: `streamlit run app.py`

## 📊 Sample questions to try
- Compare sales and profit by category
- Top 10 cities by sales in 2017
- Monthly sales trend for 2016
- Which segment is most profitable?
