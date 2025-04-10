import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def show_page():
    st.title("Invoice Automation Dashboard")

    # Generate Sample Sales Data
    data = {
        "Invoice ID": [f"INV{1000+i}" for i in range(20)],
        "Amount": np.random.randint(100, 1000, 20),
        "Date": pd.date_range("2025-03-01", periods=20, freq="D"),
        "Customer Name": np.random.choice(["Alice", "Bob", "Charlie", "David"], 20),
        "Product": np.random.choice(["Product A", "Product B", "Product C"], 20),
    }

    df = pd.DataFrame(data)
    st.subheader("Invoice Data")
    st.write(df)

    # Sales Revenue Over Time
    sales_over_time = df.groupby("Date")["Amount"].sum()
    st.subheader("Sales Revenue Over Time")
    sales_over_time.plot(kind="line")
    st.pyplot()

    # Sales by Product
    sales_by_product = df.groupby("Product")["Amount"].sum()
    st.subheader("Sales by Product")
    sales_by_product.plot(kind="bar")
    st.pyplot()
