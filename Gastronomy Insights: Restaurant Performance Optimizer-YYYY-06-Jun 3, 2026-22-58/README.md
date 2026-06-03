import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import numpy as np
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import io # For handling uploaded files

# --- NLTK Data Download (only runs once) ---
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except nltk.downloader.DownloadError:
    nltk.download('vader_lexicon')
# Initialize Sentiment Analyzer
analyzer = SentimentIntensityAnalyzer()

# --- Helper Functions ---

# Function to generate dummy data for demonstration
def generate_dummy_data():
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # Transactions data
    items = ['Burger', 'Pizza', 'Salad', 'Coffee', 'Dessert', 'Soda']
    categories = ['Main', 'Main', 'Appetizer', 'Beverage', 'Dessert', 'Beverage']
    
    transactions_data = []
    for date in dates:
        for _ in range(np.random.randint(5, 20)): # 5 to 20 transactions per day
            item = np.random.choice(items)
            category = categories[items.index(item)]
            quantity = np.random.randint(1, 5)
            unit_price = np.random.uniform(5, 25)
            unit_cost = np.random.uniform(unit_price * 0.2, unit_price * 0.5) # Cost is 20-50% of price
            
            transactions_data.append({
                'date': date,
                'item': item,
                'category': category,
                'quantity': quantity,
                'unit_price': unit_price,
                'unit_cost': unit_cost,
                'revenue': quantity * unit_price,
                'cogs': quantity * unit_cost,
                'gross_profit': quantity * (unit_price - unit_cost)
            })
    transactions_df = pd.DataFrame(transactions_data)
    transactions_df['date'] = pd.to_datetime(transactions_df['date'])
    
    # Expenses data
    expense_types = ['Rent', 'Labor', 'Utilities', 'Marketing', 'Ingredients Purchase', 'Maintenance']
    expenses_data = []
    for date in dates:
        if date.day == 1: # Monthly rent
            expenses_data.append({'date': date, 'expense_type': 'Rent', 'amount': 5000})
        for _ in range(np.random.randint(1, 3)): # 1 to 3 daily expenses
            exp_type = np.random.choice(expense_types, p=[0.05, 0.3, 0.1, 0.1, 0.4, 0.05])
            amount = np.random.uniform(50, 1000) if exp_type != 'Rent' else 0
            if exp_type == 'Labor':
                amount = np.random.uniform(800, 2000)
            elif exp_type == 'Ingredients Purchase':
                amount = np.random.uniform(300, 1500)
            
            if amount > 0:
                expenses_data.append({'date': date, 'expense_type': exp_type, 'amount': amount})
    expenses_df = pd.DataFrame(expenses_data)
    expenses_df['date'] = pd.to_datetime(expenses_df['date'])

    # Reviews data
    review_texts = [
        "Amazing food and great service!", "The burger was delicious, highly recommend.",
        "Good experience overall, but the wait time was a bit long.",
        "Average food, nothing special.", "Terrible service, food was cold.",
        "Best pizza I've had in ages!", "Coffee was excellent, cozy atmosphere.",
        "Overpriced for what you get.", "Staff was rude.", "Dessert was divine."
    ]
    ratings = [5, 4, 3, 2, 1]
    
    reviews_data = []
    for date in dates:
        if np.random.rand() < 0.3: # ~30% chance of a review on any given day
            review = np.random.choice(review_texts, p=[0.2, 0.2, 0.15, 0.15, 0.1, 0.05, 0.05, 0.05, 0.025, 0.025])
            rating_map = {
                "Amazing food and great service!": 5, "The burger was delicious, highly recommend.": 5,
                "Good experience overall, but the wait time was a bit long.": 3,
                "Average food, nothing special.": 3, "Terrible service, food was cold.": 1,
                "Best pizza I've had in ages!": 5, "Coffee was excellent, cozy atmosphere.": 4,
                "Overpriced for what you get.": 2, "Staff was rude.": 1, "Dessert was divine.": 5
            }
            rating = rating_map.get(review, np.random.choice(ratings, p=[0.3, 0.3, 0.2, 0.1, 0.1])) # Fallback
            reviews_data.append({'date': date, 'rating': rating, 'review_text': review})
    reviews_df = pd.DataFrame(reviews_data)
    reviews_df['date'] = pd.to_datetime(reviews_df['date'])

    return transactions_df, expenses_df, reviews_df

