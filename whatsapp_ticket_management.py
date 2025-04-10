import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import time 
# Suppress all warnings
def show_page():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    st.title("WhatsApp Bot Ticket Management")

    # Simulate Ticket Data with South Indian names and Indian Managers
    south_indian_names = [
        'Arun Kumar', 'Bala Subramanian', 'Chandra Sekhar', 'Dhivya Priya', 
        'Kavya Nair', 'Mani Raj', 'Suresh Babu', 'Ravi Kiran', 'Lakshmi Reddy', 'Sowmya Murthy',
        'Pradeep Reddy', 'Ravi Shankar', 'Madhavi Rani', 'Geetha Nair', 'Vishal Kumar',
        'Rajesh Subramanian', 'Hari Prasad', 'Vasundhara Reddy', 'Ananya Nair', 'Sreeja Iyer'
    ]
    
    indian_managers = ['Rajesh Kumar', 'Priya Nair', 'Vikram Reddy', 'Anil Sharma', 'Sunita Iyer', 'Kiran Babu', 'Divya Nair', 'Manoj Krishnan']

    # Generate 100 unique ticket users
    ticket_data = {
        "Ticket ID": [random.randint(1000, 9999) for _ in range(100)],  # 100 rows
        "Employee Name": random.sample(south_indian_names * 10, 100),  # 100 unique names
        "Detailed Message": [random.choice([
            "I am unable to access my company email on the new laptop. It keeps showing an error saying 'access denied'. I need access to be able to do my work effectively, especially since I need to access company-wide communications.",
            "The server failed during the deployment of our new web application. This is causing significant delays in the project's timeline, and the team is unable to proceed until it's fixed. It’s critical that we address this as soon as possible.",
            "A bug has been identified in the product dashboard that prevents users from saving changes to their profiles. This is impacting user experience and needs to be fixed immediately to prevent customer complaints.",
            "I’m unable to log into the company’s internal system. The error I get says 'Invalid credentials'. This is causing a major disruption to my workflow, as I need to access the project management tool to update tasks.",
            "There is an issue with the network connectivity in the office building. The Wi-Fi keeps dropping, which affects the team's ability to work efficiently. We need a solution to restore stable internet access across all floors.",
            "My request for access to the restricted server has been denied. I require access to complete my tasks for the new software deployment, and I would appreciate it if the IT department could approve it as soon as possible.",
            "The latest software update caused a system failure. Several features of the application are now unresponsive, which is slowing down the team's productivity. A fix is urgently needed to ensure the software works correctly.",
            "I would like to request an upgrade to my workstation to meet the demands of my new role. The current setup is outdated and is causing slow performance, which is affecting my efficiency in managing tasks.",
            "I’m having trouble syncing data to the cloud storage. The system is showing errors when trying to upload files, and I cannot access the documents I need for work. This is critical for the team's productivity, and I need this fixed immediately.",
            "A security vulnerability was discovered in the software system. It is possible that sensitive data is exposed, and it is essential that the vulnerability be patched immediately to prevent potential data breaches."
        ]) for _ in range(100)],  # Generate 100 detailed, descriptive issues
        "Reporting Manager": [random.choice(indian_managers) for _ in range(100)],
        "Ticket Status": [random.choice(['Open', 'Closed', 'Pending']) for _ in range(100)],
        "Priority": [random.choice(['High', 'Medium', 'Low']) for _ in range(100)],
        "Created At": pd.date_range("2025-04-01", periods=100, freq='D'),
    }

    # Create a DataFrame from the simulated ticket data
    df = pd.DataFrame(ticket_data)

    # Show the ticket table
    st.subheader("Ticket Table")
    st.write(df)

    # Metrics for Tickets Opened and Closed in the Previous Day
    yesterday = datetime.now() - timedelta(1)
    opened_yesterday = len(df[(df['Created At'].dt.date == yesterday.date()) & (df['Ticket Status'] == 'Open')])
    closed_yesterday = len(df[(df['Created At'].dt.date == yesterday.date()) & (df['Ticket Status'] == 'Closed')])

    # Metrics Card
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tickets Opened Yesterday", opened_yesterday)
    with col2:
        st.metric("Tickets Closed Yesterday", closed_yesterday)

    # Additional Metrics (8 more metrics)
    total_open_tickets = len(df[df['Ticket Status'] == 'Open'])
    total_closed_tickets = len(df[df['Ticket Status'] == 'Closed'])
    avg_resolution_time = (df['Created At'].max() - df['Created At'].min()).days / total_closed_tickets if total_closed_tickets > 0 else 0
    total_pending_tickets = len(df[df['Ticket Status'] == 'Pending'])
    high_priority_tickets = len(df[df['Priority'] == 'High'])
    low_priority_tickets = len(df[df['Priority'] == 'Low'])
    opened_this_week = len(df[(df['Created At'].dt.date >= (datetime.now() - timedelta(days=7)).date())])
    closed_this_week = len(df[(df['Created At'].dt.date >= (datetime.now() - timedelta(days=7)).date()) & (df['Ticket Status'] == 'Closed')])

    # Additional Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Open Tickets", total_open_tickets)
    with col2:
        st.metric("Total Closed Tickets", total_closed_tickets)
    with col3:
        st.metric("Average Resolution Time (Days)", round(avg_resolution_time,2))
    with col4:
        st.metric("Total Pending Tickets", total_pending_tickets)

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("High Priority Tickets", high_priority_tickets)
    with col6:
        st.metric("Low Priority Tickets", low_priority_tickets)
    with col7:
        st.metric("Tickets Opened This Week", opened_this_week)
    with col8:
        st.metric("Tickets Closed This Week", closed_this_week)

    # Visualize Ticket Status Distribution
 

    # Filter Manager and Employee Tickets
    st.subheader("Filter Tickets by Manager")
    manager_name = st.selectbox("Select Manager", df['Reporting Manager'].unique())
    
    # Filter tickets based on selected manager
    filtered_manager_df = df[df['Reporting Manager'] == manager_name]
    
    # Display filtered tickets for the selected manager
    st.write(f"Tickets reported by {manager_name}:")
    st.write(filtered_manager_df)

    # Collective Insights (Hardcoded Insights)
    st.subheader("Collective Insights")
    if st.button("Analyze"):
        st.info("Processing... Please wait.")
        progress_bar = st.progress(0)
        
        # Simulate a task that takes 10 seconds
        for i in range(1, 11):
            # Update the progress bar incrementally
            progress_bar.progress(i * 10)
            time.sleep(1)  # Wait for 1 second to simulate task progress
        
        # After the task is complete, display a message
        st.success("Please be cautiuous in taking devisions from AI gennerated insights")
    # Hardcoded insights in bullet points
        st.write("""
        - The most common issue reported by employees is **'Access request for a new device'** with a large number of tickets related to this issue.
        - **60%** of the tickets are **Open**, indicating that there are unresolved issues that need attention.
        - **Network connectivity** and **server failure** are the top causes of technical issues, impacting work productivity.
        - Most tickets are reported by employees in **Technical Support** and **Product Management** roles.
        - The average time taken to resolve tickets is around **2-3 days**, with priority given to **High Priority** issues.
        """)

# Run the function to display the page
