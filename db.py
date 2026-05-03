import sqlite3
import pandas as pd
import streamlit as st

@st.cache_resource
def load_data():
    conn = sqlite3.connect("store.db", check_same_thread=False)
    
    df = pd.read_csv("data/superstore.csv", encoding="latin1")
    df.columns = df.columns.str.strip()

    # ✅ Convert to proper datetime
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

    # ✅ Convert to SQLite-friendly format
    df["Order Date"] = df["Order Date"].dt.strftime("%Y-%m-%d")
    df["Ship Date"] = df["Ship Date"].dt.strftime("%Y-%m-%d")

    df.to_sql("orders_raw", conn, if_exists="replace", index=False)

    return conn