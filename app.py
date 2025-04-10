import streamlit as st
st.set_page_config(layout="wide")
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# List of pages
pages = {
    "Invoice OCR Extraction": "invoice_ocr_extraction.py",
    "WhatsApp Bot Ticket Management": "whatsapp_ticket_management.py",
    
    "Retail Store Forecasting Engine": "forecasting_engine.py",
    "Data Analysis Chatbot": "data_analysis.py",
}

# Function to display the main menu with navigation buttons
def show_main_menu():
    st.sidebar.title("AI Agent Workflow")
    # Use session_state to store selected page so that it's persistent
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = list(pages.keys())[0]  # Default to the first page
    
    # Create a selectbox to navigate between pages
    selected_page = st.sidebar.selectbox("Choose a page", list(pages.keys()), index=list(pages.keys()).index(st.session_state.selected_page))
    
    # Update session_state when a new page is selected
    if selected_page != st.session_state.selected_page:
        st.session_state.selected_page = selected_page

    return selected_page

# Show main menu or page based on navigation
back_to_main = False

# Check if the "Back to Main" button is pressed
if "back" in st.session_state:
    back_to_main = st.session_state["back"]

if back_to_main:
    # If "Back to Main" is pressed, reset the back flag and show main menu
    st.session_state["back"] = False
    button_pressed = show_main_menu()
else:
    # Show the main menu with navigation buttons
    button_pressed = show_main_menu()
    
    # Dynamically import the selected page
    page_module = __import__(pages[button_pressed].replace('.py', ''))
    
    # Show page content
    page_module.show_page()

    # Add a "Back to Main" button at the top of the page
   