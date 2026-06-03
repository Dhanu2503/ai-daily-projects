import pandas as pd
import numpy as np
import re
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer # Kept for potential future use or more advanced keyword extraction
import textstat

# --- NLTK Data Download --- (Ensures necessary NLTK data is available)
def download_nltk_data():
    print("Checking NLTK data... ")
    required_nltk_data = ['punkt', 'stopwords', 'wordnet', 'omw-1.4']
    for data_item in required_nltk_data:
        try:
            nltk.data.find(f'corpora/{data_item}') if data_item not in ['punkt'] else nltk.data.find(f'tokenizers/{data_item}')
        except nltk.downloader.DownloadError:
            print(f"Downloading NLTK {data_item}...")
            nltk.download(data_item)
    print("NLTK data check complete.")

# --- Helper Functions ---

def clean_text(text):
    """Cleans text by converting to lowercase, removing HTML tags, special characters, and extra spaces."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'<.*?>', '', text)  # Remove HTML tags
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text

def get_readability_score(text):
    """Calculates Flesch-Kincaid Grade Level for a given text."""
    if not text or len(text.split()) < 5: # textstat requires a minimum word count
        return np.nan
    try:
        return textstat.flesch_kincaid_grade(text)
    except Exception:
        return np.nan

def extract_keywords_from_description(description, top_n=5):
    """Extracts the most frequent non-stopwords as keywords from a description."""
    if not description:
        return []
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    tokens = word_tokenize(description)
    keywords = [lemmatizer.lemmatize(word) for word in tokens if word.isalpha() and word not in stop_words]
    
    # Simple frequency-based keyword extraction
    freq_dist = nltk.FreqDist(keywords)
    return [word for word, freq in freq_dist.most_common(top_n)]

def suggest_categories(description, existing_categories, min_match_len=2):
    """Suggests categories based on keywords in the description matching existing categories."""
    if not description:
        return []
    
    suggested = []
    description_words = set(word_tokenize(description.lower()))
    
    # Try to match with existing categories directly
    for category in existing_categories:
        category_words = set(word_tokenize(category.lower()))
        if len(description_words.intersection(category_words)) >= min_match_len:
            if category not in suggested:
                suggested.append(category)
    
    # Add general suggestions if no specific match or to enrich existing ones
    if 'electronic' in description or 'laptop' in description or 'mouse' in description or 'keyboard' in description or 'smart' in description or 'audio' in description or 'tech' in description:
        if 'Electronics' not in suggested: suggested.append('Electronics')
    if 'chair' in description or 'sofa' in description or 'desk' in description or 'furniture' in description or 'home' in description:
        if 'Furniture' not in suggested: suggested.append('Furniture')
    if 'kitchen' in description or 'coffee' in description or 'kettle' in description or 'bottle' in description or 'cook' in description:
        if 'Home & Kitchen' not in suggested: suggested.append('Home & Kitchen')
    if 'sport' in description or 'yoga' in description or 'outdoor' in description or 'hiking' in description or 'fitness' in description:
        if 'Sports & Outdoors' not in suggested: suggested.append('Sports & Outdoors')
    if 'apparel' in description or 't-shirt' in description or 'clothing' in description or 'wear' in description:
        if 'Apparel' not in suggested: suggested.append('Apparel')
    if 'toy' in description or 'game' in description or 'children' in description:
        if 'Toys & Games' not in suggested: suggested.append('Toys & Games')
    if 'food' in description or 'beverage' in description or 'coffee' in description or 'drink' in description:
        if 'Food & Beverage' not in suggested: suggested.append('Food & Beverage')
            
    return suggested if suggested else ['General'] # Return General if no specific match

def detect_price_outliers(series):
    """Detects price outliers using the Interquartile Range (IQR) method."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return (series < lower_bound) | (series > upper_bound)

# --- Main Optimization Logic ---

