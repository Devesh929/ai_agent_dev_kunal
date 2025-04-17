import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import os
import tempfile
import pandas as pd
import time 
def show_page():
    # Title of the app
    st.title("OCR extraction")
    with st.expander("Individual File"):
    
        # Instructions for the user
        st.write("Upload a PDF file to view its contents.")
        col1,col2=st.columns(2)
        # File uploader widget (restricted to PDF files)
        with col1:

            uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

            if uploaded_file is not None:
                st.info("Processing... Please wait.")
                progress_bar = st.progress(0)
                
                # Simulate a task that takes 10 seconds
                for i in range(1, 11):
                    # Update the progress bar incrementally
                    progress_bar.progress(i * 10)
                    time.sleep(1)  # Wait for 1 second to simulate task progress
                
                # After the task is complete, display a message
                st.success("Task Completed!")
                # Save the uploaded file to a temporary location
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_file_path = tmp_file.name  # Get the file path of the temporary file

                    # Display the uploaded file's name
                    st.write(f"Uploaded PDF file: **{uploaded_file.name}**")
                    
                    # Use the `streamlit-pdf-viewer` to display the PDF
                    pdf_viewer(temp_file_path, height=600, width=800)

                except Exception as e:
                    st.error(f"Error displaying the PDF: {e}")

                finally:
                    # Clean up the temporary file after displaying the PDF
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
            else:
                st.info("Please upload a PDF file to proceed.")
        with col2:
            if uploaded_file:
                option = st.selectbox(
                "Choose an option",
                ["Select Page number",1, 2, 3, 4],
                # Default selection (first option)
            )

            # Define markdown content for each option
                

                # Display the markdown content based on the selected option
                if option== 1:
                    st.write("Date on Signature: 12-11-24")
                    st.markdown("""
                    ```
                     Motors and Mechanical Inc.
        MASTER BILL #1407173106
        REPRINT

        FROM  Motors and Mechanical Inc.
        AT ONE ELLIS DRIVE AUBURN NY 13021 US

        CARRIER | Prepaid-Do not change

        BY DNGRDO
        TRACKING NO.

        PRINT DATE | PRINT TIME | RELEASE DATE | PLANNING POINT | MASTER BILL NO. | NO. OF DROPS:
        12/10/2024 | 13:38:01 | 12/10/2024 | 22A | 1407173106 | 0001

        SOLD TO: 372750
        APPLIED INDUSTRIAL TECH - DC
        (JR CUNIN DISTRIBUTION)
        1103 CLAREMONT RD
        CARLISLE PA 17015

        SHIP TO: 372750
        APPLIED INDUSTRIAL TECH.-2194
        (JR CUNIN DISTRIBUTION)
        1103 CLAREMONT RD
        CARLISLE PA 17015

        Contact: 717-249-0061

        SHIPPING INSTRUCTIONS:
        Stop Box Count | Weight | Name | Address
        0001 | 156EA | 1,145LB | APPLIED INDUSTRIAL TECH.-2194 | 1103 CLAREMONT RD, CARLISLE PA 17015 US

        254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356
        UPS Acct number is 17192

        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**
        372750-APPLIED INDUSTRIAL TECH.-2194 PO# 4513720966, 4513725273, 4513729771

        ITEM COUNT | KIND OF PKG, DESC. OF ARTICLES, SPECIAL MARKS, AND EXCEPTIONS | WEIGHT | CLASS OR RATE
        15 | ELECTRIC MOTORS IN BXS/CRTS <= 1500 LB OR MORE AXVGS/LB 62120 SUB 4 | 1,145 | 65

        THANK YOU FOR SHIPPING WITH A. DUE PYLE
        CUSTOMER COPY
        700 438 096

        Driver Signature acknowledges receipt of freight only
        Terms and Conditions of the Carrier's Tariffs apply

        BILL ONLY
        700 438 096

        TO EXPEDITE PAYMENT, MAIL A COPY OF THIS BILL OF LADING INCLUDING THE FREIGHT BILL TO THE FOLLOWING ADDRESS:
         Motors and Mechanical Inc.
        Freight Payment Dept
        P.O. Box 2400
        Fort Smith, AR 72902

                    ```
                    """, unsafe_allow_html=True)
                if option== 2:
                    st.markdown("""
                ```
                 Motors and Mechanical Inc.
                MASTER BILL #1407173106
                Original Master - Not Negotiable
                FROM
                 Motors and Mechanical Inc.
                AT
                ONE ELLIS DRIVE AUBURN NY 13021 US
                BY
                DM3RD0
                PRINT DATE
                PRINT TIME
                RELEASE DATE
                12/10/2024
                13:38:01
                12/10/2024
                SOLD TO:
                372750
                APPLIED INDUSTRIAL TECH - DC
                JR CUNIN DISTRIBUTION
                1103 CLAREMONT RD
                CARLISLE PA 17015
                SHIPPING INSTRUCTIONS:
                Stop
                Box Count
                Weight
                Name
                Address
                0001
                15EA
                1,145LB
                APPLIED INDUSTRIAL TECH.-2194
                1103 CLAREMONT RD, CARLISLE PA 17015 US
                254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
                Fed Ex Ground Acct number is 125726356
                UPS Acct number is 171912
                ***DO NOT STACK CONES OR STICKERS ON EVERY PALLET***
                372750-APPLIED INDUSTRIAL TECH.-2194 PO# 4513720966, 4513725273, 4513729771
                ITEM COUNT
                KIND OF PKG, DESC. OF ARTICLES, SPECIAL MARKS, AND EXCEPTIONS
                15
                SELECT MOTORS IN BX/S CRTS LBS EA OR MORE AVNXS/LB 62120 SUB 4
                WEIGHT SUBTO COR.
                1,145
                65
                CLASS OR RATE
                AGENT OR CASHIER
                PER
                (he Signature have acknowledges only the amount prepaid.)
                CHARGES:
                ADVANCED:
                $ If Charges are to be PREPAID, write or stamp here "PREPAID"
                Prepaid-Do not change
                Subject to section 7 of condition of applicable bill of lading if this shipment is to be delivered to the consignee without recourse on the consignor, the consignor shall sign the following statement: The carrier shall not make delivery of the shipment without payment of freight and other lawful charges.  Motors and Mechanical Inc.
                (Signature of Consignor)
                 Motors and Mechanical Inc.
                (Permanent post office address of shipper):
                 Motors and Mechanical Inc.
                5711 S. BOREHAM, JR ST
                FT. SMITH AR 72901
                TO EXPEDITE PAYMENT, MAIL A CO OF THIS BILL OF LADING INCLUDING THE FREIGHT BILL TO THE FOLLOWING ADDRESS:
                 Motors and Mechanical Inc.
                Freight Payment Dept
                P.O. Box 2400
                Fort Smith, AR 72902
                ```
                """, unsafe_allow_html=True)
                if option== 3:
                        st.markdown("""
                    ```
                 Motors and Bill of Lading Detail (REPRINT)

        Mechanical Inc.

        Page: 1 of 3

        CARRIER | A DUDE_EXLE INC

        FROM  Motors and Mechanical Inc.
        AT ONE ELLIS DRIVE AUBURN NY 13021

        INLAND FRT TERMS | Prepaid-Do not change

        BY DMGRDG "TRACKING NO.
        PRINT DATE PRINT TIME — RELEASE DATE PLANNING POINT_- MASTER BILL NO, DROP
        12/10/2024 | 13:38:02 | 12/30/2024 22A 1407173106 0001.

        SOLD TO: 372750
        "APPLIED INDUSTRIAL TECH - DC
        (OR CUNIN DISTRIBUTION)

        1103 CLAREMONT RD
        CARLISLE PA 17015

        SHIP TO: 372750
        APPLIED INDUSTRIAL TECH.-2194
        (JR CUNIN DISTRIBUTION)

        1103 CLAREMONT RD
        CARLISLE PA 17015

        216-426-4106 EMAIL: Corpurchasing@spotted.com

        4 1 VFSWDMS3546-E
        VFSWDMS3546-E

        216-426-4108 EMAIL: Corpurchasing@applied.com

        2 2 EMJ37711T
        EMJ37711T

        216-426-4100 EMAIL: Corpurchasing@applied.com

        2 2 CEM3546T
        CEM3546T

        216-426-4106 EMAIL: Corpurchasing@applied.com

        'KEEP ENDS MOVING. SALES MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356

        UPS Acct number is 17912

        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**
        PALLET MARK: C79192

        ORDER QTY SHIPPED BACK ORDERED PRODUCT ID DESCRIPTION WEIGHT
        2 1 0 VEUHM3546 1/. 75k 1770 1/MINREM, 3PH,60HZ,56C,352 38.0 lb
        VEUHM3546 Delivery 1512078164-000010 Sales GO: 1211816946-000080

        PO: 451372066 on 12/08/2024
        REQUEST CARRIER: AA-30JLTL-Ground, LTL BUYER = Jim Nova TELE

        254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356

        UPS Acct number is 17912

        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**

        1HP, 1770RPM, 3PH, 60Hz, 56C,3522M,TENV,FL,NJ 37.0 lb
        Delivery: 312078165-00000 Sales GO: 1211818052.000060

        PO: 4513725273 on 12/09/2024
        REQUEST CARRIER: AA-30JLTL-Ground, LTL BUYER = Jim Nova TELE

        254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356

        UPS Acct number is 17912

        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**

        4.25HP, 1770RPM, 3PH, 60Hz, 56C, 3524M, TEFC, F1 45.0 lb
        Delivery: 1312078166-000020 Sales GO: 1211821864-000020

        PO: 4513729811 on 12/10/2024
        REQUEST CARRIER: AA-30JLTL-Ground, LTL BUYER = Jim Nova TELE

        254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356

        UPS Acct number is 17912

        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**
        Packing Copy

                    ```
                    """, unsafe_allow_html=True)
            
                if option== 4:
                    st.markdown("""
                ```
                 Motors and Bill of Lading Detail (REPRINT)

        Mechanical Inc.

        PAGE: 3 of 3

        CARRIER: A DUE PYLE CO.

        FROM  Motors and Mechanical Inc.
        AT ONE ELLIS DRIVE AUBURN NY 13021

        INLAND FRT TERMS | Prepaid-Do not change

        BY DMGRDO
        TRACKING NO.

        PRINT DATE | PRINT TIME | RELEASE DATE | PLANNING POINT | MASTER BILL NO. | DROP
        12/10/2024 | 13:38:02 | 12/10/2024 | 22A | 1407173106 | 0001

        SOLD TO: 372750
        APPLIED INDUSTRIAL TECH - DC
        (JR CUNIN DISTRIBUTION)

        1103 CLAREMONT RD
        CARLISLE PA 17015

        SHIP TO: 372750
        APPLIED INDUSTRIAL TECH.-2194
        (JR CUNIN DISTRIBUTION)

        1103 CLAREMONT RD
        CARLISLE PA 17015

        SHIPPING INSTRUCTIONS:
        254T AND ABOVE PALLETS - MAX 2 ROWS HIGH
        Fed Ex Ground Acct number is 125726356
        UPS Acct number is 171912
        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**
        PACKING LIBY REQUIRED ON OUTSIDE OF PACKAGE

        MARK SHIPMENT:
        216-426-4109 EMAIL: Corpurchasing@applied.com

        ITEM COUNT KIND OF PKG, DESC. OF ARTICLES, SPECIAL MARKS, AND EXCEPTIONS WEIGHT
        2 2 VEM6315T-D SHP, 1755RPM, 3PH, 60HZ, 184TC, 3642M, TEFC, F1 117.0 lb
        VEM6315T-D Delivery: 1312078168-000070 Sales GO: 1211821584-000070
        PO #: 4513720771 on 12/10/2024
        REQUEST CARRIER: AA-30JLTL Ground, LTL BUYER = Jim Novak TELE:

        2547 AND ABOVE PALLETS - MAX 2 ROWS HIGH
        FedEx Ground Acct number 125726356
        UPS Acct number is 171912
        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**

        3.3HP, 1780RPM, 3PH, 60HZ, 56C, 3512M, TENV, N 33.0 lb
        Delivery: 1312078166-000080 Sales GO: 1211821854-000000
        PO #: 4513729771 on 12/10/2024
        REQUEST CARRIER: AA-30JLTL Ground, LTL BUYER = Jim Novak TELE:

        2547 AND ABOVE PALLETS - MAX 2 ROWS HIGH
        FedEx Ground Acct number 125726356
        UPS Acct number is 171912
        **DO NOT STACK CONES OR STICKERS ON EVERY PALLET**

        ITEMS: 15
        TOTAL WEIGHT:(LB) 1,145

        Packing Copy

                ```
                """, unsafe_allow_html=True)   
                
                
    with st.expander("Batch Processing"):
        st.write("Upload a PDF file to view its contents.")
        col11,col22=st.columns(2)
        # File uploader widget (restricted to PDF files)
        with col11:
            uploaded_file_q = st.file_uploader("Choose a PDF file", type=["pdf"],accept_multiple_files=True)     
            if uploaded_file_q:
                data = {
    'Master Bill No': [
        1407267407, 1407267407, 1407267407, 1407267407, 1407267407, 
        1407267407, 1407267407, 1407267407, 1407267407, 1407296742, 
        1407296742, 1407296742, 1407296742, 1407296742, 1407296988
    ],
    'Product ID/ Customer P/N': [
        'S36-A000-0213', 'S32-CWS0-0123', 'S36-A000-0149', 'S25-CWS0-0230', 'S18-CWS0-0189',
        'EM3546T', 'M3542', 'M358-5', 'EM37147-5', 'S36-A000-0213', 
        'S32-CWS0-0123', 'S36-A000-0149', 'S25-CWS0-0230', 'S18-CWS0-0189', 'D32-A000-0512'
    ],
    'Weight (LB ea.)': [
        1584.00, 1150.00, 1560.00, 580.00, 261.9, 
        35.00, 25.00, 22.00, 165.00, 1584.00, 
        1150.00, 1560.00, 580.00, 261.00, 'F2'
    ]
}
                # Convert the data to a pandas DataFrame
                df = pd.DataFrame(data)

                # Title for the app
                st.title("Multi-Select Dropdown Example")

                # Create a multi-select dropdown for user selection
                options = st.multiselect(
                    'Select Names to Display:',
                    options=["Product ID/ Customer P/N","Weight (lb)","Master Bill No"] , # Names of people to select from
                    default=["Master Bill No"]  # Default selection includes all names
                )

                # Create a submit button
                submit_button = st.button("Submit")

                # Display the table when the submit button is clicked
                if submit_button:
                    st.info("Processing... Please wait.")
                    progress_bar = st.progress(0)
                    
                    # Simulate a task that takes 10 seconds
                    for i in range(1, 11):
                        # Update the progress bar incrementally
                        progress_bar.progress(i * 10)
                        time.sleep(1)  # Wait for 1 second to simulate task progress
                    
                    # After the task is complete, display a message
                    st.success("Task Completed!")
                    if options:
                        # Filter the dataframe based on the selected options
                        filtered_df = df[df['Master Bill No'].isin(options)]
                        st.write("Here is the table with your selected names:")
                        st.dataframe(df)  # Display the filtered table
                    else:
                        st.write("No names selected. Please select at least one name.")
            else:
                st.write(".")
                    
