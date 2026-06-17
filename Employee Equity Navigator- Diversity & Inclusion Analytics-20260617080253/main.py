import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Employee Equity Navigator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
@st.cache_data
def load_and_preprocess_data(uploaded_file):
    """Loads CSV, cleans column names, and performs basic type conversions."""
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('[^A-Za-z0-9_]+', '', regex=True)

    # Convert common date columns if they exist
    date_cols = ['HireDate', 'PromotionDate', 'ExitDate']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Convert salary to numeric
    if 'Salary' in df.columns:
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')

    return df

def calculate_pay_gap(df, demographic_col='Gender', salary_col='Salary'):
    """Calculates pay gap based on a demographic column."""
    if demographic_col not in df.columns or salary_col not in df.columns:
        return None, "Required columns not found for pay gap analysis."

    df_cleaned = df.dropna(subset=[demographic_col, salary_col])
    if df_cleaned.empty:
        return None, "No data available for pay gap analysis after dropping NaNs."

    avg_salaries = df_cleaned.groupby(demographic_col)[salary_col].mean().sort_values(ascending=False)
    if len(avg_salaries) < 2:
        return None, f"Not enough distinct groups in '{demographic_col}' for pay gap analysis."

    # Compare highest earner group to others
    reference_group = avg_salaries.index[0]
    reference_salary = avg_salaries.iloc[0]

    pay_gap_data = []
    for group, avg_salary in avg_salaries.items():
        if group != reference_group:
            gap_percentage = ((reference_salary - avg_salary) / reference_salary) * 100 if reference_salary > 0 else 0
            pay_gap_data.append({
                'Demographic_Group': group,
                'Average_Salary': avg_salary,
                'Reference_Group_Average_Salary': reference_salary,
                'Pay_Gap_Pct_vs_Reference': gap_percentage
            })
    return pd.DataFrame(pay_gap_data), f"Pay gap analyzed against '{reference_group}'."


def calculate_promotion_rate(df, demographic_col='Gender', promotion_col='PromotionDate'):
    """Calculates promotion rate based on a demographic column."""
    if demographic_col not in df.columns:
        return None, f"'{demographic_col}' column not found for promotion rate analysis."

    df_temp = df.copy()
    df_temp['Promoted'] = False

    if promotion_col in df_temp.columns:
        # Consider promotions within the last year from current date
        one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        df_temp['Promoted'] = (df_temp[promotion_col] >= one_year_ago)
    else:
        return None, f"Neither '{promotion_col}' nor an assumed 'Promoted' boolean column found for promotion rate analysis. Consider adding a 'PromotionDate' or 'PromotedLastYear' column."

    promotion_summary = df_temp.groupby(demographic_col)['Promoted'].agg(['sum', 'count'])
    promotion_summary['Promotion_Rate_Pct'] = (promotion_summary['sum'] / promotion_summary['count']) * 100
    promotion_summary = promotion_summary.reset_index().rename(columns={'sum': 'Promoted_Count', 'count': 'Total_Employees'})
    return promotion_summary, None

def calculate_retention_rate(df, demographic_col='Gender', hire_date_col='HireDate', exit_date_col='ExitDate'):
    """Calculates retention rate based on a demographic column for a given period."""
    if not all(col in df.columns for col in [demographic_col, hire_date_col, exit_date_col]):
        return None, "Required date columns (HireDate, ExitDate) for retention analysis are missing."

    df_cleaned = df.dropna(subset=[demographic_col, hire_date_col])
    if df_cleaned.empty:
        return None, "No data available for retention analysis after dropping NaNs."

    # Employees currently active (no exit date or exit date is in the future)
    active_employees = df_cleaned[df_cleaned[exit_date_col].isnull() | (df_cleaned[exit_date_col] > datetime.datetime.now())]
    
    # Group by demographic and calculate counts
    total_by_demographic = df_cleaned.groupby(demographic_col).size().reset_index(name='Total_Employees_Recorded')
    active_by_demographic = active_employees.groupby(demographic_col).size().reset_index(name='Active_Employees')

    retention_summary = pd.merge(total_by_demographic, active_by_demographic, on=demographic_col, how='left')
    retention_summary['Active_Employees'] = retention_summary['Active_Employees'].fillna(0).astype(int)
    retention_summary['Retention_Rate_Pct'] = (retention_summary['Active_Employees'] / retention_summary['Total_Employees_Recorded']) * 100
    
    return retention_summary, None