def optimize_product_catalog(df):
    """Applies various optimization techniques to the product catalog dataframe."""
    print("Starting product catalog optimization...")
    
    # Initialize a column for optimization suggestions as a list for each product
    df['Optimization_Suggestions'] = [[] for _ in range(len(df))]

    # 1. Data Cleaning and Standardization
    print("Step 1/7: Cleaning and standardizing text data...")
    df['Cleaned_Name'] = df['Name'].apply(clean_text)
    df['Cleaned_Description'] = df['Description'].apply(clean_text)
    
    # 2. Description Optimization
    print("Step 2/7: Optimizing product descriptions...")
    df['Description_Readability_Grade'] = df['Description'].apply(get_readability_score)
    
    # Identify descriptions with low readability (e.g., above 12th grade level, indicating complexity)
    # Or extremely low (e.g., below 5th grade level for products, indicating oversimplification)
    for index, row in df.iterrows():
        suggestions = row['Optimization_Suggestions']
        if pd.notna(row['Description_Readability_Grade']):
            if row['Description_Readability_Grade'] > 12:
                suggestions.append('Description may be too complex (high readability score). Consider simplifying.')
            elif row['Description_Readability_Grade'] < 5:
                suggestions.append('Description may be too simplistic (low readability score). Consider adding more detail.')
        
        # Identify short descriptions
        if len(str(row['Description']).split()) < 30:
            suggestions.append('Description is too short. Add more details for SEO and customer information.')
        
        # Extract keywords from descriptions
        row['Suggested_Keywords'] = extract_keywords_from_description(row['Cleaned_Description'])

    # 3. Title Optimization
    print("Step 3/7: Optimizing product titles...")
    df['Title_Length'] = df['Name'].apply(lambda x: len(str(x)))
    
    for index, row in df.iterrows():
        suggestions = row['Optimization_Suggestions']
        if row['Title_Length'] < 20:
            suggestions.append('Title is too short. Consider adding more descriptive keywords.')
        elif row['Title_Length'] > 70:
            suggestions.append('Title is too long. Consider shortening for better display and SEO.')
            
        # Suggest adding keywords from description to title
        title_lower = str(row['Name']).lower()
        missing_keywords = [kw for kw in row['Suggested_Keywords'] if kw not in title_lower and len(kw) > 2]
        if missing_keywords:
            suggestions.append(f"Consider adding relevant keywords to title: {', '.join(missing_keywords[:3])}")

    # 4. Categorization and Tagging
    print("Step 4/7: Suggesting categories and tags...")
    all_categories = df['Category'].dropna().unique().tolist()
    df['Suggested_Categories'] = df['Cleaned_Description'].apply(lambda x: suggest_categories(x, all_categories))
    
    for index, row in df.iterrows():
        suggestions = row['Optimization_Suggestions']
        if pd.isna(row['Category']) or (row['Category'] not in row['Suggested_Categories'] and len(row['Suggested_Categories']) > 0):
            if row['Suggested_Categories'] and row['Suggested_Categories'] != ['General']:
                suggestions.append(f"Review/update category. Suggested based on description: {', '.join(row['Suggested_Categories'])}")
            else:
                suggestions.append("No specific category detected from description. Review category manually.")

    # 5. Pricing Analysis
    print("Step 5/7: Analyzing product pricing...")
    # Convert Price to numeric, coercing errors to NaN
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    
    # Detect price outliers globally (simplified)
    if not df['Price'].dropna().empty:
        price_outliers_idx = df.index[detect_price_outliers(df['Price'].dropna())].tolist()
        for idx in price_outliers_idx:
            df.loc[idx, 'Optimization_Suggestions'].append('Price seems to be an outlier. Review pricing strategy.')

    # 6. Image Optimization Insights
    print("Step 6/7: Checking for image optimization opportunities...")
    for index, row in df.iterrows():
        suggestions = row['Optimization_Suggestions']
        if pd.isna(row['Image_URLs']) or str(row['Image_URLs']).strip() == '':
            suggestions.append('Missing product image. Add high-quality images for better engagement.')

    # 7. Stock Management Insights
    print("Step 7/7: Providing stock management insights...")
    df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce')
    df['Sales_History'] = pd.to_numeric(df['Sales_History'], errors='coerce')

    for index, row in df.iterrows():
        suggestions = row['Optimization_Suggestions']
        if pd.notna(row['Stock']) and row['Stock'] < 10:
            suggestions.append('Low stock alert (<10 units). Consider reordering or promoting alternatives.')
        
        # Identify potential slow-moving items (simplified heuristic)
        # Requires non-null Stock and Sales_History for meaningful calculation
        if pd.notna(row['Stock']) and pd.notna(row['Sales_History']) and row['Stock'] > 0:
            # Define thresholds relative to overall data or static values
            median_sales = df['Sales_History'].median() if not df['Sales_History'].isnull().all() else 0
            median_stock = df['Stock'].median() if not df['Stock'].isnull().all() else 0
            
            if row['Sales_History'] < median_sales * 0.5 and row['Stock'] > median_stock * 1.5:
                suggestions.append('Potentially slow-moving item (high stock, low sales). Consider promotions or review pricing.')

    # Convert lists of suggestions to a comma-separated string for readability in CSV
    df['Optimization_Suggestions'] = df['Optimization_Suggestions'].apply(lambda x: '; '.join(x) if x else 'No specific suggestions')
    
    print("Optimization complete!")
    return df