@st.cache_data
def load_data(uploaded_file, data_type):
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            if data_type == 'transactions':
                df['date'] = pd.to_datetime(df['date'])
                # Ensure necessary columns are present or calculate them
                if 'revenue' not in df.columns and 'quantity' in df.columns and 'unit_price' in df.columns:
                    df['revenue'] = df['quantity'] * df['unit_price']
                if 'cogs' not in df.columns and 'quantity' in df.columns and 'unit_cost' in df.columns:
                    df['cogs'] = df['quantity'] * df['unit_cost']
                if 'gross_profit' not in df.columns and 'revenue' in df.columns and 'cogs' in df.columns:
                    df['gross_profit'] = df['revenue'] - df['cogs']
                required_cols = ['date', 'item', 'category', 'quantity', 'unit_price', 'unit_cost', 'revenue', 'cogs', 'gross_profit']
                for col in required_cols:
                    if col not in df.columns:
                        st.warning(f"Transactions data is missing '{col}' column. Please ensure your CSV has all required columns or can derive them.")
                        return pd.DataFrame(columns=required_cols) # Return empty if critical col missing
                
            elif data_type == 'expenses':
                df['date'] = pd.to_datetime(df['date'])
                required_cols = ['date', 'expense_type', 'amount']
                for col in required_cols:
                    if col not in df.columns:
                        st.warning(f"Expenses data is missing '{col}' column. Please ensure your CSV has all required columns.")
                        return pd.DataFrame(columns=required_cols)
            elif data_type == 'reviews':
                df['date'] = pd.to_datetime(df['date'])
                required_cols = ['date', 'rating', 'review_text']
                for col in required_cols:
                    if col not in df.columns:
                        st.warning(f"Reviews data is missing '{col}' column. Please ensure your CSV has all required columns.")
                        return pd.DataFrame(columns=required_cols)
            return df
        except Exception as e:
            st.error(f"Error loading {data_type} data: {e}. Please check your CSV format.")
            return None
    return None

@st.cache_data
def calculate_kpis(transactions_df, expenses_df):
    total_revenue = transactions_df['revenue'].sum() if not transactions_df.empty else 0
    total_cogs = transactions_df['cogs'].sum() if not transactions_df.empty else 0
    gross_profit = transactions_df['gross_profit'].sum() if not transactions_df.empty else 0
    
    total_operating_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0
    
    net_profit = gross_profit - total_operating_expenses
    
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    cogs_percentage = (total_cogs / total_revenue * 100) if total_revenue > 0 else 0
    
    avg_check_size = (transactions_df['revenue'].sum() / transactions_df['quantity'].count()) if transactions_df['quantity'].count() > 0 else 0
    
    # Labor cost specific
    labor_cost = expenses_df[expenses_df['expense_type'] == 'Labor']['amount'].sum() if not expenses_df.empty else 0
    labor_cost_percentage = (labor_cost / total_revenue * 100) if total_revenue > 0 else 0

    return {
        "Total Revenue": total_revenue,
        "Total COGS": total_cogs,
        "Gross Profit": gross_profit,
        "Total Operating Expenses": total_operating_expenses,
        "Net Profit": net_profit,
        "Profit Margin (%)": profit_margin,
        "COGS Percentage (%)": cogs_percentage,
        "Average Check Size": avg_check_size,
        "Labor Cost": labor_cost,
        "Labor Cost (%)": labor_cost_percentage
    }

@st.cache_data
def analyze_sentiment(reviews_df):
    if reviews_df.empty:
        return pd.DataFrame()
    
    # Filter out empty review texts
    reviews_df_clean = reviews_df.dropna(subset=['review_text']).copy()
    
    # Apply sentiment analysis
    reviews_df_clean['sentiment_score'] = reviews_df_clean['review_text'].apply(lambda text: analyzer.polarity_scores(text)['compound'])
    
    # Categorize sentiment
    def get_sentiment_label(score):
        if score >= 0.05:
            return 'Positive'
        elif score <= -0.05:
            return 'Negative'
        else:
            return 'Neutral'
            
    reviews_df_clean['sentiment_label'] = reviews_df_clean['sentiment_score'].apply(get_sentiment_label)
    return reviews_df_clean


