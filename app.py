import streamlit as st
st.set_page_config(layout="wide")
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
# Inject CSS to add background image to sidebar
sidebar_bg_image_path = "data:image/png;base64,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"
sidebar_style = f"""
    <style>
        [data-testid="stSidebarContent"] {{
            background-image: url("{sidebar_bg_image_path}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}
    </style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)
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
   
