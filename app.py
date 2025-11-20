import streamlit as st
import pandas as pd
import plotly.express as px
import io
import numpy as np

# --- 1. Mock Data (for initial view before connecting the sheet) ---
# This data is based on the CSV structure you provided.
MOCK_CSV_DATA = """
District,College,College Gender,College Type,Category,Action Taken for the Month,Action,Name,Designation,Scale,Salary Deducted,Reason,Action By,Remarks,Action for Month
Bannu,"01. Govt Postgraduate College, Bannu",Male,General,Employee,October,Explanation,Asmat ullah,Naib Qasid,3,12000,Habitual Absentiesm,Principal,,October
Bannu,"01. Govt Postgraduate College, Bannu",Male,General,Employee,October,Explanation,Ayaz Ghori,Mali,3,10000,Habitual Absentiesm,Principal,,October
Bannu,"01. Govt Postgraduate College, Bannu",Male,General,Employee,October,Explanation,Mohib ur Rehman,Naib Qasid,3,0,Proxy Attendance,Principal,,October
Bannu,"01. Govt Postgraduate College, Bannu",Male,General,Employee,October,Explanation,Zohaib Khan,Lecturer,17,0,Proxy Attendance,Principal,,October
Bannu,"02. Govt Degree College No. 2, Bannu",Male,General,Employee,October,Warning,Faqir Khan Assoc Prof,Mali,3,0,Habitual Absentiesm,Principal,,October
Bannu,"02. Govt Degree College No. 2, Bannu",Male,General,Employee,October,Warning,Shams ud Din,Naib Qasid,3,0,Habitual Absentiesm,Principal,,October
Bannu,"02. Govt Degree College No. 2, Bannu",Male,General,Employee,October,Warning,Saad Ullah Assoc Prof,Lecturer,17,0,Proxy Attendance,Principal,,October
Bannu,"02. Govt Degree College No. 2, Bannu",Male,General,Employee,October,Warning,Nazir Ahmad Shah,Naib Qasid,3,0,Proxy Attendance,Principal,,October
Bannu,"02. Govt Degree College No. 2, Bannu",Male,General,Employee,October,Warning,Hazrat Ali Khan,Mali,3,0,Habitual Absentiesm,Principal,,October
Bannu,"09. Govt Degree College, Kakki, Bannu",Male,General,Employee,October,Warning,Farid Zia A/P English,Lecturer,17,0,Habitual Absentiesm,Principal,,October
NWTD,"18. Govt Girls Degree College, Miran Shah, NWTD",Female,General,Employee,October,Inquiry,Safi Ullah,Naib Qasid,3,0,Habitual Absentiesm,Principal,,October
NWTD,"18. Govt Girls Degree College, Miran Shah, NWTD",Female,General,Employee,October,Inquiry,Usra Shahid Lab attendent,Mali,3,0,Proxy Attendance,Principal,,October
D.I. Khan,"28. Govt Degree College, Paniala, D.I. Khan",Male,General,Employee,October,Warning,Muhammad Farasat Ullah,Naib Qasid,3,0,Proxy Attendance,Principal,,October
Kohat,"61. Govt Postgraduate College, Kohat",Male,General,Employee,October,Warning,Sadiq Noor,Naib Qasid,3,0,Habitual Absentiesm,Principal,,October
Lakki Marwat,"85. Govt Degree College, Serai Naurang, Lakki Marwat",Male,General,Employee,October,Warning,Attiq Ullah Shah,Lecturer,17,0,Habitual Absentiesm,Principal,,October
"""

# --- 2. Data Loading Function ---
@st.cache_data(ttl=3600) # Cache data for 1 hour to prevent excessive external requests
def load_data(url):
    """Loads and cleans data from a published Google Sheet CSV link or uses mock data."""
    if not url:
        # Load mock data if no URL is provided
        df = pd.read_csv(io.StringIO(MOCK_CSV_DATA))
        st.info("Showing sample data. Enter your Google Sheet 'Publish to Web' CSV link above to load live data.")
    else:
        try:
            # Load data from the URL
            df = pd.read_csv(url)
        except Exception as e:
            st.error(f"Error loading data from URL. Please check the link format. Details: {e}")
            return pd.DataFrame() # Return empty DataFrame on failure

    # --- Data Cleaning and Processing ---
    df.columns = df.columns.str.strip()
    
    # Standardize column names for easier access (based on your input schema)
    df = df.rename(columns={
        'College Gender': 'Gender',
        'College Type': 'Type',
        'Salary Deducted': 'Salary',
    })
    
    # Select and reorder relevant columns
    COLUMNS_TO_KEEP = ['District', 'College', 'Gender', 'Type', 'Category', 'Action', 'Name', 'Designation', 'Salary', 'Reason']
    df = df.reindex(columns=COLUMNS_TO_KEEP, fill_value='')

    # Clean the Salary column: replace non-numeric (like empty strings) with 0 and convert to numeric
    df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce').fillna(0).astype(int)
    
    # Clean up string fields
    for col in ['District', 'College', 'Category', 'Action', 'Reason']:
        df[col] = df[col].astype(str).str.strip()

    return df

