import streamlit as st
import pandas as pd
import random
import numpy as np
import matplotlib.pyplot as plt
import time 
# Function to generate the custom dataset
def generate_data():
    # Simulating a dataset with 10,000 rows
    np.random.seed(42)

    SKUs = [f"SKU-{i:04d}" for i in range(1, 21)]  # 20 unique SKUs
    geographies = ["North", "South", "East", "West"]
    product_types = ["Juice", "Soda", "Water", "Tea", "Coffee"]
    seasons = ["Summer", "Winter", "Monsoon"]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

    # Creating random data
    data = {
        "SKU": [random.choice(SKUs) for _ in range(10000)],
        "Geography": [random.choice(geographies) for _ in range(10000)],
        "Product Type": [random.choice(product_types) for _ in range(10000)],
        "Season": [random.choice(seasons) for _ in range(10000)],
        "Month": [random.choice(months) for _ in range(10000)],
        "Order Quantity": [random.randint(50, 500) for _ in range(10000)],
        "Sales": [random.randint(100, 1000) * random.uniform(0.5, 2.0) for _ in range(10000)],
        "Profit": [random.randint(20, 200) * random.uniform(0.2, 1.5) for _ in range(10000)],
    }

    # Convert to a DataFrame
    df = pd.DataFrame(data)
    
    return df

# Predefined chatbot responses based on the custom dataset
def chatbot_response(user_query, df):
    query = user_query.lower()

    if "trend" in query:
        # Hardcoded response for trend analysis
        return "The trend for beverage sales over the last few months shows a steady increase. For instance, 'Juice' sales have been on the rise during the Summer season, especially in the 'South' region."
    
    elif "seasonality" in query:
        # Hardcoded response for seasonality
        return "Seasonality analysis shows that beverage sales spike during the Summer months, with a significant dip in Winter. Popular drinks during Summer include 'Juice' and 'Iced Tea'."
    
    elif "highest selling" in query:
        highest_selling = df.groupby("Product Type")["Sales"].sum().idxmax()
        return f"The highest selling product type is '{highest_selling}'."
    
    elif "total sales" in query:
        total_sales = df["Sales"].sum()
        return f"The total sales for all products is {total_sales:.2f}."
    
    elif "total profit" in query:
        total_profit = df["Profit"].sum()
        return f"The total profit for all products is {total_profit:.2f}."
    
    elif "average order quantity" in query:
        avg_quantity = df["Order Quantity"].mean()
        return f"The average order quantity is {avg_quantity:.2f} units."
    
    elif "highest selling sku" in query:
        highest_sku = df.groupby("SKU")["Sales"].sum().idxmax()
        return f"The highest selling SKU is {highest_sku}."
    
    elif "lowest selling sku" in query:
        lowest_sku = df.groupby("SKU")["Sales"].sum().idxmin()
        return f"The lowest selling SKU is {lowest_sku}."
    
    elif "sales by geography" in query:
        sales_by_geo = df.groupby("Geography")["Sales"].sum().to_frame()
        return f"Sales by geography: {sales_by_geo.to_dict()['Sales']}"
    
    elif "profit margin" in query:
        profit_margin = df["Profit"].mean() / df["Sales"].mean()
        return f"The average profit margin across all products is {profit_margin:.2f}."
    
    else:
        return "I'm sorry, I didn't quite get that. Please ask about trends, seasonality, sales, or other related questions."

# Streamlit UI
def show_page():
    st.title("Retail Data Analysis Chatbot")

    # Generate custom data (no file upload)
    df = generate_data()

    # Show the first few rows of the generated data
    st.subheader("Data Preview")
    st.write(df.head())


    # Show Metrics related to the dataset (e.g., total sales, highest selling SKU)
    st.subheader("Retail Metrics")
    col31,col32,col33=st.columns(3)
    # Total sales
    with col31:
        total_sales = df["Sales"].sum()
        st.metric("Total Sales", f"{total_sales:.2f}")

        # Highest selling SKU
        highest_sku = df.groupby("SKU")["Sales"].sum().idxmax()
        st.metric("Highest Selling SKU", highest_sku)
    with col32:
    # Total Profit
        total_profit = df["Profit"].sum()
        st.metric("Total Profit", f"{total_profit:.2f}")

        # Average order quantity
        avg_quantity = df["Order Quantity"].mean()
        st.metric("Average Order Quantity", f"{avg_quantity:.2f} units")

    # Get user input for the chatbot
    user_query = st.text_input("Ask a question about the data:")

    if user_query:
        st.info("Processing... Please wait.")
        progress_bar = st.progress(0)
        
        # Simulate a task that takes 10 seconds
        for i in range(1, 17):
            # Update the progress bar incrementally
            progress_bar.progress(i * 10)
            time.sleep(1)
        # Generate the chatbot response based on the user's query
        response = chatbot_response(user_query, df)
        st.write(f"Chatbot Response: {response}")

    