# --- Main Application ---
st.title("📊 Employee Equity Navigator: Diversity & Inclusion Analytics")
st.markdown("""
    This application helps organizations analyze their workforce diversity and inclusion metrics.
    Upload your employee data (CSV) to get insights into demographics, pay equity, promotion rates, and retention.
    
    **Expected CSV Columns (case-insensitive, underscores preferred):**
    `EmployeeID`, `Gender`, `Ethnicity`, `AgeGroup` (or `Age`), `Department`, `Role`, `Salary`, `HireDate`, `PromotionDate` (optional), `ExitDate` (optional), `LeadershipRole` (boolean, optional)
""")

uploaded_file = st.sidebar.file_uploader("Upload your Employee Data CSV", type="csv")

if uploaded_file is not None:
    df_original = load_and_preprocess_data(uploaded_file)
    st.sidebar.success("Data loaded successfully!")

    if df_original.empty:
        st.error("The uploaded CSV is empty or could not be parsed.")
        st.stop()

    st.sidebar.subheader("Data Filters")

    # Dynamic filters based on available columns
    
    selected_department = st.sidebar.multiselect(
        "Filter by Department",
        options=df_original['Department'].unique().tolist() if 'Department' in df_original.columns else [],
        default=df_original['Department'].unique().tolist() if 'Department' in df_original.columns else []
    )
    
    selected_role = st.sidebar.multiselect(
        "Filter by Role",
        options=df_original['Role'].unique().tolist() if 'Role' in df_original.columns else [],
        default=df_original['Role'].unique().tolist() if 'Role' in df_original.columns else []
    )

    # Apply filters
    filtered_df = df_original.copy()
    if 'Department' in filtered_df.columns and selected_department:
        filtered_df = filtered_df[filtered_df['Department'].isin(selected_department)]
    if 'Role' in filtered_df.columns and selected_role:
        filtered_df = filtered_df[filtered_df['Role'].isin(selected_role)]

    if filtered_df.empty:
        st.warning("No data matches the selected filters. Please adjust your selections.")
        st.stop()

    st.subheader("Raw Data Preview (Filtered)")
    st.dataframe(filtered_df.head())

    st.markdown("---")
    st.header("📈 Diversity & Inclusion Dashboard")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Demographics Overview", "Pay Equity Analysis", "Promotion & Growth", "Retention Insights", "Leadership Representation"])

    with tab1:
        st.subheader("Demographics Overview")
        col1, col2, col3 = st.columns(3)

        # Gender Distribution
        if 'Gender' in filtered_df.columns:
            gender_counts = filtered_df['Gender'].value_counts().reset_index()
            gender_counts.columns = ['Gender', 'Count']
            fig_gender = px.pie(gender_counts, values='Count', names='Gender', title='Gender Distribution')
            col1.plotly_chart(fig_gender, use_container_width=True)
        else:
            col1.info("Gender column not found for analysis.")

        # Ethnicity Distribution
        if 'Ethnicity' in filtered_df.columns:
            ethnicity_counts = filtered_df['Ethnicity'].value_counts().reset_index()
            ethnicity_counts.columns = ['Ethnicity', 'Count']
            fig_ethnicity = px.pie(ethnicity_counts, values='Count', names='Ethnicity', title='Ethnicity Distribution')
            col2.plotly_chart(fig_ethnicity, use_container_width=True)
        else:
            col2.info("Ethnicity column not found for analysis.")

        # Age Group Distribution
        age_col_present = 'AgeGroup' if 'AgeGroup' in filtered_df.columns else ('Age' if 'Age' in filtered_df.columns else None)
        if age_col_present:
            df_with_age_group = filtered_df.copy()
            if age_col_present == 'Age': # If only 'Age' is present, create AgeGroup
                bins = [0, 25, 35, 45, 55, 65, 100]
                labels = ['<25', '25-34', '35-44', '45-54', '55-64', '65+']
                df_with_age_group['AgeGroup_Derived'] = pd.cut(df_with_age_group['Age'], bins=bins, labels=labels, right=False, ordered=True)
                age_col_display = 'AgeGroup_Derived'
            else:
                age_col_display = age_col_present # Use existing AgeGroup
            
            if age_col_display in df_with_age_group.columns:
                age_counts = df_with_age_group[age_col_display].value_counts().sort_index().reset_index()
                age_counts.columns = ['Age_Group', 'Count']
                fig_age = px.bar(age_counts, x='Age_Group', y='Count', title='Age Group Distribution')
                col3.plotly_chart(fig_age, use_container_width=True)
            else:
                col3.info(f"Could not process {age_col_display} for age group analysis.")
        else:
            col3.info("Age or AgeGroup column not found for analysis.")

        st.markdown("### Diversity across Departments")
        demographic_options_for_dept = [col for col in ['Gender', 'Ethnicity', 'AgeGroup'] if col in filtered_df.columns]
        if 'Age' in filtered_df.columns and 'AgeGroup' not in filtered_df.columns: # Add derived AgeGroup if only Age is present
            temp_df_for_select = filtered_df.copy()
            bins = [0, 25, 35, 45, 55, 65, 100]
            labels = ['<25', '25-34', '35-44', '45-54', '55-64', '65+']
            temp_df_for_select['AgeGroup_Derived'] = pd.cut(temp_df_for_select['Age'], bins=bins, labels=labels, right=False, ordered=True)
            demographic_options_for_dept.append('AgeGroup_Derived')
            df_to_use_for_dept_breakdown = temp_df_for_select
        else:
            df_to_use_for_dept_breakdown = filtered_df

        demographic_col_for_dept = st.selectbox("Select Demographic for Department Breakdown", 
                                                options=demographic_options_for_dept,
                                                key='dept_demographic')
        if 'Department' in df_to_use_for_dept_breakdown.columns and demographic_col_for_dept:
            dept_diversity = df_to_use_for_dept_breakdown.groupby('Department')[demographic_col_for_dept].value_counts(normalize=True).unstack().fillna(0)
            st.dataframe(dept_diversity)
            fig_dept_diversity = px.bar(
                df_to_use_for_dept_breakdown.groupby(['Department', demographic_col_for_dept]).size().reset_index(name='Count'),
                x='Department',
                y='Count',
                color=demographic_col_for_dept,
                title=f'{demographic_col_for_dept} Distribution by Department',
                barmode='group'
            )
            st.plotly_chart(fig_dept_diversity, use_container_width=True)
        else:
            st.info("Department column or selected demographic not found for analysis.")


    with tab2:
        st.subheader("Pay Equity Analysis")
        pay_demographic_col = st.selectbox("Analyze Pay Gap by:", 
                                            options=[col for col in ['Gender', 'Ethnicity', 'AgeGroup', 'Department', 'Role'] if col in filtered_df.columns],
                                            key='pay_demographic')
        
        if pay_demographic_col and 'Salary' in filtered_df.columns:
            pay_gap_df, msg = calculate_pay_gap(filtered_df, demographic_col=pay_demographic_col, salary_col='Salary')
            if pay_gap_df is not None:
                st.markdown(f"**Insight:** {msg}")
                st.dataframe(pay_gap_df)
                
                fig_pay_gap = px.bar(
                    pay_gap_df,
                    x='Demographic_Group',
                    y='Pay_Gap_Pct_vs_Reference',
                    color='Demographic_Group',
                    title=f'Pay Gap by {pay_demographic_col} (vs. Highest Earning Group)',
                    labels={'Pay_Gap_Pct_vs_Reference': 'Pay Gap (%)'},
                    height=500
                )
                st.plotly_chart(fig_pay_gap, use_container_width=True)

                avg_salary_df = filtered_df.groupby(pay_demographic_col)['Salary'].mean().reset_index()
                fig_avg_salary = px.bar(
                    avg_salary_df,
                    x=pay_demographic_col,
                    y='Salary',
                    color=pay_demographic_col,
                    title=f'Average Salary by {pay_demographic_col}',
                    labels={'Salary': 'Average Salary'},
                    height=500
                )
                st.plotly_chart(fig_avg_salary, use_container_width=True)

            else:
                st.warning(msg)
        else:
            st.info("Salary column or selected demographic not found for pay equity analysis.")


    with tab3:
        st.subheader("Promotion & Growth Opportunities")
        promotion_demographic_col = st.selectbox("Analyze Promotion Rate by:", 
                                                options=[col for col in ['Gender', 'Ethnicity', 'AgeGroup', 'Department', 'Role'] if col in filtered_df.columns],
                                                key='promo_demographic')
        
        if promotion_demographic_col:
            promotion_summary_df, msg = calculate_promotion_rate(filtered_df, demographic_col=promotion_demographic_col)
            if promotion_summary_df is not None:
                st.dataframe(promotion_summary_df)

                fig_promo_rate = px.bar(
                    promotion_summary_df,
                    x=promotion_demographic_col,
                    y='Promotion_Rate_Pct',
                    color=promotion_demographic_col,
                    title=f'Promotion Rate by {promotion_demographic_col}',
                    labels={'Promotion_Rate_Pct': 'Promotion Rate (%)'},
                    height=500
                )
                st.plotly_chart(fig_promo_rate, use_container_width=True)
            else:
                st.warning(msg)
        else:
            st.info("Selected demographic for promotion rate analysis not found or insufficient data.")

    with tab4:
        st.subheader("Employee Retention Insights")
        retention_demographic_col = st.selectbox("Analyze Retention Rate by:", 
                                                options=[col for col in ['Gender', 'Ethnicity', 'AgeGroup', 'Department', 'Role'] if col in filtered_df.columns],
                                                key='retention_demographic')

        if retention_demographic_col:
            retention_summary_df, msg = calculate_retention_rate(filtered_df, demographic_col=retention_demographic_col)
            if retention_summary_df is not None:
                st.dataframe(retention_summary_df)

                fig_retention_rate = px.bar(
                    retention_summary_df,
                    x=retention_demographic_col,
                    y='Retention_Rate_Pct',
                    color=retention_demographic_col,
                    title=f'Retention Rate by {retention_demographic_col}',
                    labels={'Retention_Rate_Pct': 'Retention Rate (%)'},
                    height=500
                )
                st.plotly_chart(fig_retention_rate, use_container_width=True)
            else:
                st.warning(msg)
        else:
            st.info("Selected demographic for retention rate analysis not found or insufficient data.")

    with tab5:
        st.subheader("Leadership Representation")
        if 'LeadershipRole' in filtered_df.columns:
            st.markdown("Assuming 'LeadershipRole' column is a boolean (True/False or 1/0) indicating leadership positions.")

            leadership_data = filtered_df[filtered_df['LeadershipRole'] == True]

            if not leadership_data.empty:
                st.markdown("### Overall Leadership Demographics")
                col_lead1, col_lead2 = st.columns(2)

                if 'Gender' in leadership_data.columns:
                    gender_lead_counts = leadership_data['Gender'].value_counts().reset_index()
                    gender_lead_counts.columns = ['Gender', 'Count']
                    fig_gender_lead = px.pie(gender_lead_counts, values='Count', names='Gender', title='Gender in Leadership')
                    col_lead1.plotly_chart(fig_gender_lead, use_container_width=True)
                else:
                    col_lead1.info("Gender column not found for leadership analysis.")

                if 'Ethnicity' in leadership_data.columns:
                    ethnicity_lead_counts = leadership_data['Ethnicity'].value_counts().reset_index()
                    ethnicity_lead_counts.columns = ['Ethnicity', 'Count']
                    fig_ethnicity_lead = px.pie(ethnicity_lead_counts, values='Count', names='Ethnicity', title='Ethnicity in Leadership')
                    col_lead2.plotly_chart(fig_ethnicity_lead, use_container_width=True)
                else:
                    col_lead2.info("Ethnicity column not found for leadership analysis.")
                
                st.markdown("### Leadership Representation vs. Overall Workforce")
                demographic_lead_comp_options = [col for col in ['Gender', 'Ethnicity', 'AgeGroup'] if col in filtered_df.columns]
                if 'Age' in filtered_df.columns and 'AgeGroup' not in filtered_df.columns: # Add derived AgeGroup if only Age is present
                    temp_df_for_lead_select = filtered_df.copy()
                    bins = [0, 25, 35, 45, 55, 65, 100]
                    labels = ['<25', '25-34', '35-44', '45-54', '55-64', '65+']
                    temp_df_for_lead_select['AgeGroup_Derived'] = pd.cut(temp_df_for_lead_select['Age'], bins=bins, labels=labels, right=False, ordered=True)
                    demographic_lead_comp_options.append('AgeGroup_Derived')
                    df_to_use_for_lead_breakdown = temp_df_for_lead_select
                else:
                    df_to_use_for_lead_breakdown = filtered_df

                demographic_lead_comp = st.selectbox("Compare Leadership Representation by:", 
                                                    options=demographic_lead_comp_options,
                                                    key='lead_comp_demographic')
                
                if demographic_lead_comp:
                    overall_distribution = df_to_use_for_lead_breakdown[demographic_lead_comp].value_counts(normalize=True).reset_index()
                    overall_distribution.columns = [demographic_lead_comp, 'Overall_Workforce_Pct']
                    overall_distribution['Overall_Workforce_Pct'] *= 100

                    leadership_distribution = leadership_data[demographic_lead_comp].value_counts(normalize=True).reset_index()
                    leadership_distribution.columns = [demographic_lead_comp, 'Leadership_Pct']
                    leadership_distribution['Leadership_Pct'] *= 100

                    comparison_df = pd.merge(overall_distribution, leadership_distribution, on=demographic_lead_comp, how='outer').fillna(0)
                    
                    fig_lead_comp = px.bar(
                        comparison_df.melt(id_vars=[demographic_lead_comp], var_name='Category', value_name='Percentage'),
                        x=demographic_lead_comp,
                        y='Percentage',
                        color='Category',
                        barmode='group',
                        title=f'{demographic_lead_comp} Representation: Overall Workforce vs. Leadership'
                    )
                    st.plotly_chart(fig_lead_comp, use_container_width=True)
                    st.dataframe(comparison_df)
                else:
                    st.info("Please select a demographic for comparison.")
            else:
                st.info("No employees identified in leadership roles based on the 'LeadershipRole' column.")
        else:
            st.info("The 'LeadershipRole' column (boolean) is required for Leadership Representation analysis.")