# --- 3. KPI Calculation ---
def calculate_kpis(df):
    """Calculates key metrics for the dashboard."""
    if df.empty:
        return {}
        
    kpis = {
        'Total Actions': df.shape[0],
        'Unique Colleges': df['College'].nunique(),
        'Total Salary Deducted': df['Salary'].sum(),
        'Employee Issues': df[df['Category'] == 'Employee'].shape[0],
        'Warnings': df[df['Action'].str.contains('Warning', case=False)].shape[0],
        'Explanations': df[df['Action'].str.contains('Explanation', case=False)].shape[0],
        'Inquiries': df[df['Action'].str.contains('Inquiry', case=False)].shape[0],
    }
    return kpis

# --- 4. Chart Creation ---
def create_charts(df):
    """Generates Plotly charts for visualization."""
    if df.empty:
        return
    
    st.subheader("Action Breakdown")
    
    # --- Pie Chart: Action Type Distribution ---
    action_counts = df['Action'].value_counts().reset_index()
    action_counts.columns = ['Action', 'Count']
    
    fig_pie = px.pie(
        action_counts, 
        values='Count', 
        names='Action', 
        title='Distribution of Action Types',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.Agsunset,
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

    
    st.subheader("Top Reasons for Action")
    
    # --- Bar Chart: Top Reasons ---
    reason_counts = df['Reason'].value_counts().nlargest(5).reset_index()
    reason_counts.columns = ['Reason', 'Count']

    fig_bar = px.bar(
        reason_counts, 
        x='Count', 
        y='Reason', 
        orientation='h',
        title='Top 5 Reasons for Disciplinary Action',
        color='Count',
        color_continuous_scale=px.colors.sequential.Redor,
    )
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)


# --- 5. Streamlit App Layout ---
def main():
    st.set_page_config(layout="wide", page_title="HED Monitoring Dashboard")

    st.markdown("""
        <style>
            .css-1d391kg { padding-top: 2rem; padding-bottom: 2rem; }
            .reportview-container .main .block-container { max-width: 1200px; }
            .st-emotion-cache-1r6i7l3 {background-color: #2e8b57; color: white; padding: 1.5rem; border-radius: 0.5rem;}
        </style>
        <h1 style="color:#2e8b57;">Higher Education Department</h1>
        <p style="font-size: 1.2em; color: #555;">Colleges Monitoring Action Dashboard</p>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # --- Data Input Section ---
    st.header("🔗 Connect Data Source")
    sheet_url = st.text_input(
        "Paste Google Sheet 'Publish to web' CSV Link Here:",
        help="Go to your Google Sheet > File > Share > Publish to web > Select CSV > Copy Link."
    )
    
    # Load and process data
    df = load_data(sheet_url)

    if df.empty and sheet_url:
        # If the user entered a link but it failed to load, stop here.
        return
    
    if df.empty and not sheet_url:
        # If showing mock data, continue
        pass

    # --- KPI Display ---
    st.header("📊 Key Performance Indicators")
    kpis = calculate_kpis(df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Format Currency for Display
    salary_str = f"PKR {kpis.get('Total Salary Deducted', 0):,}"
    
    col1.metric("Total Actions", kpis.get('Total Actions', 0))
    col2.metric("Unique Colleges", kpis.get('Unique Colleges', 0))
    col3.metric("Total Salary Deducted", salary_str, delta_color="inverse")
    col4.metric("Employee Issues", kpis.get('Employee Issues', 0))

    col5, col6, col7 = st.columns(3)
    col5.metric("Warnings Issued", kpis.get('Warnings', 0))
    col6.metric("Explanations Called", kpis.get('Explanations', 0))
    col7.metric("Inquiries Initiated", kpis.get('Inquiries', 0))

    st.markdown("---")
    
    # --- Charts Section ---
    st.header("📈 Visual Analysis")
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        create_charts(df)
    
    # --- Detailed Records Table (Filterable) ---
    st.markdown("---")
    st.header("📄 Detailed Records")

    # Filter/Search Widget
    search_term = st.text_input("Search records (Name, College, or Reason):", value="")
    
    if search_term:
        search_lower = search_term.lower()
        filtered_df = df[df.apply(lambda row: row.astype(str).str.lower().str.contains(search_lower).any(), axis=1)]
    else:
        filtered_df = df

    # Display the final, filtered table
    st.dataframe(
        filtered_df[['District', 'College', 'Name', 'Designation', 'Action', 'Reason', 'Salary']].style.format({
            'Salary': 'PKR {:,.0f}',
        }),
        use_container_width=True,
        hide_index=True,
        column_order=['District', 'College', 'Name', 'Designation', 'Action', 'Reason', 'Salary'],
        column_config={
            "Salary": st.column_config.NumberColumn("Salary Deducted", format="PKR %d"),
        }
    )

    if filtered_df.empty and search_term:
        st.warning(f"No records found matching '{search_term}'.")
    elif filtered_df.empty:
        st.warning("The data frame is empty.")

if __name__ == '__main__':
    main()
