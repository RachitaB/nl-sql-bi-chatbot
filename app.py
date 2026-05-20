import streamlit as st
from db import load_data
from llm import generate_sql
from utils import run_sql, generate_chart, generate_insight
import traceback

st.set_page_config(page_title="BI Chatbot", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #f5f4f0; }
    .schema-type  { color: #185FA5; font-size: 11px; font-family: monospace; margin-right: 4px; }
    .schema-col   { font-size: 13px; margin: 2px 0 2px 16px; }
    .schema-tname { font-weight: 600; font-size: 14px; margin: 12px 0 4px; }

    .ctx-box {
        background: #eef4ff; border: 1px solid #c3d9f7;
        border-radius: 8px; padding: 10px 14px;
        margin-bottom: 4px; font-size: 12px; color: #2c4a72; line-height: 1.7;
    }
    .ctx-box b { color: #185FA5; }

    .chat-bubble-user {
        background: #185FA5; color: white; padding: 10px 16px;
        border-radius: 12px 12px 2px 12px; max-width: 75%;
        margin-left: auto; margin-bottom: 8px; font-size: 14px;
    }

    .result-card {
        border: 1px solid #e4e4e4; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 20px;
        background: #fafafa; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    .insight-pill {
        display: inline-block; background: #e6f4ee; color: #0f6e56;
        border: 1px solid #9fe1cb; border-radius: 20px;
        padding: 4px 14px; font-size: 12px; font-weight: 500; margin-bottom: 12px;
    }

    .row-meta { font-size: 12px; color: #888; margin-bottom: 4px; }

    .section-label {
        font-size: 11px; font-weight: 600; color: #888;
        letter-spacing: 0.08em; text-transform: uppercase; margin: 8px 0 6px;
    }

    div[data-testid="stButton"] > button {
        width: 100%; text-align: left; background: white;
        border: 1px solid #ddd; border-radius: 10px;
        padding: 9px 13px; font-size: 12.5px; color: #111;
        margin-bottom: 5px; cursor: pointer; transition: all 0.15s;
    }
    div[data-testid="stButton"] > button:hover {
        background: #e8f0fb; border-color: #185FA5; color: #185FA5;
    }

    .empty-state { text-align: center; color: #888; margin-top: 100px; }
    .empty-title  { font-size: 20px; font-weight: 500; color: #333; margin-bottom: 6px; }

    .bottom-spacer { height: 90px; }
</style>
""", unsafe_allow_html=True)

conn = load_data()

# ── Session state ─────────────────────────────────────────────────────────────
for key, val in [("history", []), ("prefill", ""), ("submitted", False), ("last_error", None)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**SCHEMA**")
    schema = {
        "orders_raw": [
            ("str", "Order ID"),     ("str", "Order Date"),
            ("str", "Ship Mode"),    ("str", "Customer Name"),
            ("str", "Segment"),      ("str", "City"),
            ("str", "State"),        ("str", "Region"),
            ("str", "Category"),     ("str", "Sub-Category"),
            ("str", "Product Name"),
            ("num", "Sales"),        ("int", "Quantity"),
            ("num", "Discount"),     ("num", "Profit"),
        ]
    }
    for table, cols in schema.items():
        st.markdown(f'<div class="schema-tname">▼ {table}</div>', unsafe_allow_html=True)
        for dtype, col in cols:
            st.markdown(
                f'<div class="schema-col"><span class="schema-type">{dtype}</span>{col}</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("""
    <div class="ctx-box">
        <b>📦 Dataset Context</b><br>
        US Superstore retail orders<br>
        <b>Period:</b> 2014 – 2017<br>
        <b>Geography:</b> United States (49 states)<br>
        <b>Segments:</b> Consumer · Corporate · Home Office<br>
        <b>Categories:</b> Furniture · Office Supplies · Technology
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="section-label">Try asking</div>', unsafe_allow_html=True)

    suggestions = [
        "Compare sales and profit by category",
        "Show profit by region",
        "Monthly sales trend for 2016",
        "Top 10 cities by sales in 2017",
        "Which segment is most profitable?",
        "Sales vs profit by region",
        "Top 5 sub-categories by profit",
    ]
    for s in suggestions:
        if st.button(s, key=f"sugg_{s}"):
            st.session_state.prefill   = s
            st.session_state.submitted = True
            st.rerun()

    st.markdown("---")
    if st.session_state.history:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.history = []
            st.rerun()

# ── Main panel ────────────────────────────────────────────────────────────────
if not st.session_state.history:
    st.markdown("""
    <div class="empty-state">
        <div style="font-size:44px">📊</div>
        <div class="empty-title">Ask anything about your data</div>
        <div>Type in plain English — get SQL + results</div>
        <div style="margin-top:10px; font-size:12px; color:#bbb;">
            US Superstore · 2014–2017 · 49 States
        </div>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.last_error:
    st.error(st.session_state.last_error["message"])
    with st.expander("Error details"):
        st.code(st.session_state.last_error["traceback"])

# Chat history
for i, entry in enumerate(st.session_state.history):

    # User bubble (right-aligned)
    st.markdown(f'<div class="chat-bubble-user">{entry["question"]}</div>',
                unsafe_allow_html=True)

    # Result card
    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    # Insight pill
    st.markdown(f'<div class="insight-pill">💡 {entry["insight"]}</div>',
                unsafe_allow_html=True)

    # SQL (collapsed by default)
    with st.expander("📜 View SQL"):
        st.code(entry["sql"], language="sql")

    # Chart + download
    if entry.get("chart_path"):
        st.image(entry["chart_path"], use_container_width=True)
        with open(entry["chart_path"], "rb") as f:
            st.download_button(
                "⬇ Download chart", f,
                file_name="chart.png", mime="image/png",
                key=f"dl_chart_{i}"
            )

    # Row count + CSV download
    df = entry["df"]
    col_meta, col_dl = st.columns([3, 1])
    with col_meta:
        st.markdown(
            f'<div class="row-meta">{len(df)} row{"s" if len(df) != 1 else ""} returned</div>',
            unsafe_allow_html=True
        )
    with col_dl:
        st.download_button(
            "⬇ CSV", df.to_csv(index=False),
            file_name="result.csv", mime="text/csv",
            key=f"dl_csv_{i}"
        )

    # Dataframe — color negative Profit red
    if "Profit" in df.columns:
        def color_profit(val):
            if isinstance(val, (int, float)) and val < 0:
                return "color: #c0392b; font-weight: 500"
            return ""
        st.dataframe(
            df.style.applymap(color_profit, subset=["Profit"]),
            use_container_width=True
        )
    else:
        st.dataframe(df, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Spacer above fixed bar
st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)

# Auto-scroll to latest message
st.markdown("""
<script>
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
</script>
""", unsafe_allow_html=True)

# ── Input bar (bottom) ────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])

with col_input:
    question = st.text_input(
        label="Ask a data question",
        value=st.session_state.prefill,
        placeholder="e.g. Compare sales and profit by region",
        label_visibility="collapsed",
        key="question_input",
        on_change=lambda: st.session_state.update({"submitted": True})
    )

with col_btn:
    clicked = st.button("Ask ↗", use_container_width=True, type="primary")

# Consume prefill so it doesn't loop
if st.session_state.prefill:
    st.session_state.prefill = ""

# ── Run query ─────────────────────────────────────────────────────────────────
if (clicked or st.session_state.submitted) and question.strip():
    st.session_state.submitted = False
    st.session_state.last_error = None

    with st.status("🤖 Generating SQL...", expanded=True) as status:
        try:
            response   = generate_sql(question)
            sql        = response["sql"]
            chart_type = response["chart_type"]
            print(f"\n[GENERATED SQL]\n{sql}\n")

            status.update(label="📊 Running query...")
            df = run_sql(sql, conn)

            status.update(label="🎨 Building chart...")
            chart_path = generate_chart(df, chart_type)
            insight    = generate_insight(df)

            status.update(label="✅ Done!", state="complete", expanded=False)

            st.session_state.history.append({
                "question":   question,
                "sql":        sql,
                "df":         df,
                "chart_path": chart_path,
                "insight":    insight,
            })

        except Exception as e:
            status.update(label="❌ Error", state="error", expanded=False)
            st.session_state.last_error = {
                "message": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
            print(st.session_state.last_error["traceback"])

    st.rerun()