# --- Main Execution Block ---
if __name__ == "__main__":
    download_nltk_data()

    DATA_DIR = 'data'
    REPORTS_DIR = 'reports'
    INPUT_FILE = os.path.join(DATA_DIR, 'products.csv')
    OUTPUT_FILE = os.path.join(REPORTS_DIR, 'optimized_products_report.csv')

    # Create directories if they don't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # --- Create Dummy Data if not exists ---
    if not os.path.exists(INPUT_FILE):
        print(f"Creating dummy data at {INPUT_FILE}...")
        dummy_data = {
            'SKU': [f'PROD{i:03d}' for i in range(1, 21)],
            'Name': [
                "Laptop Pro X", "Ergonomic Office Chair", "Wireless Mouse Elite", "Gaming Keyboard RGB",
                "Smart Watch Pro", "Portable Bluetooth Speaker", "Eco-Friendly Water Bottle",
                "Premium Coffee Maker", "Yoga Mat Deluxe", "Designer Desk Lamp",
                "Electric Kettle Rapid Boil", "Smart Home Hub", "Luxury Sofa Set",
                "Hiking Backpack Pro", "Wireless Earbuds ANC", "Basic T-shirt",
                "Premium T-shirt", "Vintage Record Player", "Children's Toy Car", "Gourmet Coffee Beans"
            ],
            'Description': [
                "A powerful laptop for professionals. Featuring a fast processor, ample RAM, and a stunning display. Ideal for productivity and creative tasks.",
                "Comfortable office chair with adjustable lumbar support. Perfect for long working hours. Available in black and grey.",
                "High-precision wireless mouse with customisable buttons. Long battery life and ergonomic design. Connects via Bluetooth.",
                "Mechanical gaming keyboard with vibrant RGB backlighting. Tactile keys for responsive gaming. Durable construction.",
                "Track your fitness, receive notifications, and monitor your health with this advanced smartwatch. Waterproof design.",
                "Compact and powerful Bluetooth speaker with rich bass. Ideal for outdoor use and parties. 10-hour battery life.",
                "Durable stainless steel water bottle. Keeps drinks cold for 24 hours and hot for 12 hours. BPA-free.",
                "Brew delicious coffee with this programmable coffee maker. Features a built-in grinder and thermal carafe.",
                "High-density yoga mat for optimal comfort and support during your practice. Non-slip surface.",
                "Modern LED desk lamp with touch controls and adjustable brightness. Energy-efficient.",
                "Boil water quickly and safely with this electric kettle. Stainless steel interior. Auto shut-off.",
                "Centralize your smart devices with this hub. Compatible with various protocols. Easy setup.",
                "A truly luxurious and comfortable sofa set for your living room. Made with premium fabric and sturdy construction. Very elegant and stylish.",
                "Lightweight and durable hiking backpack with multiple compartments. Hydration bladder compatible. For long treks.",
                "Enjoy crystal-clear audio with these wireless earbuds featuring active noise cancellation. Long battery life.",
                "A plain and simple t-shirt for everyday wear. Made from 100% cotton.",
                "A high quality t-shirt made from organic cotton. Soft and breathable. Available in various colors.",
                "Relive the classic sound with this vintage-style record player. Built-in speakers and Bluetooth connectivity.",
                "A fun and durable toy car for children aged 3+. Bright colors and safe materials.",
                "Premium Arabica coffee beans, medium roast. Rich flavor and aroma."
            ],
            'Category': [
                "Electronics", "Furniture", "Electronics", "Electronics",
                "Electronics", "Electronics", "Home & Kitchen",
                "Home & Kitchen", "Sports & Outdoors", "Furniture",
                "Home & Kitchen", "Electronics", "Furniture",
                "Sports & Outdoors", "Electronics", "Apparel",
                "Apparel", "Electronics", "Toys & Games", "Food & Beverage"
            ],
            'Price': [
                1200.00, 250.00, 50.00, 100.00,
                180.00, 75.00, 20.00,
                150.00, 35.00, 80.00,
                45.00, 200.00, 2500.00, # High price outlier
                90.00, 120.00, 15.00,
                30.00, 180.00, 25.00, 18.00
            ],
            'Stock': [
                50, 100, 200, 75,
                120, 15, # Low stock
                300, 40, 80, 60,
                110, 25, 5, # Low stock
                30, 90, 500,
                250, 10, # Low stock
                150, 70
            ],
            'Sales_History': [ # Mock sales history
                150, 300, 500, 200,
                400, 100, 600,
                120, 250, 180,
                350, 80, 20, # Low sales for 'Luxury Sofa Set' with 5 stock suggests it could be slow-moving
                90, 300, 1000,
                500, 30,
                400, 200
            ],
            'Image_URLs': [
                "http://example.com/img/laptop_pro_x.jpg", "http://example.com/img/chair.jpg",
                "http://example.com/img/mouse.jpg", "http://example.com/img/keyboard.jpg",
                np.nan, # Missing image
                "http://example.com/img/speaker.jpg", "http://example.com/img/bottle.jpg",
                "http://example.com/img/coffee_maker.jpg", "http://example.com/img/yoga_mat.jpg",
                "http://example.com/img/desk_lamp.jpg", "http://example.com/img/kettle.jpg",
                "http://example.com/img/smart_hub.jpg", "http://example.com/img/sofa.jpg",
                "http://example.com/img/backpack.jpg", "http://example.com/img/earbuds.jpg",
                "", # Missing image
                "http://example.com/img/premium_tshirt.jpg", "http://example.com/img/record_player.jpg",
                "http://example.com/img/toy_car.jpg", "http://example.com/img/coffee_beans.jpg"
            ]
        }
        pd.DataFrame(dummy_data).to_csv(INPUT_FILE, index=False)
        print("Dummy data created successfully.")

    try:
        df_products = pd.read_csv(INPUT_FILE)
        print(f"Loaded {len(df_products)} products from {INPUT_FILE}")

        # Run the optimization
        optimized_df = optimize_product_catalog(df_products.copy()) # Operate on a copy to preserve original df

        # Select relevant columns for the report and save
        report_columns = [
            'SKU', 'Name', 'Category', 'Price', 'Stock', 'Sales_History', 'Image_URLs',
            'Description', 'Description_Readability_Grade', 'Suggested_Keywords',
            'Title_Length', 'Suggested_Categories', 'Optimization_Suggestions'
        ]
        
        # Ensure all report columns exist in the output dataframe
        for col in report_columns:
            if col not in optimized_df.columns:
                optimized_df[col] = np.nan # Default for missing columns

        # Save the report
        optimized_df[report_columns].to_csv(OUTPUT_FILE, index=False)
        print(f"Optimization report saved to {OUTPUT_FILE}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_FILE}. Please ensure it exists or is generated.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