def generate_recommendations(kpis, processed_reviews_df, transactions_df, target_profit_margin):
    recs = []
    
    # Financial Recommendations
    if kpis["Profit Margin (%)"] < target_profit_margin:
        recs.append(f"**Improve Profit Margin**: Current profit margin is {kpis['Profit Margin (%)']:.2f}% which is below your target of {target_profit_margin}%.\n")
        if kpis["COGS Percentage (%)"] > 30: # General industry benchmark for food cost
            recs.append(f"  - **Reduce COGS**: COGS is {kpis['COGS Percentage (%)']:.2f}% of revenue. Review ingredient sourcing, portion sizes, and waste management.\n")
        if kpis["Labor Cost (%)"] > 25: # General industry benchmark for labor cost
            recs.append(f"  - **Optimize Labor Costs**: Labor costs are {kpis['Labor Cost (%)']:.2f}% of revenue. Consider optimizing staff scheduling, cross-training, or productivity improvements.\n")
        recs.append(f"  - **Increase Revenue**: Explore marketing campaigns, menu engineering, or special promotions.\n")
    else:
        recs.append(f"**Maintain Strong Profitability**: Your profit margin of {kpis['Profit Margin (%)']:.2f}% is healthy and above your target of {target_profit_margin}%.\n")

    # Sales & Menu Recommendations
    if not transactions_df.empty:
        daily_avg_revenue = transactions_df.groupby(transactions_df['date'].dt.date)['revenue'].sum().mean()
        if daily_avg_revenue < 1000: # Arbitrary threshold for low daily sales
            recs.append(f"**Boost Sales Volume**: Average daily revenue is ${daily_avg_revenue:.2f}. Consider promotions or expanding operating hours.\n")

        top_items = transactions_df.groupby('item')['revenue'].sum().nlargest(3)
        bottom_items = transactions_df.groupby('item')['revenue'].sum().nsmallest(3)
        recs.append(f"**Menu Optimization**:\n")
        recs.append(f"  - **Top Performing Items**: {', '.join(top_items.index)} are your best sellers. Consider promoting them more or creating variations.\n")
        recs.append(f"  - **Underperforming Items**: {', '.join(bottom_items.index)} have low sales. Evaluate if these items should be removed, re-priced, or improved.\n")
    
    # Customer Feedback Recommendations
    if not processed_reviews_df.empty: # Check if processed reviews df is empty
        avg_rating = processed_reviews_df['rating'].mean()
        negative_reviews_count = processed_reviews_df[processed_reviews_df['sentiment_label'] == 'Negative'].shape[0]
        total_reviews = processed_reviews_df.shape[0]

        if avg_rating < 3.5:
            recs.append(f"**Improve Customer Satisfaction**: Average rating is {avg_rating:.1f}. Focus on service quality and food consistency.\n")
        if total_reviews > 0 and negative_reviews_count / total_reviews > 0.15: # More than 15% negative reviews
            recs.append(f"  - **Address Negative Feedback**: {negative_reviews_count} out of {total_reviews} reviews are negative. Analyze common themes in negative reviews to pinpoint issues (e.g., 'cold food', 'slow service').\n")
            # Example: finding common words in negative reviews (simple approach)
            negative_texts = " ".join(processed_reviews_df[processed_reviews_df['sentiment_label'] == 'Negative']['review_text'].dropna().tolist())
            if "service" in negative_texts.lower() or "staff" in negative_texts.lower():
                recs.append("  - **Service Improvement**: Many negative reviews mention 'service' or 'staff'. Implement staff training or improve management oversight.\n")
            if "food" in negative_texts.lower() or "cold" in negative_texts.lower() or "taste" in negative_texts.lower():
                recs.append("  - **Food Quality Control**: Many negative reviews mention 'food' quality (e.g., cold, taste). Review kitchen processes and ingredient quality.\n")
    else:
        recs.append("**Customer Feedback**: No review data available. Consider implementing a feedback system to gauge customer satisfaction.\n")
        
    if not recs:
        recs.append("All key metrics appear healthy based on available data. Continue monitoring performance closely!\n")
            
    return recs

