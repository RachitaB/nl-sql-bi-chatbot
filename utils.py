import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import time
import os

CHART_DIR = "charts"
os.makedirs(CHART_DIR, exist_ok=True)

BLUE    = "#185FA5"
GREEN   = "#1D9E75"
ORANGE  = "#D85A30"
PURPLE  = "#6C5CE7"
PALETTE = [BLUE, GREEN, ORANGE, PURPLE, "#BA7517", "#993556"]


def run_sql(sql, conn):
    return pd.read_sql_query(sql, conn)


def _save(fig, prefix="chart"):
    path = os.path.join(CHART_DIR, f"{prefix}_{int(time.time())}.png")
    fig.savefig(path, bbox_inches="tight", dpi=130)
    plt.close(fig)
    return path


def _fmt_val(v):
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if abs(v) >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


def generate_chart(df, chart_type):
    if df.empty or chart_type == "table":
        return None

    num_cols  = df.select_dtypes(include="number").columns.tolist()
    str_cols  = df.select_dtypes(exclude="number").columns.tolist()
    label_col = str_cols[0] if str_cols else df.columns[0]

    # Sort by first numeric col descending
    if num_cols:
        df = df.sort_values(by=num_cols[0], ascending=False).reset_index(drop=True)

    # Two numeric columns → grouped bar (Sales vs Profit etc.)
    if len(num_cols) >= 2 and chart_type in ("bar", "stacked"):
        return _grouped_bar(df, label_col, num_cols[:2])

    if chart_type == "bar" and num_cols:
        return _single_bar(df, label_col, num_cols[0])

    if chart_type == "line" and num_cols:
        return _line_chart(df, label_col, num_cols)

    # Fallback
    if num_cols:
        return _single_bar(df, label_col, num_cols[0])

    return None


def _single_bar(df, label_col, val_col):
    top = df.head(12)
    fig, ax = plt.subplots(figsize=(8, 4.5))

    bars = ax.barh(top[label_col][::-1], top[val_col][::-1],
                   color=BLUE, height=0.6)

    for bar in bars:
        w = bar.get_width()
        ax.text(w * 1.01, bar.get_y() + bar.get_height() / 2,
                _fmt_val(w), va="center", ha="left", fontsize=9, color="#333")

    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: _fmt_val(x)))
    ax.set_xlabel(val_col, fontsize=10)
    ax.set_title(f"{val_col} by {label_col}", fontsize=11, pad=10, color="#333")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)
    fig.tight_layout()
    return _save(fig, "bar")


def _grouped_bar(df, label_col, val_cols):
    top    = df.head(10)
    labels = top[label_col].tolist()
    x      = list(range(len(labels)))
    width  = 0.38

    fig, ax = plt.subplots(figsize=(9, 5))

    bars1 = ax.bar([i - width / 2 for i in x], top[val_cols[0]], width,
                   label=val_cols[0], color=BLUE,  alpha=0.9)
    bars2 = ax.bar([i + width / 2 for i in x], top[val_cols[1]], width,
                   label=val_cols[1], color=GREEN, alpha=0.9)

    max_val = max(top[val_cols[0]].max(), top[val_cols[1]].max())
    offset  = max_val * 0.012

    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                _fmt_val(h), ha="center", va="bottom", fontsize=7.5, color="#333")
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                _fmt_val(h), ha="center", va="bottom", fontsize=7.5, color="#333")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _fmt_val(v)))
    ax.legend(fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(f"{val_cols[0]} vs {val_cols[1]} by {label_col}",
                 fontsize=11, pad=10, color="#333")
    fig.tight_layout()
    return _save(fig, "grouped")


def _line_chart(df, label_col, val_cols):
    fig, ax = plt.subplots(figsize=(9, 4.5))

    for i, col in enumerate(val_cols[:3]):
        ax.plot(df[label_col], df[col], marker="o", markersize=4,
                label=col, color=PALETTE[i], linewidth=2)
        last_x = df[label_col].iloc[-1]
        last_y = df[col].iloc[-1]
        ax.annotate(_fmt_val(last_y), xy=(last_x, last_y),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=8, color=PALETTE[i])

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: _fmt_val(v)))
    step = max(1, len(df) // 8)
    ax.set_xticks(df[label_col][::step])
    ax.set_xticklabels(df[label_col][::step], rotation=35, ha="right", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)

    title = f"{', '.join(val_cols[:3])} over {label_col}"
    ax.set_title(title, fontsize=11, pad=10, color="#333")

    if len(val_cols) > 1:
        ax.legend(fontsize=9)

    fig.tight_layout()
    return _save(fig, "line")


def generate_insight(df):
    if df.empty:
        return "No results returned."

    num_cols = df.select_dtypes(include="number").columns.tolist()
    str_cols = df.select_dtypes(exclude="number").columns.tolist()

    if not num_cols:
        return "Query executed successfully."

    df_s = df.sort_values(by=num_cols[0], ascending=False)
    top  = df_s.iloc[0]

    if str_cols and len(num_cols) >= 2:
        return (f"{top.iloc[0]} leads with {num_cols[0]} of "
                f"{_fmt_val(top[num_cols[0]])} and "
                f"{num_cols[1]} of {_fmt_val(top[num_cols[1]])}")

    if str_cols:
        return (f"{top.iloc[0]} has the highest {num_cols[0]} "
                f"of {_fmt_val(top[num_cols[0]])}")

    return "Query executed successfully."