else:
    st.info("Please upload a CSV file to begin your Diversity & Inclusion analysis.")
    st.markdown("---")
    st.markdown("### Sample CSV Data Structure")
    st.code("""
EmployeeID,Gender,Ethnicity,Age,Department,Role,Salary,HireDate,PromotionDate,ExitDate,LeadershipRole
1,Female,White,30,Sales,Sales_Representative,60000,2020-01-15,,FALSE
2,Male,Asian,45,Marketing,Marketing_Manager,90000,2018-03-01,,TRUE
3,Non-binary,Black,28,Engineering,Software_Engineer,85000,2021-06-20,,FALSE
4,Female,Hispanic,35,HR,HR_Business_Partner,70000,2019-11-10,,FALSE
5,Male,White,50,Sales,Sales_Director,120000,2015-07-01,,TRUE
6,Female,Asian,25,Engineering,Junior_Developer,75000,2022-02-01,2023-01-01,FALSE
7,Male,Black,40,Marketing,Marketing_Specialist,70000,2020-04-01,,FALSE
8,Female,White,33,HR,HR_Coordinator,55000,2021-09-01,2022-10-01,FALSE
9,Male,Hispanic,38,Engineering,Senior_Software_Engineer,100000,2017-08-10,,FALSE
10,Non-binary,Other,29,Sales,Account_Executive,65000,2022-03-15,,FALSE
""")