# --- Streamlit App ---
def main():
    st.set_page_config(layout="wide", page_title="Gastronomy Insights: Restaurant Performance Optimizer")

    st.title("🍽️ Gastronomy Insights: Restaurant Performance Optimizer")
    st.markdown("Optimize your restaurant's performance by analyzing sales, expenses, and customer feedback.")

    # --- Sidebar for Data Upload and Settings ---
    st.sidebar.header("📂 Data Upload")
    st.sidebar.markdown("Upload your restaurant's operational data.")

    uploaded_transactions_file = st.sidebar.file_uploader("Upload Transactions CSV", type=["csv"], key="transactions")
    uploaded_expenses_file = st.sidebar.file_uploader("Upload Expenses CSV", type=["csv"], key="expenses")
    uploaded_reviews_file = st.sidebar.file_uploader("Upload Customer Reviews CSV", type=["csv"], key="reviews")

    st.sidebar.markdown("--- ")
    st.sidebar.header("⚙️ Settings")
    target_profit_margin = st.sidebar.slider("Target Net Profit Margin (%)", min_value=0.0, max_value=50.0, value=15.0, step=0.5)
    st.sidebar.markdown("--- ")
    st.sidebar.info("Using dummy data if no files are uploaded. See dummy data structure [here](https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/sample_data.csv) (placeholder link).") # Placeholder link

    # Load data
    transactions_df = load_data(uploaded_transactions_file, 'transactions')
    expenses_df = load_data(uploaded_expenses_file, 'expenses')
    reviews_df = load_data(uploaded_reviews_file, 'reviews')

    # Use dummy data if no files are uploaded and enable regeneration if some are missing
    if transactions_df is None or transactions_df.empty:
        st.info("No transactions data uploaded. Using dummy data for demonstration.")
        transactions_df_dummy, expenses_df_dummy, reviews_df_dummy = generate_dummy_data()
        transactions_df = transactions_df_dummy
        if expenses_df is None or expenses_df.empty:
            expenses_df = expenses_df_dummy
        if reviews_df is None or reviews_df.empty:
            reviews_df = reviews_df_dummy
    else:
        if expenses_df is None or expenses_df.empty:
            st.info("No expenses data uploaded. Using dummy expense data.")
            _, expenses_df, _ = generate_dummy_data()
        if reviews_df is None or reviews_df.empty:
            st.info("No reviews data uploaded. Using dummy review data.")
            _, _, reviews_df = generate_dummy_data()

    if transactions_df is None or transactions_df.empty:
        st.error("Could not load or generate transactions data. Please upload a valid CSV or ensure dummy data generation works.")
        return # Exit if no data can be loaded/generated

    # Process data
    processed_reviews_df = analyze_sentiment(reviews_df)
    kpis = calculate_kpis(transactions_df, expenses_df)
    
    st.markdown("--- ")

    # --- Main Content Area ---

    # 1. Overview Dashboard
    st.header("📊 Overview Dashboard")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Revenue", f"${kpis['Total Revenue']:.2f}")
    with col2:
        st.metric("Gross Profit", f"${kpis['Gross Profit']:.2f}")
    with col3:
        st.metric("Net Profit", f"${kpis['Net Profit']:.2f}")
    with col4:
        st.metric("Profit Margin", f"{kpis['Profit Margin (%)']:.2f}%")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("COGS %", f"{kpis['COGS Percentage (%)']:.2f}%")
    with col6:
        st.metric("Labor Cost %", f"{kpis['Labor Cost (%)']:.2f}%")
    with col7:
        st.metric("Avg Check Size", f"${kpis['Average Check Size']:.2f}")
    with col8:
        avg_rating = processed_reviews_df['rating'].mean() if not processed_reviews_df.empty else 0
        st.metric("Avg Customer Rating", f"{avg_rating:.1f} / 5")

    st.markdown("--- ")

    # 2. Sales Performance Analysis
    st.header("📈 Sales Performance")
    
    # Resample for daily/weekly/monthly trends
    transactions_daily = transactions_df.set_index('date').resample('D').agg({
        'revenue': 'sum',
        'cogs': 'sum',
        'gross_profit': 'sum'
    }).fillna(0)
    
    # Calculate Net Profit daily
    expenses_daily = expenses_df.set_index('date').resample('D')['amount'].sum().fillna(0)
    combined_daily = transactions_daily.merge(expenses_daily.rename('total_expenses'), left_index=True, right_index=True, how='left').fillna(0)
    combined_daily['net_profit'] = combined_daily['gross_profit'] - combined_daily['total_expenses']

    st.subheader("Revenue and Profit Over Time")
    fig_sales_profit = px.line(combined_daily, x=combined_daily.index, y=['revenue', 'gross_profit', 'net_profit'],
                               title='Daily Revenue, Gross Profit, and Net Profit',
                               labels={'value': 'Amount ($)', 'date': 'Date'})
    st.plotly_chart(fig_sales_profit, use_container_width=True)

    col_sales_1, col_sales_2 = st.columns(2)
    with col_sales_1:
        st.subheader("Sales by Category")
        sales_by_category = transactions_df.groupby('category')['revenue'].sum().sort_values(ascending=False).reset_index()
        fig_cat = px.bar(sales_by_category, x='category', y='revenue', 
                         title='Total Revenue by Menu Category',
                         labels={'revenue': 'Total Revenue ($)', 'category': 'Category'})
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_sales_2:
        st.subheader("Top Selling Items (by Revenue)")
        top_items_revenue = transactions_df.groupby('item')['revenue'].sum().nlargest(10).reset_index()
        fig_items = px.bar(top_items_revenue, x='item', y='revenue', 
                           title='Top 10 Items by Revenue',
                           labels={'revenue': 'Total Revenue ($)', 'item': 'Item'},
                           color='revenue', color_continuous_scale=px.colors.sequential.Viridis)
        st.plotly_chart(fig_items, use_container_width=True)
        
    st.markdown("--- ")

    # 3. Expense Management
    st.header("💰 Expense Management")
    
    st.subheader("Expense Breakdown")
    if not expenses_df.empty:
        expenses_by_type = expenses_df.groupby('expense_type')['amount'].sum().sort_values(ascending=False).reset_index()
        fig_expenses_pie = px.pie(expenses_by_type, values='amount', names='expense_type', 
                                  title='Total Expenses by Type',
                                  hole=0.3)
        st.plotly_chart(fig_expenses_pie, use_container_width=True)
        
        st.subheader("Expenses Over Time")
        expenses_monthly = expenses_df.set_index('date').resample('M')['amount'].sum().reset_index()
        fig_expenses_line = px.line(expenses_monthly, x='date', y='amount', 
                                    title='Monthly Total Expenses',
                                    labels={'amount': 'Total Expenses ($)', 'date': 'Month'})
        st.plotly_chart(fig_expenses_line, use_container_width=True)
    else:
        st.info("No expense data available for analysis.")

    st.markdown("--- ")

    # 4. Customer Feedback Analysis
    st.header("🗣️ Customer Feedback Analysis")
    if not processed_reviews_df.empty:
        col_feedback_1, col_feedback_2 = st.columns(2)
        with col_feedback_1:
            st.subheader("Rating Distribution")
            fig_ratings = px.histogram(processed_reviews_df, x='rating', nbins=5, 
                                       title='Distribution of Customer Ratings',
                                       labels={'rating': 'Rating (1-5)'})
            st.plotly_chart(fig_ratings, use_container_width=True)

        with col_feedback_2:
            st.subheader("Sentiment Distribution")
            sentiment_counts = processed_reviews_df['sentiment_label'].value_counts().reset_index()
            sentiment_counts.columns = ['Sentiment', 'Count']
            fig_sentiment = px.pie(sentiment_counts, values='Count', names='Sentiment', 
                                   title='Overall Sentiment Distribution',
                                   color='Sentiment',
                                   color_discrete_map={'Positive':'green', 'Neutral':'grey', 'Negative':'red'})
            st.plotly_chart(fig_sentiment, use_container_width=True)
            
        st.subheader("Sentiment Over Time")
        reviews_sentiment_daily = processed_reviews_df.set_index('date').resample('D')['sentiment_score'].mean().fillna(0).reset_index()
        fig_sentiment_time = px.line(reviews_sentiment_daily, x='date', y='sentiment_score',
                                    title='Average Daily Sentiment Score',
                                    labels={'sentiment_score': 'Avg Sentiment Score', 'date': 'Date'})
        st.plotly_chart(fig_sentiment_time, use_container_width=True)
        
        st.subheader("Recent Reviews")
        st.dataframe(processed_reviews_df[['date', 'rating', 'review_text', 'sentiment_label']].sort_values('date', ascending=False).head(10))
    else:
        st.info("No customer review data available for analysis. Please upload a reviews CSV.")

    st.markdown("--- ")

    # 5. Actionable Recommendations
    st.header("💡 Actionable Recommendations")
    
    recommendations = generate_recommendations(kpis, processed_reviews_df, transactions_df, target_profit_margin)
    for rec in recommendations:
        st.markdown(f"- {rec}")

    st.markdown("--- ")
    st.markdown("Developed with ❤️ for Restaurant Owners.")

if __name__ == "__main__":
    main()
